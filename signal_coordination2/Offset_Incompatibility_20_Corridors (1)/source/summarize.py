from pathlib import Path
import json,itertools
import numpy as np,pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent.parent

def fit_predict(train,test,cols):
    a=train[cols].to_numpy(float);b=test[cols].to_numpy(float)
    mean=a.mean(0);sd=a.std(0);sd[sd<1e-12]=1
    X=np.c_[np.ones(len(a)),(a-mean)/sd];Z=np.c_[np.ones(len(b)),(b-mean)/sd]
    beta=np.linalg.lstsq(X,train.Dopt_s.to_numpy(),rcond=None)[0]
    return Z@beta,beta

def metrics(y,p):
    y=np.asarray(y);p=np.asarray(p);err=y-p
    return dict(R2=1-float(err@err)/float(((y-y.mean())**2).sum()),MAE=float(abs(err).mean()),RMSE=float(np.sqrt((err**2).mean())),prediction_r=float(np.corrcoef(y,p)[0,1]))

def main():
 results_path=ROOT/'certified_results.csv'
 z=pd.read_csv(results_path if results_path.exists() else ROOT/'case_results.csv');z['R0']=z.unweighted_value;z['Rw']=z.weighted_value;z['R0_fast']=z.unweighted_fast_value;z['Rw_fast']=z.weighted_fast_value
 for col in ['S1','R0','Rw','R0_fast','Rw_fast']:z.loc[abs(z[col])<1e-7,col]=0
 corr=[];cols=['S1','R0','Rw','R0_fast','Rw_fast']
 for label,d in [('all',z)]+[(f'n={n}',z[z.n==n]) for n in [4,6,8,10]]:
  for c in cols:
   r=d[c].corr(d.Dopt_s);sp=spearmanr(d[c],d.Dopt_s).statistic
   corr.append(dict(group=label,feature=c,n_conditions=len(d),pearson_r=r,spearman_r=sp))
 within=z.copy();within[cols+['Dopt_s']]=within[cols+['Dopt_s']]-within.groupby('route')[cols+['Dopt_s']].transform('mean')
 for c in cols:corr.append(dict(group='within_route',feature=c,n_conditions=len(z),pearson_r=within[c].corr(within.Dopt_s),spearman_r=spearmanr(within[c],within.Dopt_s).statistic))
 cr=pd.DataFrame(corr);cr.to_csv(ROOT/'correlations.csv',index=False)
 models={'S1':['S1'],'R0':['R0'],'Rw':['Rw'],'S1+R0':['S1','R0'],'S1+Rw':['S1','Rw'],'S1+R0_fast':['S1','R0_fast'],'S1+Rw_fast':['S1','Rw_fast'],'n+S1':['n','S1'],'n+S1+R0':['n','S1','R0'],'n+S1+Rw':['n','S1','Rw']}
 rows=[];preds=z[['route','n','speed_kmh','Dopt_s']].copy();coef=[]
 for name,cc in models.items():
  pin,beta=fit_predict(z,z,cc);cv=np.zeros(len(z))
  for rid in z.route.unique():
   mask=z.route==rid;cv[mask],_=fit_predict(z[~mask],z[mask],cc)
  for evaluation,p in [('in_sample',pin),('leave_one_corridor_out',cv)]:rows.append(dict(model=name,evaluation=evaluation,**metrics(z.Dopt_s,p)))
  preds[name+'_LOCO']=cv;coef.append(dict(model=name,columns=cc,standardized_coefficients=beta.tolist()))
 pd.DataFrame(rows).to_csv(ROOT/'model_comparisons.csv',index=False);preds.to_csv(ROOT/'cross_validated_predictions.csv',index=False)
 # Simple standardized least-squares collinearity diagnostics.
 vv=[]
 for name,cc in models.items():
  if len(cc)<2:continue
  for c in cc:
   other=[d for d in cc if d!=c];a=z[other].to_numpy();X=np.c_[np.ones(len(z)),a];y=z[c].to_numpy();p=X@np.linalg.lstsq(X,y,rcond=None)[0];r2=1-sum((p-y)**2)/sum((y-y.mean())**2)
   vv.append(dict(model=name,feature=c,VIF=float(1/max(1-r2,1e-12))))
 pd.DataFrame(vv).to_csv(ROOT/'vif.csv',index=False);z[['n','Dopt_s']+cols].corr().to_csv(ROOT/'feature_correlation_matrix.csv')
 per=[]
 for rid,d in z.groupby('route'):
  for c in cols:per.append(dict(route=rid,feature=c,pearson_r=d[c].corr(d.Dopt_s)))
 pd.DataFrame(per).to_csv(ROOT/'within_each_corridor_correlations.csv',index=False)
 times=[]
 for n,d in [('all',z)]+[(str(n),z[z.n==n]) for n in [4,6,8,10]]:
  for mode in ['unweighted','weighted']:
   for method in ['fast','verified']:
    col=mode+('_fast_seconds' if method=='fast' else '_seconds');v=d[col]+d.preprocessing_s
    times.append(dict(group=n,mode=mode,method=method,median_s=v.median(),mean_s=v.mean(),max_s=v.max(),total_s=v.sum(),certified_fraction=d[mode+'_certified'].mean(),median_relative_gap=d[mode+'_relative_gap'].median(),max_relative_gap=d[mode+'_relative_gap'].max()))
 pd.DataFrame(times).to_csv(ROOT/'runtime_summary.csv',index=False)
 # Partial association beyond S1 (descriptive, not independent significance tests).
 partial=[]
 X=np.c_[np.ones(len(z)),z.S1]
 dy=z.Dopt_s-X@np.linalg.lstsq(X,z.Dopt_s,rcond=None)[0]
 for c in ['R0','Rw']:
  dr=z[c]-X@np.linalg.lstsq(X,z[c],rcond=None)[0];partial.append(dict(feature=c,partial_r_controlling_S1=np.corrcoef(dy,dr)[0,1]))
 pd.DataFrame(partial).to_csv(ROOT/'partial_correlations.csv',index=False)
 summary=dict(n_conditions=len(z),correlations=cr[cr.group.isin(['all','within_route'])].to_dict('records'),models=rows,partial=partial,certified=dict(unweighted=int(z.unweighted_certified.sum()),weighted=int(z.weighted_certified.sum())),max_duality_error=float(max(z.unweighted_flow_dual_error.max(),z.weighted_flow_dual_error.max())))
 (ROOT/'summary.json').write_text(json.dumps(summary,indent=2));(ROOT/'regression_coefficients.json').write_text(json.dumps(coef,indent=2))
 plt.rcParams.update({'font.size':12,'axes.spines.top':False,'axes.spines.right':False})
 colors={4:'#2374AB',6:'#F39C35',8:'#37A087',10:'#9C65A8'}
 fig,axs=plt.subplots(1,3,figsize=(15,4.8))
 for ax,c,label in zip(axs,['S1','R0','Rw'],['Sum of ideal pair minima [s/vehicle]','Unweighted incompatibility [offset s]','Weighted incompatibility [index units]']):
  for n in [4,6,8,10]:
   d=z[z.n==n];ax.scatter(d[c],d.Dopt_s,s=24,color=colors[n],alpha=.65,label=f'{n} intersections')
  ax.set(xlabel=label,ylabel='Corridor delay, GA best found [s/vehicle]',title=f'{c} | Pearson r = {z[c].corr(z.Dopt_s):.3f}');ax.grid(alpha=.2)
 axs[0].legend(fontsize=9);fig.suptitle('20 corridors × 13 speeds | all intersection pairs',fontsize=16);fig.text(.5,.005,'R0/Rw: all 260 circular minima certified within numerical tolerances.',ha='center',fontsize=10);fig.tight_layout(rect=[0,.035,1,1]);fig.savefig(ROOT/'01_individual_correlations.png',dpi=180);fig.savefig(ROOT/'01_individual_correlations.svg');plt.close(fig)
 fig,axs=plt.subplots(1,3,figsize=(14,4.8))
 for ax,name in zip(axs,['S1','S1+R0','S1+Rw']):
  p=preds[name+'_LOCO'];mm=metrics(z.Dopt_s,p)
  for n in [4,6,8,10]:
   sel=z.n==n;ax.scatter(p[sel],z.Dopt_s[sel],s=24,color=colors[n],alpha=.65,label=f'{n} intersections')
  ax.plot([0,170],[0,170],color='gray',ls='--');ax.set(xlabel='Predicted delay [s/vehicle]',ylabel='GA best-found delay [s/vehicle]',title=f'{name}\nLOCO R²={mm["R2"]:.3f}, MAE={mm["MAE"]:.2f} s');ax.grid(alpha=.2)
 axs[0].legend(fontsize=9);fig.suptitle('Held-out corridor predictions | each test corridor excluded from training',fontsize=15);fig.text(.5,.005,'R0/Rw: all circular minima certified. Combinations use linear regression.',ha='center',fontsize=10);fig.tight_layout(rect=[0,.035,1,1]);fig.savefig(ROOT/'02_combined_models_LOCO.png',dpi=180);fig.savefig(ROOT/'02_combined_models_LOCO.svg');plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(12,4.7))
 for rid in ['N08_B','N10_D']:
  d=z[z.route==rid];axs[0].plot(d.speed_kmh,d.Dopt_s,'o-',label=rid)
  axs[1].plot(d.speed_kmh,d.Rw,'o-',label=rid)
 axs[0].set(xlabel='Speed [km/h]',ylabel='GA best-found delay [s/vehicle]');axs[1].set(xlabel='Speed [km/h]',ylabel='Weighted incompatibility [index units]')
 for ax in axs:ax.legend();ax.grid(alpha=.2)
 fig.tight_layout();fig.savefig(ROOT/'03_example_speed_profiles.png',dpi=180);plt.close(fig)
 print(cr[cr.group.isin(['all','within_route'])].to_string(index=False));print(pd.DataFrame(rows).to_string(index=False));print('certified',summary['certified']);print(pd.DataFrame(partial).to_string(index=False))

if __name__=='__main__':main()
