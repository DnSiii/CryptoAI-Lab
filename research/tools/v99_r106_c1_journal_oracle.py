"""Independent hourly C1 accounting oracle: raw train opens -> journal net/equity.
No signal optimization, future-value parsing, order submission or new trials.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from research.tools import v99_r106_c1_core as core
FIELDS=("time","regime","btc_weight","eth_weight","turnover","fee","net","equity","peak","lock_remaining")
def near(label,a,b):
    if not math.isfinite(a) or not math.isfinite(b) or abs(a-b)>1e-9*max(1,abs(a),abs(b)):
        raise ValueError("journal_accounting_discrepancy:"+label)
def verify(b,e,path,cost):
    if cost not in (core.SEVERE,core.SUPERSEVERE):
        raise ValueError("unfrozen_cost")
    if len(b)!=len(e) or any(x[0]!=y[0] for x,y in zip(b,e)):
        raise ValueError("source_pair_mismatch")
    indices=[i for i in range(721,len(b)-1) if b[i][0]>=core.START]
    if not indices or b[-1][0]>=core.END:
        raise ValueError("train_scope_violation")
    with open(path,newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=list(FIELDS):raise ValueError("journal_schema_mismatch")
        rows=list(reader)
    if len(rows)!=len(indices):raise ValueError("journal_hourly_coverage_mismatch")
    equity=peak=1.;previous=(0.,0.);fees=0.
    for index,(i,row) in enumerate(zip(indices,rows)):
        expected=b[i][0].isoformat()
        if row["time"]!=expected:
            raise ValueError("journal_wrong_time_or_duplicate:"+str(index))
        try:
            wb=float(row["btc_weight"]);we=float(row["eth_weight"])
            turn=float(row["turnover"]);fee=float(row["fee"])
            recorded_net=float(row["net"]);recorded_eq=float(row["equity"])
            recorded_peak=float(row["peak"]);lock=int(row["lock_remaining"])
        except (TypeError,ValueError) as exc:
            raise ValueError("non_numeric_journal") from exc
        if any(not math.isfinite(x) for x in (wb,we,turn,fee,recorded_net,recorded_eq,recorded_peak)):
            raise ValueError("nonfinite_journal")
        if abs(wb)>0.65+1e-9 or abs(we)>0.65+1e-9 or abs(wb)+abs(we)>1.3+1e-9:
            raise ValueError("journal_gross_limit_exceeded")
        if lock<0 or lock>167:
            raise ValueError("invalid_governor_lock")
        expected_turn=abs(wb-previous[0])+abs(we-previous[1])
        expected_fee=cost*expected_turn
        gross=wb*(b[i+1][1]/b[i][1]-1)+we*(e[i+1][1]/e[i][1]-1)
        expected_net=gross-expected_fee
        near("turnover",turn,expected_turn)
        near("fee",fee,expected_fee)
        near("net",recorded_net,expected_net)
        equity*=1+expected_net
        peak=max(equity,peak)
        near("equity",recorded_eq,equity)
        near("peak",recorded_peak,peak)
        if equity<=0:raise ValueError("liquidated_simulated_capital")
        fees+=expected_fee;previous=(wb,we)
    return {"rows":len(rows),"cost_per_side":cost,"independent_net_roi":equity-1,
        "verified_modeled_fee_sum":fees,
        "journal_sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "exchange_fee_and_funding_authenticated":False,
        "holdout_accessed":False,"promotion_authorized":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--btc",type=Path,default=Path("data/canonical/BTCUSDT_1h.csv"))
    p.add_argument("--eth",type=Path,default=Path("data/canonical/ETHUSDT_1h.csv"))
    p.add_argument("--report",type=Path,default=Path("reports/candidate_v99_r106_c1_integrated_train.json"))
    p.add_argument("--prefix",type=Path,default=Path("research_evidence/v99_r106_c1"))
    p.add_argument("--out",type=Path,default=Path("research_evidence/v99_r106_c1_oracle.json"))
    a=p.parse_args()
    b,_=core.load_train(a.btc);e,_=core.load_train(a.eth)
    core.assert_train_coverage(b);core.assert_train_coverage(e)
    report=json.loads(a.report.read_text())
    if (report.get("status")!="TRAIN_REJECT_NO_RETUNE"
        or report.get("promotion_authorized") is not False
        or report.get("holdout_market_values_parsed") is not False
        or report.get("economic_trials")!=1):
        raise ValueError("historical_c1_decision_unexpected")
    results={}
    for kind,cost in (("severe",core.SEVERE),("supersevere",core.SUPERSEVERE)):
        witness=verify(b,e,Path(str(a.prefix)+"_"+kind+".csv"),cost)
        near("reported_roi_"+kind,witness["independent_net_roi"],report[kind]["roi"])
        near("reported_fees_"+kind,witness["verified_modeled_fee_sum"],report[kind]["modeled_transaction_cost_sum"])
        if witness["journal_sha256"]!=report[kind]["simulated_journal_sha256"]:
            raise ValueError("journal_SHA256_inconsistent")
        results[kind]=witness
    result={"schema":"V99_R106_C1_INDEPENDENT_JOURNAL_ORACLE_V1",
      "status":"C1_REJECT_CONFIRMED_ACCOUNTING_CORRECT_NO_PROMOTION",
      "evidence":results,"holdout_accessed":False,"real_orders_enabled":False,
      "native_funding_verified":False,"promotion_authorized":False}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"rows_each":results["severe"]["rows"],
      "severe_roi":results["severe"]["independent_net_roi"],
      "supersevere_roi":results["supersevere"]["independent_net_roi"],
      "promotion_authorized":False}))
if __name__=="__main__":main()
