"""Theory-based circular offset incompatibility; time is in cycles internally.

Sakakibara & Oguchi (2025), equations 15,16,20,21,25.
All pairs including nonadjacent. NO optimized traffic offsets are inputs.
"""
import time,itertools
import numpy as np
from scipy.optimize import linprog,milp,Bounds,LinearConstraint
from scipy.sparse import lil_matrix
C=120.;P=.5

def directional(z,gs,gd):
    rd=1-gs-gd+P;z=np.mod(z,1.)
    if rd<=1e-12:return np.zeros_like(z)
    return np.where((z>=gd-P)&(z<gd),rd*(z-gd+P)/P,
           np.where((z>=gd)&(z<1-gs+P),1-gs-z+P,0.))

def theory_curve(phi,lam,gi,gj):
    return .5*(directional(lam-np.asarray(phi),gi,gj)+directional(lam+np.asarray(phi),gj,gi))

def pair_features(lam,gi,gj):
    # All exact breakpoints of the two directional piecewise-linear functions.
    knots=np.mod([0,lam-(gj-P),lam-gj,lam-(1-gi+P),
                  gi-P-lam,gi-lam,1-gj+P-lam],1.)
    knots=np.sort(np.r_[0.,knots,1.]);knots=knots[np.r_[True,np.diff(knots)>1e-10]]
    values=theory_curve(knots,lam,gi,gj);lo=float(values.min());hi=float(values.max());tol=1e-9
    if hi-lo<tol:return dict(dmin=lo*C,dmax=hi*C,arcs=[(.5,.5)])
    segments=[]
    for k in range(len(knots)-1):
        if abs(values[k]-lo)<tol and abs(values[k+1]-lo)<tol:segments.append((knots[k],knots[k+1]))
    for k,t in enumerate(knots):
        if abs(values[k]-lo)<tol:segments.append((t,t))
    segments.sort();merged=[]
    for a,b in segments:
        if merged and a<=merged[-1][1]+tol:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:merged.append((a,b))
    if len(merged)>1 and merged[0][0]<tol and merged[-1][1]>1-tol:
        first=merged.pop(0);last=merged.pop(-1);merged.append((last[0],first[1]+1))
    arcs=[(((a+b)/2)%1,(b-a)/2) for a,b in merged]
    return dict(dmin=lo*C,dmax=hi*C,arcs=arcs)

def make_pairs(route,v):
    pos=np.r_[0,np.cumsum(route['lengths_m'])];g=np.array(route['greens_s'])/C
    ans=[]
    for i,j in itertools.combinations(range(len(g)),2):
        lam=(pos[j]-pos[i])/(C*(v/3.6));p=pair_features(lam,g[i],g[j]);p.update(i=i,j=j,L_m=float(pos[j]-pos[i]),lam=float(lam),gi=g[i],gj=g[j]);ans.append(p)
    return ans

def pair_distance(d,arcs):
    return min(max(abs((d-c+.5)%1-.5)-r,0.) for c,r in arcs)

def evaluate(x,pairs,weights):
    return float(sum(w*pair_distance(x[p['j']]-x[p['i']],p['arcs']) for p,w in zip(pairs,weights)))

def fixed_branch_lp(n,pairs,weights,x):
    """Choose nearest arc/winding from x, then solve the continuous LP exactly.
    This LP is the dual of the fixed-interval capacitated min-cost circulation.
    The full periodic problem is NOT claimed to be a single circulation problem.
    """
    m=len(pairs);A=np.zeros((2*m,n+m));b=np.zeros(2*m);selected=[]
    for e,p in enumerate(pairs):
        i,j=p['i'],p['j'];d=x[j]-x[i]
        opts=[]
        for c,r in p['arcs']:
            k=int(np.floor(d-c+.5));gap=max(abs(d-c-k)-r,0);opts.append((gap,c,r,k))
        _,c,r,k=min(opts);selected.append((c,r,k))
        A[2*e,j]=1;A[2*e,i]=-1;A[2*e,n+e]=-1;b[2*e]=c+k+r
        A[2*e+1,j]=-1;A[2*e+1,i]=1;A[2*e+1,n+e]=-1;b[2*e+1]=-c-k+r
    obj=np.r_[np.zeros(n),weights];res=linprog(obj,A_ub=A,b_ub=b,bounds=[(0,0)]+[(None,None)]*(n-1)+[(0,None)]*m,method='highs')
    if not res.success:raise RuntimeError(res.message)
    # Fixed-interval min-cost circulation, costs=b, capacities=weights.
    # Primal/dual equality can be checked without reconstructing all cycles.
    f=-res.ineqlin.marginals
    err=abs(float(-b@f)-res.fun)
    if err>1e-7:raise AssertionError(('flow_dual_gap',err))
    return res.x[:n]%1,res.fun,err

