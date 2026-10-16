"""C1 frozen integrated system TRAIN-only economic decision, no final holdout."""
import argparse,json
from pathlib import Path
from research.tools import v99_r106_c1_core as c
from research.tools import v99_r106_c1_accounting as a
SPEC=Path("research/V99_R106_C1_TRAIN_ISOLATION_NOTE_20261016.md")
def gates(s,v):
    return {
      "positive_severe":s["roi"]>0,
      "positive_supersevere":v["roi"]>0,
      "at_least_4_5_positive_severe_folds":s["positive_folds"]>=4,
      "at_least_3_5_positive_supersevere_folds":v["positive_folds"]>=3,
      "both_hourly_profit_factors_above_one":(s["hourly_profit_factor"] or 0)>1 and (v["hourly_profit_factor"] or 0)>1,
      "both_remove_best_day_positive":s["remove_best_day_roi"]>0 and v["remove_best_day_roi"]>0,
      "supersevere_drawdown_within_35pct":v["max_drawdown"]>=-.35,
      "at_least_720_active_hours":s["active_hours"]>=720,
      "beats_train_btc_passive":s["roi"]>s["benchmark_proxies"]["btc_100pct"],
      "beats_train_equal_weight_passive":s["roi"]>s["benchmark_proxies"]["btc_eth_equal"],
      "exactly_five_folds":len(s["fold_returns"])==len(v["fold_returns"])==5,
      "six_regimes_reported":len(s["regime_matrix"])==len(v["regime_matrix"])==6}
def run(btc,eth,out,journal_root):
    if not SPEC.is_file() or not SPEC.read_text().strip():raise ValueError("precommitment_missing")
    b,bsha=c.load_train(btc);e,esha=c.load_train(eth)
    c.assert_train_coverage(b);c.assert_train_coverage(e)
    if len(b)!=len(e) or any(x[0]!=y[0] for x,y in zip(b,e)):raise ValueError("unaligned_historical_pair")
    s=a.simulate(b,e,c.SEVERE,Path(str(journal_root)+"_severe.csv"))
    v=a.simulate(b,e,c.SUPERSEVERE,Path(str(journal_root)+"_supersevere.csv"))
    g=gates(s,v);ok=all(g.values())
    report={"study":"V99 R106 C1 complete integrated system frozen TRAIN gate",
      "status":"TRAIN_PASS_PENDING_INDEPENDENT_VALIDATION" if ok else "TRAIN_REJECT_NO_RETUNE",
      "preregistered_spec":str(SPEC),"gates":g,"passed_all_train_gates":ok,
      "btc_train_sha256":bsha,"eth_train_sha256":esha,
      "train_start":c.START.isoformat(),"train_end_exclusive":c.END.isoformat(),
      "sealed_validation_start":c.END.isoformat(),"final_holdout_start":c.FINAL_HOLDOUT.isoformat(),
      "severe":s,"supersevere":v,"economic_trials":1,
      "final_holdout_accessed":False,"validation_market_values_parsed":False,
      "holdout_market_values_parsed":False,"funding_settlements_authenticated":False,
      "native_fee_tier_authenticated":False,"real_fills_authenticated":False,
      "preliminary_pre_funding":True,"promotion_authorized":False,
      "paper_publication_authorized":False,"real_orders_enabled":False,
      "v16_frozen_changed":False,"v99_frozen_changed":False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--btc",type=Path,default=Path("data/canonical/BTCUSDT_1h.csv"))
    p.add_argument("--eth",type=Path,default=Path("data/canonical/ETHUSDT_1h.csv"))
    p.add_argument("--out",type=Path,default=Path("reports/candidate_v99_r106_c1_integrated_train.json"))
    p.add_argument("--journal",type=Path,default=Path("research_evidence/v99_r106_c1"))
    x=p.parse_args();r=run(x.btc,x.eth,x.out,x.journal)
    print(json.dumps({"status":r["status"],"severe_roi":r["severe"]["roi"],
      "supersevere_roi":r["supersevere"]["roi"],"severe_positive_folds":r["severe"]["positive_folds"],
      "supersevere_positive_folds":r["supersevere"]["positive_folds"],
      "supersevere_max_drawdown":r["supersevere"]["max_drawdown"],
      "failed_gates":[k for k,v in r["gates"].items() if not v],
      "holdout_accessed":False,"promotion_authorized":False},sort_keys=True))
if __name__=="__main__":main()
