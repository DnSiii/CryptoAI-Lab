"""Phase195-AN DATA_ONLY immutable V99 research paper prefix guard.
Never repairs, rewrites, promotes, or publishes any historical evidence.
"""
import json,sys,zipfile
from pathlib import Path
IDENTITY=('mode','version','schema_version','base_capital_brl','paper_start_after_timestamp','same_boundary_for_all_variants','real_orders_enabled')
def guard(old,new):
 issues=[];results={}
 for key in IDENTITY:
  if old.get(key)!=new.get(key):issues.append('IDENTITY_CHANGED:'+key)
 if old.get('mode')!='PAPER_ONLY' or old.get('real_orders_enabled') is not False:issues.append('UNSAFE_PAPER_MODE')
 if set(old.get('variants',{}))!=set(new.get('variants',{})):issues.append('VARIANT_SET_CHANGED')
 if old.get('backtest_reference')!=new.get('backtest_reference'):issues.append('HISTORICAL_BACKTEST_CHANGED')
 boundary=old.get('paper_start_after_timestamp','')
 for label,ref in new.get('backtest_reference',{}).items():
  curve=ref.get('curve',[])
  if not isinstance(curve,list) or any(not isinstance(row,dict) or not isinstance(row.get('timestamp'),str) for row in curve):
   issues.append('INVALID_BACKTEST_CURVE:'+label)
  elif any(row['timestamp']>boundary for row in curve):issues.append('BACKTEST_CROSSES_PAPER_BOUNDARY:'+label)
 for name,a in old.get('variants',{}).items():
  b=new.get('variants',{}).get(name)
  if b is None:continue
  o=a.get('equity_curve',[]);n=b.get('equity_curve',[])
  if not o or len(n)<len(o):
   results[name]={'gate':'BLOCK_TRUNCATION'};issues.append('TRUNCATION:'+name);continue
  ot=[x['timestamp'] for x in o];nt=[x['timestamp'] for x in n]
  if len(set(ot))!=len(ot) or len(set(nt))!=len(nt) or nt[:len(o)]!=ot:
   results[name]={'gate':'BLOCK_TIMESTAMPS'};issues.append('TIMESTAMPS:'+name);continue
  changed=[i for i in range(len(o)) if o[i]!=n[i]]
  if changed:issues.append('EQUITY_REWRITE:'+name)
  ao=a.get('operations',[]);bo=b.get('operations',[])
  if not isinstance(ao,list) or not isinstance(bo,list):issues.append('INVALID_OPERATIONS:'+name);continue
  ai={(r['timestamp'],r['symbol']):r for r in ao};bi={(r['timestamp'],r['symbol']):r for r in bo}
  if len(ai)!=len(ao) or len(bi)!=len(bo):issues.append('DUPLICATE_OPERATIONS:'+name)
  changes=sum(ai[k]!=bi[k] for k in ai.keys()&bi.keys())
  if changes:issues.append('OPERATION_REWRITE:'+name)
  results[name]={'gate':'BLOCK_REWRITE' if changed or changes else 'PASS_PREFIX',
   'changed_equity_hours':len(changed),'first_changed_equity_hour':ot[changed[0]] if changed else None,
   'changed_retained_operations':changes,'operations_capped':len(ao)==1500 or len(bo)==1500}
 return {'gate':'BLOCK_PUBLICATION' if issues else 'PASS_APPEND_ONLY','issues':issues,
         'variants':results,'paper_history_rewrite_authorized':False,'promotion_authorized':False}
def load(path):
 with zipfile.ZipFile(path) as z:return json.loads(z.read('reports/paper_v99_research_ledger.json'))
if __name__=='__main__':
 result=guard(load(Path(sys.argv[1])),load(Path(sys.argv[2])))
 print(json.dumps(result,indent=2,sort_keys=True))
 if result['gate']!='PASS_APPEND_ONLY':sys.exit(2)
