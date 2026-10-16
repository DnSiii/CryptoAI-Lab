"""Read-only status census; no PnL, market data or holdout access."""
import argparse,json,re
from collections import Counter
from pathlib import Path
PAT=re.compile(r"candidate_v99_r106_phase\d+(?:_[a-z0-9]+)*_train_alpha\.json\Z")
def scan(root):
    rows=[]
    for p in sorted(root.glob("candidate_v99_r106_phase*_train_alpha.json")):
        if not PAT.fullmatch(p.name):raise ValueError("invalid_candidate_name")
        j=json.loads(p.read_text())
        if not isinstance(j,dict) or not isinstance(j.get("status"),str):raise ValueError("invalid_train_status")
        if j.get("holdout_market_values_parsed") is True or j.get("holdout_rows_used_for_selection") is True:raise ValueError("contaminated_train_record")
        rows.append((p.name,j["status"]))
    if not rows:raise ValueError("no_train_records")
    return {"status":"RECORDED_TRAIN_STATUS_ONLY","count":len(rows),
      "recorded_status_counts":dict(sorted(Counter(s for _,s in rows).items())),
      "not_rejected_not_promoted":[{"file":n,"recorded_status":s} for n,s in rows if "REJECT" not in s.upper()],
      "pnl_inspected":False,"holdout_accessed":False,"promotion_authorized":False,"paper_publication_authorized":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("reports"))
    p.add_argument("--out",type=Path,default=Path("research_evidence/train_inventory.json"))
    a=p.parse_args();j=scan(a.root);a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(j,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"count":j["count"],"status_counts":j["recorded_status_counts"],
      "not_rejected":len(j["not_rejected_not_promoted"])}))
if __name__=="__main__":main()
