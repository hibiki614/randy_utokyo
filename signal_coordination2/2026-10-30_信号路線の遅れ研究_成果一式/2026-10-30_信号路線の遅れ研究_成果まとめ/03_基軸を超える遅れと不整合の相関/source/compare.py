"""Direct comparison requested: GA delay minus anchor delay vs incompatibility.
Run: python source/compare.py
"""
from pathlib import Path
import json,zipfile
import numpy as np,pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent.parent
z=pd.read_csv(ROOT/'comparison_inputs.csv')
z['residual_D_minus_B']=z.Dopt_s-z.B_anchor
z.loc[abs(z.residual_D_minus_B)<1e-7,'residual_D_minus_B']=0.
for c in ['R0','Rw']:z.loc[abs(z[c])<1e-7,c]=0.
cols=['residual_D_minus_B','R0','Rw'];within=z.copy();within[cols]-=within.groupby('route')[cols].transform('mean')
rows=[]
for label,d in [('all',z),('within_route_centered',within)]+[(f'n={n}',z[z.n==n]) for n in [4,6,8,10]]:
 for c in ['R0','Rw']:
  rows.append(dict(group=label,indicator=c,count=len(d),pearson_r=d[c].corr(d.residual_D_minus_B),spearman_r=spearmanr(d[c],d.residual_D_minus_B).statistic))
pd.DataFrame(rows).to_csv(ROOT/'correlations.csv',index=False)
routes=[]
for rid,d in z.groupby('route'):
 for c in ['R0','Rw']:routes.append(dict(route=rid,n=int(d.n.iloc[0]),indicator=c,count=len(d),pearson_r=d[c].corr(d.residual_D_minus_B),spearman_r=spearmanr(d[c],d.residual_D_minus_B).statistic,residual_min_s=d.residual_D_minus_B.min(),residual_max_s=d.residual_D_minus_B.max()))
r=pd.DataFrame(routes);r.to_csv(ROOT/'per_corridor_correlations.csv',index=False);z.to_csv(ROOT/'comparison_data.csv',index=False)
plt.rcParams.update({'font.size':14,'axes.spines.top':False,'axes.spines.right':False});colors={4:'#2374AB',6:'#F39C35',8:'#37A087',10:'#9C65A8'}
for centered,df,name in [(False,z,'01_residual_vs_incompatibility'),(True,within,'02_within_corridor_changes')]:
 fig,axs=plt.subplots(1,2,figsize=(12.5,5.2))
 for ax,c,label in zip(axs,['R0','Rw'],['Unweighted incompatibility [offset s]','Weighted incompatibility [index units]']):
  for n in [4,6,8,10]:
   d=df[df.n==n];ax.scatter(d[c],d.residual_D_minus_B,s=29,color=colors[n],alpha=.7,label=f'{n} intersections')
  ax.set(xlabel=label+('\n(deviation from corridor mean)' if centered else ''),ylabel=r'$D_{GA}-B$ [s/vehicle]'+('\n(deviation from corridor mean)' if centered else ''),title=f'{c} | Pearson r={df[c].corr(df.residual_D_minus_B):.3f}');ax.grid(alpha=.2)
  if centered:ax.axhline(0,color='gray',lw=.7);ax.axvline(0,color='gray',lw=.7)
 axs[0].legend(fontsize=11);fig.suptitle('Same-corridor speed changes' if centered else 'GA delay minus anchor delay | 20 corridors × 13 speeds',fontsize=16)
 fig.text(.5,.005,'The residual is a baseline discrepancy, not an identified causal contribution of offset incompatibility.',ha='center',fontsize=10);fig.tight_layout(rect=[0,.04,1,1])
 for ext in ['png','svg']:fig.savefig(ROOT/f'{name}.{ext}',dpi=180)
 plt.close(fig)
fig,ax=plt.subplots(figsize=(12,4.7));ids=sorted(z.route.unique());xx=np.arange(len(ids));p=r.pivot(index='route',columns='indicator',values='pearson_r').reindex(ids)
ax.bar(xx-.18,p.R0,width=.36,label='Unweighted');ax.bar(xx+.18,p.Rw,width=.36,label='Weighted');ax.axhline(0,color='black',lw=.8);ax.set_xticks(xx,ids,rotation=55,ha='right');ax.set(ylabel='Within-corridor Pearson r',ylim=(-1.05,1.05),title=r'Each corridor: $D_{GA}-B$ vs incompatibility (13 speeds)');ax.legend(loc='upper right');ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(ROOT/'03_each_corridor_correlations.png',dpi=180);plt.close(fig)
meta=dict(n_cases=len(z),n_corridors=z.route.nunique(),residual_min_s=float(z.residual_D_minus_B.min()),residual_max_s=float(z.residual_D_minus_B.max()),zero_incompatibility_count=int((z.R0<1e-7).sum()),zero_incompatibility_residual_max_s=float(z.loc[z.R0<1e-7,'residual_D_minus_B'].max()))
(ROOT/'summary.json').write_text(json.dumps(meta,indent=2))
print(pd.DataFrame(rows).to_string(index=False))
