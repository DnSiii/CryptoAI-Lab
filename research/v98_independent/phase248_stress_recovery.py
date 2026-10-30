#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"research"/"v98_independent"))
import phase244_growth_core as P

RET_H=168
RV_H=24
REF_H=720
Q=.80
BREADTH=3
SLEEVE_PER_ASSET=-.125
CORE_PER_ASSET=.25
SYSTEM_CAP=1.0
DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def targets(data):
    c=data.close.loc[:,P.ASSETS]
    ret7=c/c.shift(RET_H)-1
    lr=np.log(c/c.shift(1))
    market_lr=lr.mean(axis=1)
    rv24=np.sqrt(market_lr.pow(2).rolling(RV_H,min_periods=RV_H).sum())
    ref=rv24.shift(1).rolling(REF_H,min_periods=REF_H).quantile(Q)

    core=pd.DataFrame(0.,index=c.index,columns=P.ASSETS)
    sleeve=pd.DataFrame(0.,index=c.index,columns=P.ASSETS)
    stress=False

    for i,t in enumerate(c.index):
        if t<START_DECISION:
            continue
        core.iloc[i]=CORE_PER_ASSET
        if t.hour==DECISION_HOUR:
            breadth=int((ret7.iloc[i]<0).fillna(False).sum())
            vol_ok=bool(np.isfinite(rv24.iloc[i]) and np.isfinite(ref.iloc[i]) and rv24.iloc[i]>ref.iloc[i])
            stress=(breadth>=BREADTH and vol_ok)
        if stress:
            sleeve.iloc[i]=SLEEVE_PER_ASSET

    combo=core+sleeve
    if float(combo.abs().sum(axis=1).max())>SYSTEM_CAP+1e-12:
        raise RuntimeError("system gross invariant")
    if float(combo.min().min())<-.0000001:
        raise RuntimeError("Phase248 must never become net short")
    return core,sleeve,combo

def run(data,t,tier,cap):
    cost,debit,credit=P.TIERS[tier]
    return P.exact_fast(
        data,t,
        cost_per_side=cost,
        gross_guard_cap=cap,
        funding_debit_multiplier=debit,
        funding_credit_multiplier=credit,
    )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase248_stress_recovery_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if sm.get("holdout_accessed") is not False or sm.get("alpha_or_pnl_computed") is not False:
        raise RuntimeError("source firewall")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    core,sleeve,combo=targets(data)
    cr={z:run(data,core,z,1.0) for z in P.TIERS}
    sr={z:run(data,combo,z,SYSTEM_CAP) for z in P.TIERS}

    core_m={z:P.metric(cr[z],P.START,P.CUT) for z in P.TIERS}
    sys_m={z:P.metric(sr[z],P.START,P.CUT) for z in P.TIERS}
    cf={y:P.metric(cr["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    sf={y:P.metric(sr["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:sf[y]["return"]-cf[y]["return"] for y in P.FOLDS}
    dg=P.diag(sr["base"],data,combo)

    pb=core_m["base"]; b=sys_m["base"]
    failures=[]
    if b["return"]<=pb["return"]:
        failures.append("base_return_not_above_core")
    if b["cagr"]<=pb["cagr"]:
        failures.append("base_cagr_not_above_core")
    if b["max_drawdown"]<pb["max_drawdown"]+.05:
        failures.append("dd_improvement<5pp")
    if b["profit_factor_daily"]<pb["profit_factor_daily"]:
        failures.append("base_pf_below_core")
    if b["worst_day"]<=pb["worst_day"]:
        failures.append("worst_day_not_improved")
    if sum(v>0 for v in marginal.values())<2:
        failures.append("marginal_positive_in_fewer_than_2_folds")
    if min(marginal.values())<=-.05:
        failures.append("fold_underperformance>5pp")
    if sys_m["severe"]["return"]<=core_m["severe"]["return"]:
        failures.append("severe_not_above_core")
    if sys_m["supersevere"]["return"]<=core_m["supersevere"]["return"]:
        failures.append("supersevere_not_above_core")
    if any(x["ruin"] for x in sys_m.values()):
        failures.append("ruin")
    if dg["max_open_gross"]>1.000000001:
        failures.append("open_gross>1")
    if dg["max_asset_contribution_share"]>.70:
        failures.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45:
        failures.append("top10_day_concentration>45%")

    decision="STRESS_RECOVERY_SLEEVE_CANDIDATE" if not failures else "REJECT_STRESS_RECOVERY_NO_RESCUE"
    mask=(sleeve.index>=P.START)&(sleeve.index<P.CUT)
    active=sleeve.loc[mask].abs().sum(axis=1)>0

    out={
        "engine":"V98 Independent","phase":248,
        "architecture":["growth_core_structural_beta","volatility_confirmed_stress_recovery_sleeve"],
        "training_only":True,"validation":None,"holdout_accessed":False,
        "v14_used":False,"v15_used":False,"v99_used":False,
        "parameters":{
            "assets":list(P.ASSETS),
            "downside_return_hours":RET_H,
            "rv_hours":RV_H,
            "reference_hours":REF_H,
            "reference_quantile":Q,
            "breadth_required":BREADTH,
            "sleeve_per_asset":SLEEVE_PER_ASSET,
            "core_per_asset":CORE_PER_ASSET,
            "system_gross_cap":SYSTEM_CAP,
            "decision_hour_utc":DECISION_HOUR,
        },
        "cost_funding_tiers":P.TIERS,
        "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),
        "combined_targets_sha256":hashlib.sha256(combo.to_csv(float_format="%.12g").encode()).hexdigest(),
        "core":core_m,"combined":sys_m,
        "core_folds":cf,"combined_folds":sf,
        "marginal_return_by_fold":marginal,
        "stress_activity":{
            "active_hour_ratio":float(active.mean()),
            "active_hours":int(active.sum()),
            "active_days_equivalent":float(active.sum()/24),
        },
        "diagnostics":dg,
        "gate":{"decision":decision,"passed":not failures,"failures":failures},
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "decision":decision,"failures":failures,
        "core":core_m,"combined":sys_m,
        "marginal_return_by_fold":marginal,
        "stress_activity":out["stress_activity"],
        "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")},
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
