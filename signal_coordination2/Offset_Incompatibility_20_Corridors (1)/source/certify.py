"""Strengthened circular MILP with valid cycle cuts and phase reflection symmetry.

No traffic-optimal offsets are used. Certifies the circular incompatibility model,
not the original traffic-delay objective. SciPy/HiGHS numerical tolerances apply.
"""
import itertools,time,json,argparse
from pathlib import Path
import numpy as np,pandas as pd
from scipy.optimize import milp,Bounds,LinearConstraint,linprog
from scipy.sparse import lil_matrix
from model import make_pairs,evaluate,C

def build(route,v,weighted,incumbent,offsets,max_cycle=4):
    n=route['n'];g=np.array(route['greens_s'])/C;shift=(g-g[0])/2
    pairs=make_pairs(route,v);pp=[]
    for p in pairs:
        if p['dmax']-p['dmin']<1e-8:continue
        if len(p['arcs'])!=1:raise NotImplementedError('Separate arc disjunction needed')
        c,r=p['arcs'][0];cc=(c+(g[p['j']]-g[p['i']])/2)%1
        if min(abs(cc),abs(cc-1))<1e-8:cc=0.
        elif abs(cc-.5)<1e-8:cc=.5
        else:raise AssertionError(cc)
        pp.append(dict(**p,center=cc,radius=r))
    m=len(pp);weights=np.array([(p['dmax']-p['dmin'])/C if weighted else 1. for p in pp]);scale=C*C if weighted else C
    nv=n+2*m;obj=np.r_[np.zeros(n),weights,np.zeros(m)]
    lower=np.r_[np.zeros(n+m),np.full(m,-1.)];upper=np.r_[np.ones(n),np.full(m,.5),np.ones(m)];upper[0]=0
    # Reflection y -> -y leaves all 0/half-period preferred centers unchanged.
    if n>1:upper[1]=.5
    integer=np.zeros(nv);integer[n+m:]=1
    rows=[];rhs=[];lb=[];index={}
    def row(vals,lo=-np.inf,hi=np.inf):rows.append(vals);lb.append(lo);rhs.append(hi)
    for e,p in enumerate(pp):
        i,j=p['i'],p['j'];index[i,j]=e
        row({j:1,i:-1,n+e:-1,n+m+e:-1},hi=p['center']+p['radius'])
        row({j:-1,i:1,n+e:-1,n+m+e:1},hi=-p['center']+p['radius'])
    row({n+e:w for e,w in enumerate(weights)},hi=incumbent/scale+1e-8)
    cuts=0
    # Every closed walk has a center mismatch which tolerance radii + violations
    # must absorb. These are valid independently of all winding choices.
    for length in range(3,max_cycle+1):
      for nodes in itertools.combinations(range(n),length):
       for tail in itertools.permutations(nodes[1:]):
        cycle=(nodes[0],)+tail
        if cycle[1]>cycle[-1]:continue
        edges=[];center=0.;radius=0.;valid=True
        for u,w in zip(cycle,cycle[1:]+cycle[:1]):
            key=(min(u,w),max(u,w))
            if key not in index:valid=False;break
            e=index[key];p=pp[e];edges.append(e);center+=(1 if u<w else -1)*p['center'];radius+=p['radius']
        if not valid:continue
        gap=max(abs((center+.5)%1-.5)-radius,0.)
        if gap>1e-10:row({n+e:1 for e in edges},lo=gap);cuts+=1
    A=lil_matrix((len(rows),nv))
    for k,rr in enumerate(rows):
        for j,a in rr.items():A[k,j]=a
    return obj,integer,Bounds(lower,upper),LinearConstraint(A.tocsc(),np.array(lb),np.array(rhs)),pp,weights,scale,shift,cuts

def certify(route,v,weighted,value,x0,time_limit=30,max_cycle=4):
    start=time.perf_counter();c,integ,bounds,cons,pp,weights,scale,shift,cuts=build(route,v,weighted,value,x0,max_cycle)
    res=milp(c,integrality=integ,bounds=bounds,constraints=cons,options={'time_limit':time_limit,'mip_rel_gap':1e-8})
    best=value;xbest=x0
    if res.x is not None:
        xx=(res.x[:route['n']]-shift)%1
        vv=evaluate(xx,pp,weights)*scale
        if vv<best:best=vv;xbest=(xx*C).tolist()
    low=getattr(res,'mip_dual_bound',None)
    low=0. if low is None or not np.isfinite(low) else max(0.,float(low)*scale)
    gap=max(0.,best-low)/max(abs(best),1e-9)
    if low>best+1e-5:raise AssertionError(('invalid bound',best,low))
    return dict(value=float(best),lower_bound=float(min(low,best)),relative_gap=float(gap),certified=bool(gap<1e-6),status=int(res.status),seconds=time.perf_counter()-start,offsets_s=xbest,cycle_cuts=cuts,nodes=int(getattr(res,'mip_node_count',0) or 0))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--time-limit',type=float,default=30);ap.add_argument('--max-cycle',type=int,default=4);args=ap.parse_args()
    root=Path(__file__).resolve().parent.parent
    path=root/'certified_results.csv';z=pd.read_csv(path if path.exists() else root/'case_results.csv')
    offpath=root/'certified_offsets.json';oo=json.loads((offpath if offpath.exists() else root/'index_offsets.json').read_text());offsets={(a['route'],a['speed_kmh'],a['mode']):a['offsets_s'] for a in oo}
    routes={a['route']:a for a in json.loads((root/'inputs/routes.json').read_text())}
    logpath=root/'certification_log.json';logs=json.loads(logpath.read_text()) if logpath.exists() else []
    for idx,row in z.iterrows():
      for mode,weighted in [('unweighted',False),('weighted',True)]:
        if bool(row[mode+'_certified']):continue
        key=(row.route,float(row.speed_kmh),mode)
        out=certify(routes[row.route],row.speed_kmh,weighted,float(z.loc[idx,mode+'_value']),offsets[key],args.time_limit,args.max_cycle)
        offsets[key]=out.pop('offsets_s');logs.append(dict(route=row.route,speed_kmh=float(row.speed_kmh),mode=mode,**out))
        for k in ['value','lower_bound','relative_gap','certified','status']:z.loc[idx,mode+'_'+k]=out[k]
        z.loc[idx,mode+'_seconds']+=out['seconds']
        z.to_csv(path,index=False);logpath.write_text(json.dumps(logs,indent=2));offpath.write_text(json.dumps([dict(route=k[0],speed_kmh=k[1],mode=k[2],offsets_s=xx) for k,xx in offsets.items()],indent=2))
        print(row.route,row.speed_kmh,mode,'value',round(out['value'],6),'gap',round(out['relative_gap'],8),'certified',out['certified'],'seconds',round(out['seconds'],2),flush=True)
    print('certified',z.unweighted_certified.sum(),z.weighted_certified.sum(),flush=True)

if __name__=='__main__':main()
