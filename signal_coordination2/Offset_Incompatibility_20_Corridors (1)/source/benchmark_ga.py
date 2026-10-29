"""Optional same-environment timing against the user's original GA code.
Usage: python benchmark_ga.py --original-code /absolute/path/to/actual_run_code
The original queue_fast.so must have been compiled in that directory.
This is a 3-case timing check, not a new 20-corridor simulation.
"""
from pathlib import Path
import argparse,sys,json,time
ap=argparse.ArgumentParser();ap.add_argument('--original-code',required=True);args=ap.parse_args()
sys.path.insert(0,args.original_code)
from ga_model import ga
root=Path(__file__).resolve().parent.parent;routes=json.loads((root/'inputs/routes.json').read_text());rows=[]
for rid in ['N04_A','N08_B','N10_D']:
 rt=next(x for x in routes if x['route']==rid);start=time.perf_counter();runs=[]
 for seed in [11,22,33]:
  z,_=ga(rt['lengths_m'],40,rt['greens_s'],seed,popsize=96,generations=150,warmup=12)
  assert abs(z['delay_s']-z['extended_warmup_delay_s'])<1e-6;runs.append(z)
 rows.append(dict(route=rid,speed_kmh=40,three_seed_runtime_s=time.perf_counter()-start,best_found_delay_s=min(z['delay_s'] for z in runs),warmup_cycles=12,population=96,generations=150,seeds=[11,22,33]))
(root/'current_environment_GA_benchmark.json').write_text(json.dumps(rows,indent=2))
