"""C1 post-rejection loss/exposure forensics ONLY; cannot select/tune strategy."""
import argparse,csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path
from research.tools.v99_r106_c1_journal_oracle import FIELDS

def read(path):
    with open(path,newline="",encoding="utf-8") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames!=list(FIELDS):raise ValueError("forensic_journal_schema")
        rows=list(rd)
    if not rows:raise ValueError("empty_journal")
    times=[r["time"] for r in rows]
    if len(times)!=len(set(times)) or sorted(times)!=times:
        raise ValueError("journal_time_order_or_duplicate")
    return rows

def forensic(severe,supersevere):
    if len(severe)!=len(supersevere) or [x["time"] for x in severe]!=[x["time"] for x in supersevere]:
        raise ValueError("scenarios_not_same_train_hours")
    diffs=0;locks={"severe":0,"supersevere":0};active={"severe":0,"supersevere":0}
    block={}
    for name,rows in (("severe",severe),("supersevere",supersevere)):
        daily=defaultdict(lambda:{"gross":0.,"fee":0.,"net":0.,"hours":0})
        regimes=defaultdict(lambda:{"gross":0.,"fee":0.,"net":0.,"hours":0})
        for r in rows:
            try:
                net=float(r["net"]);fee=float(r["fee"]);wb=float(r["btc_weight"]);we=float(r["eth_weight"])
                lock=int(r["lock_remaining"])
            except (ValueError,TypeError) as exc:raise ValueError("malformed_forensic_record") from exc
            if not all(math.isfinite(x) for x in (net,fee,wb,we)) or fee<0 or lock<0 or lock>167:
                raise ValueError("invalid_forensic_economic_record")
            date=r["time"][:10]
            gross=net+fee
            for target in (daily[date],regimes[r["regime"]]):
                target["gross"]+=gross;target["fee"]+=fee;target["net"]+=net;target["hours"]+=1
            locks[name]+=int(lock>0);active[name]+=int(abs(wb)+abs(we)>0)
        worst=sorted(daily.items(),key=lambda x:x[1]["net"])[:5]
        block[name]={"active_hours":active[name],"cash_lock_hours":locks[name],
          "gross_pnl_sum_pre_funding":sum(r["gross"] for r in daily.values()),
          "modeled_fees_sum":sum(r["fee"] for r in daily.values()),
          "net_simple_sum":sum(r["net"] for r in daily.values()),
          "worst_5_utc_days_by_simple_net":[{"date":d,**v} for d,v in worst],
          "regime_simple_contributions":dict(sorted(regimes.items())),
          "distinct_trade_days":sum(any(float(r["btc_weight"]) or float(r["eth_weight"])
              for r in rows if r["time"].startswith(day)) for day in daily)}
    for a,b in zip(severe,supersevere):
        wa=(float(a["btc_weight"]),float(a["eth_weight"]))
        wb=(float(b["btc_weight"]),float(b["eth_weight"]))
        if any(abs(x-y)>1e-12 for x,y in zip(wa,wb)):diffs+=1
    return {"schema":"V99_R106_C1_READONLY_POST_REJECTION_FORENSICS_V1",
      "status":"C1_REJECT_MAINTAINED_NO_RETUNE","aligned_hours_per_scenario":len(severe),
      "scenario_different_exposure_hours":diffs,
      "scenarios":block,
      "sum_of_hourly_returns_is_not_compounded_return":True,
      "does_not_identify_profitable_candidate":True,
      "new_economic_trials":0,"holdout_accessed":False,"validation_accessed":False,
      "promotion_authorized":False,"paper_publication_authorized":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,default=Path("reports/candidate_v99_r106_c1_integrated_train.json"))
    p.add_argument("--prefix",type=Path,default=Path("research_evidence/v99_r106_c1"))
    p.add_argument("--output",type=Path,default=Path("research_evidence/v99_r106_c1_failure_forensics.json"))
    a=p.parse_args()
    report=json.loads(a.report.read_text())
    if report.get("status")!="TRAIN_REJECT_NO_RETUNE" or report.get("promotion_authorized") is not False:
        raise ValueError("forensics_only_on_rejected_frozen_C1")
    rows=[]
    for name in ("severe","supersevere"):
        path=Path(str(a.prefix)+"_"+name+".csv")
        if hashlib.sha256(path.read_bytes()).hexdigest()!=report[name]["simulated_journal_sha256"]:
            raise ValueError("forensic_journal_hash_changed")
        rows.append(read(path))
    result=forensic(*rows)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"hours":result["aligned_hours_per_scenario"],
      "different_exposure_hours":result["scenario_different_exposure_hours"],
      "severe_lock_hours":result["scenarios"]["severe"]["cash_lock_hours"],
      "supersevere_lock_hours":result["scenarios"]["supersevere"]["cash_lock_hours"],
      "holdout_accessed":False,"promotion_authorized":False},sort_keys=True))
if __name__=="__main__":main()
