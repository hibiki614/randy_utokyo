"""Independent numerical checks; run from any working directory."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from scipy.optimize import linprog
from model import make_pairs,theory_curve,fixed_branch_lp,solve,C
root=Path(__file__).resolve().parent.parent
routes=json.loads((root/'inputs/routes.json').read_text())
ref=pd.read_csv(root/'inputs/reference_theoretical_pair_delays.csv').set_index(['route','speed_kmh','i','j'])
errors=[]
for rt in routes:
 for v in np.arange(20,50.1,2.5):
  for p in make_pairs(rt,v):
   errors.append(abs(p['dmin']-ref.loc[(rt['route'],v,p['i'],p['j']),'delta_ij_s']))
   for c,r in p['arcs']:
    for phi in [c-r,c,c+r]:
     assert abs(float(theory_curve(phi,p['lam'],p['gi'],p['gj']))*C-p['dmin'])<1e-6
assert max(errors)<1e-7
rng=np.random.default_rng(34);flow_errors=[]
for trial in range(12):
 rt=routes[trial%len(routes)];pp=[p for p in make_pairs(rt,37.5) if p['dmax']-p['dmin']>1e-8]
 n=rt['n'];m=len(pp);x=np.r_[0,rng.random(n-1)];weights=np.array([(p['dmax']-p['dmin'])/C for p in pp])
 _,value,_=fixed_branch_lp(n,pp,weights,x)
 costs=[];inc=np.zeros((n,2*m))
 for e,p in enumerate(pp):
  d=x[p['j']]-x[p['i']];opts=[]
  for c,r in p['arcs']:
   k=int(np.floor(d-c+.5));opts.append((max(abs(d-c-k)-r,0),c,r,k))
  _,c,r,k=min(opts);costs.extend([c+k+r,-c-k+r])
  inc[p['i'],2*e]=1;inc[p['j'],2*e]=-1;inc[p['j'],2*e+1]=1;inc[p['i'],2*e+1]=-1
 flow=linprog(costs,A_eq=inc,b_eq=np.zeros(n),bounds=[(0,float(w)) for w in np.repeat(weights,2)],method='highs')
 assert flow.success;flow_errors.append(abs(flow.fun+value));assert flow_errors[-1]<1e-7
small=[]
for L,g in [([100,500],[60,90,60]),([200,200],[60,90,60]),([350,350],[60,90,60])]:
 rt=dict(n=3,lengths_m=L,greens_s=g);pp=make_pairs(rt,36);ph=np.arange(0,120,.5)/C
 for weighted in [False,True]:
  z=solve(rt,36,pp,weighted,time_limit=4);weights=np.array([(p['dmax']-p['dmin'])/C if weighted else 1 for p in pp]);grid=np.inf
  for x1 in ph:
   val=np.zeros(len(ph))
   for p,w in zip(pp,weights):
    d=x1 if (p['i'],p['j'])==(0,1) else ph if (p['i'],p['j'])==(0,2) else ph-x1
    val+=w*np.minimum.reduce([np.maximum(abs((d-c+.5)%1-.5)-r,0) for c,r in p['arcs']])
   grid=min(grid,float(val.min()))
  grid*=C*C if weighted else C
  assert z['certified'];assert z['value']<=grid+1e-6
  small.append(dict(L=L,weighted=weighted,continuous=z['value'],half_second_grid=grid))
result=dict(n_pair_minima_checked=len(errors),max_pair_minimum_error_s=float(max(errors)),n_fixed_interval_flow_dual_checks=len(flow_errors),max_flow_dual_error=float(max(flow_errors)),small_periodic_MILP_checks=small)
(root/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
