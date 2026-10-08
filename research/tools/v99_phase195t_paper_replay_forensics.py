"""Phase195-T read-only forensic classifier for durable forward paper history.
Never repairs, overwrites, backfills or weakens append-only publication gates.
"""
import argparse,json,zipfile
LEDGERS=("paper_v13_ledger.json","paper_v14_ledger.json","paper_v15_ledger.json","paper_v16_ledger.json","paper_v99_ledger.json","paper_core_comparison_v1_ledger.json","paper_opportunity_v1_ledger.json","paper_combined_v1_ledger.json")
def compare(old,new,name):
 if not isinstance(old,dict) or not isinstance(new,dict):raise ValueError("ledger_not_object")
 r={"ledger":name,"published_end":old.get("latest_data_timestamp"),"replayed_end":new.get("latest_data_timestamp"),"fields":{},"publication_authorized":False}
 for key in ("mode","candidate","base_capital_brl","paper_start_after_timestamp","opening_snapshot"):
  if old.get(key)!=new.get(key):r.update(decision="HOLD_BOUNDARY_CHANGED",reason=key);return r
 mismatch=[]
 for field in ("equity_curve","decisions"):
  a,b=old.get(field,[]),new.get(field,[])
  if not isinstance(a,list) or not isinstance(b,list):raise ValueError("invalid_"+field)
  if len(b)<len(a):
   r["fields"][field]={"old_rows":len(a),"new_rows":len(b),"decision":"TRUNCATED"};mismatch.append((field,-1));continue
  first=next((i for i in range(len(a)) if a[i]!=b[i]),None)
  item={"old_rows":len(a),"new_rows":len(b),"first_mismatch_index":first}
  if first is not None:
   x,y=a[first],b[first]
   item["first_mismatch_timestamp"]=x.get("timestamp") if isinstance(x,dict) else None
   item["replay_timestamp"]=y.get("timestamp") if isinstance(y,dict) else None
   if isinstance(x,dict) and isinstance(y,dict):
    item["changed_fields"]={k:{"published":x.get(k),"replay":y.get(k)} for k in sorted(set(x)|set(y)) if x.get(k)!=y.get(k)}
   mismatch.append((field,first))
  r["fields"][field]=item
 if not mismatch:r["decision"]="APPEND_ONLY_PREFIX_MATCH"
 elif all(i>=0 and i==len(old.get(f,[]))-1 and r["fields"][f].get("first_mismatch_timestamp")==old.get("latest_data_timestamp") and r["fields"][f].get("replay_timestamp")==old.get("latest_data_timestamp") for f,i in mismatch):
  r["decision"]="HOLD_LAST_PUBLISHED_HOUR_MUTATED"
 else:r["decision"]="HOLD_EARLIER_PUBLISHED_HISTORY_MUTATED"
 return r
def audit_zip(path):
 with zipfile.ZipFile(path) as z:
  rows=[compare(json.loads(z.read("reports/published_baseline/"+name)),json.loads(z.read("reports/"+name)),name) for name in LEDGERS]
 return {"phase":"195-T","scope":"PAPER_FORENSICS_ONLY","ledgers":rows,"counts":{d:sum(x["decision"]==d for x in rows) for d in sorted(set(x["decision"] for x in rows))},"publication_authorized":False,"history_rewrite_authorized":False,"economic_trials":0,"holdout_accessed":False,"promotion_authorized":False}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--artifact",required=True);a=p.parse_args()
 print(json.dumps(audit_zip(a.artifact),sort_keys=True,separators=(",",":")))
