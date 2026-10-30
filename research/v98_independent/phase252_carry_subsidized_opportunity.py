#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"research"/"v98_independent"))
import phase244_growth_core as P

WINDOW_H=168
SLEEVE_PER_ASSET=.0625
CORE_PER_ASSET=.25
SYSTEM_CAP=1.25
DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def targets(data):
    fd=data.funding.loc[:,P.ASSETS]
    trail=fd.rolling(WINDOW_H,min_periods=WINDOW_H).sum()
    mean_trail=trail.mean(axis=1)
    core=pd.DataFrame(0.,index=fd.index,columns=P.ASSETS)
    sleeve=pd.DataFrame(0.,index=fd.index,columns=P.ASSETS)
    on=False
    for i,t in enumerate(fd.index):
        if t<START_DECISION:
            continue
        core.iloc[i]=CORE_PER_ASSET
        if t.hour==DECISION_HOUR and pd.notna(mean_trail.iloc[i]):
            on=bool(mean_trail.iloc[i]<=0)
        if on:
            sleeve.iloc[i]=SLEEVE_PER_ASSET
    combo=core+sleeve
    if float(combo.abs().sum(axis=1).max())>SYSTEM_CAP+1e-12:
        raise RuntimeError("system gross invariant")
    return core,sleeve,combo,mean_trail

def run(data,t,tier,cap):
    cost,debit,credit=P.TIERS[tier]
    return P.exact_fast(data,t,cost_per_side=cost,gross_guard_cap=cap,
                        funding_debit_multiplier=debit,funding_credit_multiplier=credit)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase252_carry_subsidized_opportunity_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if sm.get("holdout_accessed") is not False or sm.get("alpha_or_pnl_computed") is not False:
        raise RuntimeError("source firewall")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT or data.funding.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    core,sleeve,combo,mean_trail=targets(data)
    cr={z:run(data,core,z,1.0) for z in P.TIERS}
    sr={z:run(data,combo,z,SYSTEM_CAP) for z in P.TIERS}

    cm={z:P.metric(cr[z],P.START,P.CUT) for z in P.TIERS}
    smet={z:P.metric(sr[z],P.START,P.CUT) for z in P.TIERS}
    cf={y:P.metric(cr["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    sf={y:P.metric(sr["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:sf[y]["return"]-cf[y]["return"] for y in P.FOLDS}
    dg=P.diag(sr["base"],data,combo)

    mask=(sleeve.index>=P.START)&(sleeve.index<P.CUT)
    active=sleeve.loc[mask].abs().sum(axis=1)>0
    funding_signal=mean_trail.loc[mask]

    b=smet["base"]; cb=cm["base"]
    failures=[]
    if b["return"]<=cb["return"]*1.05:
        failures.append("base_marginal_return<5pct_relative")
    if b["cagr"]<=cb["cagr"]:
        failures.append("base_cagr_not_above_core")
    if b["profit_factor_daily"]<cb["profit_factor_daily"]:
        failures.append("base_pf_below_core")
    if b["max_drawdown"]<cb["max_drawdown"]-.05:
        failures.append("dd_worse_by_more_than_5pp")
    if b["worst_day"]<-.20:
        failures.append("worst_day<-20%")
    if sum(v>0 for v in marginal.values())<2:
        failures.append("marginal_positive_in_fewer_than_2_folds")
    if min(marginal.values())<=-.10:
        failures.append("fold_underperformance>10pp")
    if smet["severe"]["return"]<=cm["severe"]["return"]:
        failures.append("severe_not_above_core")
    if smet["supersevere"]["return"]<=cm["supersevere"]["return"]:
        failures.append("supersevere_not_above_core")
    if any(x["ruin"] for x in smet.values()):
        failures.append("ruin")
    if dg["max_open_gross"]>1.250000001:
        failures.append("open_gross>1.25")
    if dg["max_asset_contribution_share"]>.70:
        failures.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45:
        failures.append("top10_day_concentration>45%")

    decision="CARRY_SUBSIDIZED_OPPORTUNITY_CANDIDATE" if not failures else "REJECT_CARRY_SUBSIDIZED_OPPORTUNITY_NO_RESCUE"
    out={
        "engine":"V98 Independent","phase":252,
        "architecture":["growth_core_structural_beta","carry_subsidized_opportunity_sleeve"],
        "training_only":True,"validation":None,"holdout_accessed":False,
        "v14_used":False,"v15_used":False,"v99_used":False,
        "parameters":{
            "assets":list(P.ASSETS),
            "funding_window_hours":WINDOW_H,
            "activation":"cross_asset_mean_trailing_funding_sum <= 0",
            "sleeve_per_asset":SLEEVE_PER_ASSET,
            "core_per_asset":CORE_PER_ASSET,
            "system_gross_cap":SYSTEM_CAP,
            "decision_hour_utc":DECISION_HOUR,
        },
        "cost_funding_tiers":P.TIERS,
        "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),
        "combined_targets_sha256":hashlib.sha256(combo.to_csv(float_format="%.12g").encode()).hexdigest(),
        "core":cm,"combined":smet,
        "core_folds":cf,"combined_folds":sf,
        "marginal_return_by_fold":marginal,
        "opportunity_activity":{
            "active_hour_ratio":float(active.mean()),
            "active_hours":int(active.sum()),
            "active_days_equivalent":float(active.sum()/24),
            "signal_nonpositive_ratio":float((funding_signal<=0).mean()),
        },
        "diagnostics":dg,
        "gate":{"decision":decision,"passed":not failures,"failures":failures},
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "decision":decision,"failures":failures,
        "core":cm,"combined":smet,
        "marginal_return_by_fold":marginal,
        "opportunity_activity":out["opportunity_activity"],
        "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")},
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