def heuristic(n,pairs,weights,tau):
    starts=[np.zeros(n),np.r_[0,np.cumsum(tau)]%1,(-np.r_[0,np.cumsum(tau)])%1]
    rng=np.random.default_rng(20261030)
    starts += [np.r_[0,rng.random(n-1)] for _ in range(3)]
    best=(np.inf,None);maxerr=0.;calls=0
    for x in starts:
        # Exact 1-node minimization of circular piecewise-linear distances.
        # Its breakpoints are arc boundaries and gap midpoints.
        for sweep in range(4):
            improved=False
            for node in range(1,n):
                incident=[(p,w) for p,w in zip(pairs,weights) if node in [p['i'],p['j']]]
                cand=[x[node]]
                for p,w in incident:
                    centers=sorted([c for c,r in p['arcs']]);knots=[]
                    for c,r in p['arcs']:knots += [c-r,c+r]
                    aa=sorted([(c-r)%1 for c,r in p['arcs']]+[(c+r)%1 for c,r in p['arcs']])
                    for k,a in enumerate(aa):knots.append((a+(aa[(k+1)%len(aa)]-a)%1/2)%1)
                    other=p['i'] if node==p['j'] else p['j'];sgn=1 if node==p['j'] else -1
                    cand += [float((x[other]+sgn*t)%1) for t in knots]
                cand=np.array(cand);cost=np.zeros(len(cand))
                for p,w in incident:
                    dd=cand-x[p['i']] if node==p['j'] else x[p['j']]-cand
                    cost += w*np.minimum.reduce([np.maximum(np.abs((dd-c+.5)%1-.5)-r,0) for c,r in p['arcs']])
                ix=int(np.argmin(cost))
                if cost[ix]<cost[0]-1e-10:x[node]=cand[ix];improved=True
            if not improved:break
        old=evaluate(x,pairs,weights)
        if old<best[0]:best=(old,x.copy())
        for _ in range(8):
            xn,_,err=fixed_branch_lp(n,pairs,weights,x);calls+=1;maxerr=max(maxerr,err)
            val=evaluate(xn,pairs,weights)
            if val<best[0]-1e-10:best=(val,xn.copy())
            x=xn
            if val>=old-1e-9:break
            old=val
    return best,maxerr,calls

def solve(route,v,pairs,weighted=False,time_limit=1.):
    start=time.perf_counter();n=route['n'];active=[p for p in pairs if p['dmax']-p['dmin']>1e-8]
    # Completely flat pair functions have all phases optimal: zero incompatibility.
    if not active:return dict(value=0.,fast_value=0.,fast_seconds=time.perf_counter()-start,lower_bound=0.,relative_gap=0.,certified=True,status=0,seconds=time.perf_counter()-start,offsets_s=[0.]*n,lp_calls=0,flow_dual_error=0.)
    m=len(active);weights=np.array([(p['dmax']-p['dmin'])/C if weighted else 1. for p in active])
    tau=np.array(route['lengths_m'])/(v/3.6)/C
    (upper,xbest),err,calls=heuristic(n,active,weights,tau)
    scale=C*C if weighted else C
    fast_value=upper*scale;fast_seconds=time.perf_counter()-start
    if upper<1e-8:return dict(value=upper*scale,fast_value=fast_value,fast_seconds=fast_seconds,lower_bound=0.,relative_gap=0.,certified=True,status=0,seconds=time.perf_counter()-start,offsets_s=(xbest*C).tolist(),lp_calls=calls,flow_dual_error=err)
    if time_limit<=0:return dict(value=fast_value,fast_value=fast_value,fast_seconds=fast_seconds,lower_bound=0.,relative_gap=1.,certified=False,status=1,seconds=time.perf_counter()-start,offsets_s=(xbest*C).tolist(),lp_calls=calls,flow_dual_error=err)
    # Exact circular distance to a union of arcs. Integer winding k, branch z.
    # r_e is shared by the two sides: a distance to the chosen interval.
    zbase=n+2*m;nz=sum(len(p['arcs']) for p in active if len(p['arcs'])>1);nv=zbase+nz
    obj=np.zeros(nv);obj[n:n+m]=weights
    lb=np.r_[np.zeros(n+m),np.full(m,-2.),np.zeros(nz)];ub=np.r_[np.ones(n),np.full(m,.5),np.full(m,2.),np.ones(nz)];ub[0]=0
    integer=np.zeros(nv);integer[n+m:n+2*m]=1;integer[zbase:]=1
    rows=[];rhs=[];equal_rows=[];z=zbase
    for e,p in enumerate(active):
        aa=p['arcs'];multiple=len(aa)>1
        if multiple:
            rr={z+k:1. for k in range(len(aa))};equal_rows.append(rr)
        for k,(c,r) in enumerate(aa):
            for sign in [1,-1]:
                row={p['j']:sign,p['i']:-sign,n+e:-1,n+m+e:-sign}
                bound=sign*c+r
                if multiple:row[z+k]=4.;bound+=4.
                rows.append(row);rhs.append(bound)
        if multiple:z+=len(aa)
    # Known feasible objective provides a cutoff, without using traffic-optimal offsets.
    rows.append({n+e:float(w) for e,w in enumerate(weights)});rhs.append(upper+1e-8)
    nr=len(rows);A=lil_matrix((nr+len(equal_rows),nv));lower=np.full(nr+len(equal_rows),-np.inf);upper_rows=np.r_[rhs,np.ones(len(equal_rows))]
    for k,row in enumerate(rows+equal_rows):
        for j,a in row.items():A[k,j]=a
    lower[nr:]=1.
    res=milp(obj,integrality=integer,bounds=Bounds(lb,ub),constraints=LinearConstraint(A.tocsc(),lower,upper_rows),options={'time_limit':time_limit,'mip_rel_gap':1e-7})
    if res.x is not None:
        val=evaluate(res.x[:n],active,weights)
        if val<upper:upper=val;xbest=res.x[:n]
    bound=getattr(res,'mip_dual_bound',0.)
    if bound is None or not np.isfinite(bound):bound=0.
    bound=max(0.,min(float(bound),upper));gap=(upper-bound)/max(upper,1e-9)
    return dict(value=upper*scale,fast_value=fast_value,fast_seconds=fast_seconds,lower_bound=bound*scale,relative_gap=gap,certified=gap<1e-6,status=int(res.status),seconds=time.perf_counter()-start,offsets_s=(xbest*C).tolist(),lp_calls=calls,flow_dual_error=err)
