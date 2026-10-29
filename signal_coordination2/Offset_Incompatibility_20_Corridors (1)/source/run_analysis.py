from pathlib import Path
import json,time,argparse
import numpy as np,pandas as pd
from model import make_pairs,solve,C

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--time-limit',type=float,default=1.);ap.add_argument('--fast-only',action='store_true');args=ap.parse_args()
 if args.fast_only:args.time_limit=0.
 root=Path(__file__).resolve().parent.parent;routes=json.loads((root/'inputs/routes.json').read_text());summary=pd.read_csv(root/'inputs/speed_summary.csv')
 rows=[];pairs_all=[];offsets=[];start=time.perf_counter()
 for rt in routes:
  for _,z in summary[summary.route==rt['route']].sort_values('speed_kmh').iterrows():
   t=time.perf_counter();pp=make_pairs(rt,z.speed_kmh);prep=time.perf_counter()-t
   row=dict(route=rt['route'],n=rt['n'],speed_kmh=z.speed_kmh,Dopt_s=max(0.,z.delay_s),GA_recorded_runtime_s=z.total_runtime_s,S1=sum(p['dmin'] for p in pp),preprocessing_s=prep)
   for p in pp:
    pairs_all.append(dict(route=rt['route'],speed_kmh=z.speed_kmh,**{k:val for k,val in p.items() if k!='arcs'},weight=p['dmax']-p['dmin'],arcs_s=json.dumps([[float(c*C),float(r*C)] for c,r in p['arcs']])))
   for mode,weighted in [('unweighted',False),('weighted',True)]:
    ans=solve(rt,z.speed_kmh,pp,weighted=weighted,time_limit=args.time_limit)
    offsets.append(dict(route=rt['route'],speed_kmh=z.speed_kmh,mode=mode,offsets_s=ans.pop('offsets_s')))
    row.update({mode+'_'+k:val for k,val in ans.items()})
   rows.append(row)
   pd.DataFrame(rows).to_csv(root/'case_results.csv',index=False)
  print(rt['route'],len(rows),'conditions; elapsed',round(time.perf_counter()-start,1),'s',flush=True)
 pd.DataFrame(pairs_all).to_csv(root/'pair_inputs.csv',index=False);(root/'index_offsets.json').write_text(json.dumps(offsets,indent=2))
 (root/'run_metadata.json').write_text(json.dumps(dict(total_wall_s=time.perf_counter()-start,milp_time_limit_s=args.time_limit,n_conditions=len(rows),n_pair_conditions=len(pairs_all)),indent=2))

if __name__=='__main__':main()
