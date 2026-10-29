from pathlib import Path
import json,time,sys
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fast_model import delay
root=Path(__file__).resolve().parent.parent
inp=root/'inputs'
routes={x['route']:x for x in json.loads((inp/'routes.json').read_text())}
ga=pd.read_csv(inp/'speed_summary.csv').set_index(['route','speed_kmh'])
rows=[]
for item in json.loads((inp/'certified_offsets.json').read_text()):
 rt=routes[item['route']];v=item['speed_kmh'];x=np.array(item['offsets_s']);g=np.array(rt['greens_s']);L=rt['lengths_m']
 # Reflection of green-center phases preserves this pair incompatibility objective.
 xr=(-x-(g-g[0]))%120
 st=time.perf_counter();d=delay(L,v,x,g,warm=24);d48=delay(L,v,x,g,warm=48)
 dr=delay(L,v,xr,g,warm=24);dr48=delay(L,v,xr,g,warm=48)
 assert max(abs(d-d48),abs(dr-dr48))<1e-6
 ref=max(0,float(ga.loc[(item['route'],v),'delay_s']))
 rows.append(dict(route=item['route'],n=rt['n'],speed_kmh=v,mode=item['mode'],GA_delay_s=ref,method_delay_s=max(d,0),reflected_delay_s=max(dr,0),best_of_reflection_s=max(min(d,dr),0),gap_s=d-ref,best_reflection_gap_s=min(d,dr)-ref,warmup_difference_s=max(abs(d-d48),abs(dr-dr48)),evaluation_seconds=time.perf_counter()-st,offsets_s=json.dumps(x.tolist()),reflected_offsets_s=json.dumps(xr.tolist())))
df=pd.DataFrame(rows);df.to_csv(root/'comparison.csv',index=False)
stats=[]
for label,col in [('saved_solution','method_delay_s'),('best_of_two_reflections','best_of_reflection_s')]:
 for (mode,n),z in df.groupby(['mode','n']):
  gap=z[col]-z.GA_delay_s
  stats.append(dict(solution=label,mode=mode,n=int(n),cases=len(z),mean_gap_s=gap.mean(),median_gap_s=gap.median(),max_gap_s=gap.max(),within_1s=int((gap<=1+1e-6).sum()),within_5s=int((gap<=5+1e-6).sum()),better_than_GA=int((gap < -1e-5).sum())))
 for mode,z in df.groupby('mode'):
  gap=z[col]-z.GA_delay_s
  stats.append(dict(solution=label,mode=mode,n='all',cases=len(z),mean_gap_s=gap.mean(),median_gap_s=gap.median(),max_gap_s=gap.max(),within_1s=int((gap<=1+1e-6).sum()),within_5s=int((gap<=5+1e-6).sum()),better_than_GA=int((gap < -1e-5).sum())))
pd.DataFrame(stats).to_csv(root/'summary.csv',index=False)
plt.rcParams.update({'font.size':13})
fig,axs=plt.subplots(1,2,figsize=(12,5),layout='constrained')
for ax,mode in zip(axs,['unweighted','weighted']):
 z=df[df['mode']==mode]
 for n,t in z.groupby('n'): ax.scatter(t.GA_delay_s,t.method_delay_s,label=f'{n} intersections',alpha=.65,s=25)
 lim=max(z.GA_delay_s.max(),z.method_delay_s.max())+5;ax.plot([0,lim],[0,lim],'k--',lw=1);ax.set(xlabel='GA delay [s/vehicle]',ylabel='Proposed offsets: delay [s/vehicle]',title=mode.capitalize());ax.legend(fontsize=10)
fig.savefig(root/'01_delay_comparison.png',dpi=180);fig.savefig(root/'01_delay_comparison.svg');plt.close(fig)
fig,axs=plt.subplots(4,5,figsize=(19,13),layout='constrained',sharex=True)
for ax,(rid,z) in zip(axs.flat,df.groupby('route',sort=True)):
 for mode,style in [('unweighted','--'),('weighted',':')]:
  t=z[z['mode']==mode].sort_values('speed_kmh');ax.plot(t.speed_kmh,t.method_delay_s,style,label=mode)
 ax.plot(t.speed_kmh,t.GA_delay_s,'k-',label='GA');ax.set_title(rid);ax.grid(alpha=.2)
axs[0,0].legend(fontsize=9);fig.supxlabel('Speed [km/h]');fig.supylabel('Average delay [s/vehicle]');fig.savefig(root/'02_all_corridors.png',dpi=170);plt.close(fig)
print(pd.DataFrame(stats).to_string(index=False))
