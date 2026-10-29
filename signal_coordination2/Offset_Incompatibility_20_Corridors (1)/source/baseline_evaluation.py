"""Compare ideal-pair sums and reference-intersection (anchor) path baseline.

Anchor baseline B[j]=max_{i<j}(B[i]+delta_ij), B[0]=0.
This is a diagnostic theoretical baseline, NOT asserted to be a universal lower
bound on the actual platoon model. D-B contains all model discrepancies too.
"""
from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from summarize import fit_predict,metrics

def main():
 root=Path(__file__).resolve().parent.parent
 z=pd.read_csv(root/('certified_results.csv' if (root/'certified_results.csv').exists() else 'case_results.csv'))
 pairs=pd.read_csv(root/'pair_inputs.csv');rows=[]
 for _,a in z.iterrows():
  q=pairs[(pairs.route==a.route)&(pairs.speed_kmh==a.speed_kmh)];n=int(a.n);b=np.zeros(n);path={0:[0]}
  for j in range(1,n):
   candidates=[b[i]+float(q[(q.i==i)&(q.j==j)].dmin.iloc[0]) for i in range(j)];i=int(np.argmax(candidates));b[j]=candidates[i];path[j]=path[i]+[j]
  rows.append(dict(route=a.route,n=n,speed_kmh=a.speed_kmh,B_anchor=b[-1],Dopt_s=a.Dopt_s,S1=a.S1,R0=a.unweighted_value,Rw=a.weighted_value,anchor_path=json.dumps(path[n-1])))
 x=pd.DataFrame(rows);x['residual_D_minus_B']=x.Dopt_s-x.B_anchor;x.to_csv(root/'baseline_decomposition.csv',index=False)
 cols=['Dopt_s','S1','B_anchor','R0','Rw','residual_D_minus_B'];x[cols].corr().to_csv(root/'baseline_correlation_matrix.csv')
 within=x.copy();within[cols]-=within.groupby('route')[cols].transform('mean');within[cols].corr().to_csv(root/'baseline_within_route_correlation_matrix.csv')
 result=[];pred=x[['route','speed_kmh','Dopt_s']].copy()
 for name,cc in [('B',['B_anchor']),('B+R0',['B_anchor','R0']),('B+Rw',['B_anchor','Rw'])]:
  pin,beta=fit_predict(x,x,cc);cv=np.zeros(len(x))
  for rid in x.route.unique():
   mask=x.route==rid;cv[mask],_=fit_predict(x[~mask],x[mask],cc)
  for evaluation,p in [('in_sample',pin),('leave_one_corridor_out',cv)]:result.append(dict(model=name,evaluation=evaluation,**metrics(x.Dopt_s,p)))
  pred[name+'_LOCO']=cv
 pd.DataFrame(result).to_csv(root/'baseline_model_comparisons.csv',index=False);pred.to_csv(root/'baseline_cv_predictions.csv',index=False)
 zeros=x[x.R0<1e-6].copy();zeros.to_csv(root/'zero_incompatibility_cases.csv',index=False)
 meta=dict(anchor_vs_D_r=x.B_anchor.corr(x.Dopt_s),anchor_vs_D_within_route_r=within.B_anchor.corr(within.Dopt_s),residual_vs_R0_r=x.residual_D_minus_B.corr(x.R0),residual_vs_Rw_r=x.residual_D_minus_B.corr(x.Rw),residual_vs_R0_within_route_r=within.residual_D_minus_B.corr(within.R0),residual_vs_Rw_within_route_r=within.residual_D_minus_B.corr(within.Rw),n_zero_incompatibility=len(zeros),zero_incompatibility_D_min=float(zeros.Dopt_s.min()),zero_incompatibility_D_max=float(zeros.Dopt_s.max()),n_D_below_pair_sum=int((x.Dopt_s<x.S1-1e-6).sum()),n_D_below_anchor=int((x.Dopt_s<x.B_anchor-1e-6).sum()))
 (root/'baseline_summary.json').write_text(json.dumps(meta,indent=2))
 plt.rcParams.update({'font.size':12,'axes.spines.top':False,'axes.spines.right':False});fig,axs=plt.subplots(1,3,figsize=(15,4.7));colors={4:'#2374AB',6:'#F39C35',8:'#37A087',10:'#9C65A8'}
 for n in [4,6,8,10]:
  d=x[x.n==n];axs[0].scatter(d.B_anchor,d.Dopt_s,s=24,alpha=.65,color=colors[n],label=f'{n} intersections');axs[1].scatter(d.R0,d.residual_D_minus_B,s=24,alpha=.65,color=colors[n]);axs[2].scatter(d.Rw,d.residual_D_minus_B,s=24,alpha=.65,color=colors[n])
 axs[0].plot([0,160],[0,160],'--',color='gray');axs[0].set(xlabel='Anchor baseline B [s/vehicle]',ylabel='GA best-found delay [s/vehicle]',title=f'Baseline vs total delay | r={meta["anchor_vs_D_r"]:.3f}');axs[0].legend(fontsize=9)
 axs[1].set(xlabel='Unweighted incompatibility [offset s]',ylabel='D - B [s/vehicle]',title=f'Residual vs R0 | r={meta["residual_vs_R0_r"]:.3f}')
 axs[2].set(xlabel='Weighted incompatibility [index units]',ylabel='D - B [s/vehicle]',title=f'Residual vs Rw | r={meta["residual_vs_Rw_r"]:.3f}')
 for ax in axs:ax.grid(alpha=.2)
 fig.text(.5,.005,'D - B is a baseline discrepancy, not an identified causal contribution of offset incompatibility.',ha='center',fontsize=10);fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(root/'04_anchor_baseline_and_residual.png',dpi=180);fig.savefig(root/'04_anchor_baseline_and_residual.svg');plt.close(fig)
 print(json.dumps(meta,indent=2));print(pd.DataFrame(result).to_string(index=False))

if __name__=='__main__':main()
