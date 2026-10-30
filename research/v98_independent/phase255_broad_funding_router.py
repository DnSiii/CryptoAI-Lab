#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"research"/"v98_independent"))
import phase244_growth_core as P
import phase252_carry_subsidized_opportunity as O

WINDOW_H=168
BREADTH_REQUIRED=3
SLEEVE_PER_ASSET=.0625
CORE_PER_ASSET=.25
SYSTEM_CAP=1.25
DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def routed_targets(data):
    fd=data.funding.loc[:,P.ASSETS]
    trail=fd.rolling(WINDOW_H,min_periods=WINDOW_H).sum()
    core=pd.DataFrame(0.,index=fd.index,columns=P.ASSETS)
    sleeve=pd.DataFrame(0.,index=fd.index,columns=P.ASSETS)
    on=False
    for i,t in enumerate(fd.index):
        if t<START_DECISION:
            continue
        core.iloc[i]=CORE_PER_ASSET
        if t.hour==DECISION_HOUR:
            row=trail.iloc[i]
            if row.notna().all():
                mean_ok=bool(float(row.mean())<=0)
                breadth=int((row<=0).sum())
                on=bool(mean_ok and breadth>=BREADTH_REQUIRED)
        if on:
            sleeve.iloc[i]=SLEEVE_PER_ASSET
    combo=core+sleeve
    if float(combo.abs().sum(axis=1).max())>SYSTEM_CAP+1e-12:
        raise RuntimeError("system gross invariant")
    return core,sleeve,combo

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase255_broad_funding_router_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if sm.get("holdout_accessed") is not False or sm.get("alpha_or_pnl_computed") is not False:
        raise RuntimeError("source firewall")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT or data.funding.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    _,base_sleeve,baseline,_=O.targets(data)
    _,routed_sleeve,routed=routed_targets(data)
    br={z:O.run(data,baseline,z,SYSTEM_CAP) for z in P.TIERS}
    rr={z:O.run(data,routed,z,SYSTEM_CAP) for z in P.TIERS}

    bm={z:P.metric(br[z],P.START,P.CUT) for z in P.TIERS}
    rm={z:P.metric(rr[z],P.START,P.CUT) for z in P.TIERS}
    bf={y:P.metric(br["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    rf={y:P.metric(rr["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:rf[y]["return"]-bf[y]["return"] for y in P.FOLDS}
    dg=P.diag(rr["base"],data,routed)

    mask=(routed.index>=P.START)&(routed.index<P.CUT)
    base_active=base_sleeve.loc[mask].abs().sum(axis=1)>0
    routed_active=routed_sleeve.loc[mask].abs().sum(axis=1)>0

    b=rm["base"];bb=bm["base"]
    failures=[]
    if b["return"]<=bb["return"]: failures.append("base_return_not_above_phase252")
    if b["cagr"]<=bb["cagr"]: failures.append("base_cagr_not_above_phase252")
    if b["profit_factor_daily"]<bb["profit_factor_daily"]: failures.append("base_pf_below_phase252")
    if b["max_drawdown"]<bb["max_drawdown"]+.02: failures.append("dd_improvement<2pp")
    if b["worst_day"]<bb["worst_day"]: failures.append("worst_day_worse_than_phase252")
    if sum(v>0 for v in marginal.values())<2: failures.append("marginal_positive_in_fewer_than_2_folds")
    if min(marginal.values())<=-.05: failures.append("fold_underperformance>5pp")
    if rm["severe"]["return"]<=bm["severe"]["return"]: failures.append("severe_not_above_phase252")
    if rm["supersevere"]["return"]<=bm["supersevere"]["return"]: failures.append("supersevere_not_above_phase252")
    if any(x["ruin"] for x in rm.values()): failures.append("ruin")
    if dg["max_open_gross"]>1.250000001: failures.append("open_gross>1.25")
    if float(routed_active.mean())>=float(base_active.mean()): failures.append("router_did_not_filter_activity")
    if dg["max_asset_contribution_share"]>.70: failures.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45: failures.append("top10_day_concentration>45%")

    decision="BROAD_FUNDING_ROUTER_CANDIDATE" if not failures else "REJECT_BROAD_FUNDING_ROUTER_NO_RESCUE"
    out={
      "engine":"V98 Independent","phase":255,
      "architecture":["growth_core_structural_beta","carry_subsidized_opportunity_sleeve","broad_funding_regime_router"],
      "training_only":True,"validation":None,"holdout_accessed":False,
      "v14_used":False,"v15_used":False,"v99_used":False,
      "parameters":{"assets":list(P.ASSETS),"funding_window_hours":WINDOW_H,
        "mean_condition":"cross_asset_mean_trailing_funding_sum <= 0",
        "breadth_condition":"at least 3 of 4 trailing funding sums <= 0",
        "breadth_required":BREADTH_REQUIRED,"sleeve_per_asset":SLEEVE_PER_ASSET,
        "core_per_asset":CORE_PER_ASSET,"system_gross_cap":SYSTEM_CAP,"decision_hour_utc":DECISION_HOUR},
      "cost_funding_tiers":P.TIERS,
      "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),
      "baseline_targets_sha256":hashlib.sha256(baseline.to_csv(float_format="%.12g").encode()).hexdigest(),
      "routed_targets_sha256":hashlib.sha256(routed.to_csv(float_format="%.12g").encode()).hexdigest(),
      "phase252_baseline":bm,"routed":rm,"phase252_folds":bf,"routed_folds":rf,
      "marginal_return_by_fold":marginal,
      "router_activity":{"phase252_active_hour_ratio":float(base_active.mean()),
        "routed_active_hour_ratio":float(routed_active.mean()),
        "filtered_hour_ratio":float(base_active.mean()-routed_active.mean()),
        "routed_active_hours":int(routed_active.sum())},
      "diagnostics":dg,
      "gate":{"decision":decision,"passed":not failures,"failures":failures}
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"decision":decision,"failures":failures,"phase252":bm,"routed":rm,
      "marginal_return_by_fold":marginal,"router_activity":out["router_activity"],
      "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")}},indent=2,sort_keys=True))

if __name__=="__main__":main()
