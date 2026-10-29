from pathlib import Path
import numpy as np,pandas as pd,json
from sklearn.base import clone
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor,ExtraTreesRegressor,HistGradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent.parent
z=pd.read_csv(root/'inputs/baseline_decomposition.csv')
B=z.B_anchor.to_numpy();y=z.residual_D_minus_B.to_numpy();D=z.Dopt_s.to_numpy();groups=z.route
models={'Ridge':make_pipeline(StandardScaler(),Ridge(alpha=10)),
 'RandomForest':RandomForestRegressor(n_estimators=250,max_depth=5,min_samples_leaf=5,max_features=1.0,random_state=42,n_jobs=2),
 'ExtraTrees':ExtraTreesRegressor(n_estimators=250,max_depth=5,min_samples_leaf=5,random_state=42,n_jobs=2),
 'HistGradientBoosting':HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=5,min_samples_leaf=15,l2_regularization=10,learning_rate=.05,random_state=42)}
feature_sets={'B_only':['B_anchor'],'B_R0':['B_anchor','R0'],'B_Rw':['B_anchor','Rw'],'B_R0_Rw':['B_anchor','R0','Rw']}
pred=z.copy();rows=[]
def score(name,fs,split,p):
 out=B+p
 return dict(model=name,features=fs,evaluation=split,MAE_delay_s=mean_absolute_error(D,out),RMSE_delay_s=np.sqrt(mean_squared_error(D,out)),R2_delay=r2_score(D,out),R2_residual=r2_score(y,p))
rows.append(score('Baseline_B','none','LOCO',np.zeros(len(z))))
pred['Baseline_B']=B
for fs,cols in feature_sets.items():
 X=z[cols]
 for name,model in models.items():
  p=np.empty(len(z))
  for tr,te in LeaveOneGroupOut().split(X,y,groups):
   m=clone(model).fit(X.iloc[tr],y[tr]);p[te]=m.predict(X.iloc[te])
  rows.append(score(name,fs,'LOCO',p));pred[fs+'__'+name]=B+p
  m=clone(model).fit(X,y);rows.append(score(name,fs,'training',m.predict(X)))
  print(fs,name,rows[-2],flush=True)
scores=pd.DataFrame(rows);scores.to_csv(root/'scores.csv',index=False);pred.to_csv(root/'predictions.csv',index=False)
per=[]
for col in pred.columns[len(z.columns):]:
 for n,t in pred.groupby('n'):
  per.append(dict(model=col,n=n,MAE_s=mean_absolute_error(t.Dopt_s,t[col]),RMSE_s=np.sqrt(mean_squared_error(t.Dopt_s,t[col]))))
pd.DataFrame(per).to_csv(root/'scores_by_intersections.csv',index=False)
best=scores[(scores.evaluation=='LOCO')&(scores.features=='B_R0_Rw')].sort_values('MAE_delay_s').iloc[0];key='B_R0_Rw__'+best.model
plt.rcParams.update({'font.size':12})
fig,axs=plt.subplots(1,2,figsize=(11,5),layout='constrained')
for ax,col,title in zip(axs,['Baseline_B',key],['Baseline: B','B + predicted residual ('+best.model+')']):
 for n,t in pred.groupby('n'):ax.scatter(t.Dopt_s,t[col],s=23,alpha=.7,label=f'{n} intersections')
 ax.plot([0,180],[0,180],'k--');ax.set(xlabel='GA delay [s/vehicle]',ylabel='Predicted delay [s/vehicle]',title=title);ax.legend(fontsize=9)
fig.savefig(root/'01_predictions_LOCO.png',dpi=180);plt.close(fig)
print(scores[scores.evaluation=='LOCO'].sort_values('MAE_delay_s').to_string(index=False),flush=True)
