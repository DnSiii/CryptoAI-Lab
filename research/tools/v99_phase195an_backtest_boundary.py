"""DATA_ONLY projection: exclude forward-paper points from historical backtest."""
import json,sys,zipfile
from pathlib import Path
def load(path):
 with zipfile.ZipFile(path) as z:return json.loads(z.read('reports/paper_v99_research_ledger.json'))
def audit(old,new):
 boundary=old['paper_start_after_timestamp']
 if boundary!=new['paper_start_after_timestamp']:raise ValueError('boundary changed')
 out={}
 for key in old['backtest_reference']:
  a=old['backtest_reference'][key]['curve'];b=new['backtest_reference'][key]['curve']
  ax=[r for r in a if r['timestamp']<boundary];bx=[r for r in b if r['timestamp']<boundary]
  if len(ax)!=len(bx):raise ValueError('historical length changed')
  changed=[i for i,(x,y) in enumerate(zip(ax,bx)) if x!=y]
  out[key]={'old_contaminated_points':len(a)-len(ax),'new_contaminated_points':len(b)-len(bx),
            'prepaper_points':len(ax),'changed_prepaper_points':len(changed),
            'first_changed_prepaper_timestamp':ax[changed[0]]['timestamp'] if changed else None,
            'gate':'BLOCK_PREPAPER_REWRITE' if changed else 'PASS_PREPAPER_PREFIX'}
 return {'phase':'195-AN','status':'DATA_ONLY_HOLD','boundary':boundary,'variants':out,
         'paper_rewrite_authorized':False,'promotion_authorized':False}
if __name__=='__main__':
 print(json.dumps(audit(load(Path(sys.argv[1])),load(Path(sys.argv[2]))),indent=2,sort_keys=True))
