#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"research"/"v98_independent"))
import phase244_growth_core as P
import phase252_carry_subsidized_opportunity as O

RV_H=24
REF_H=720
STRESS_MULT=2.0
MEMORY_H=72
SLEEVE_PER_ASSET=.0625
SYSTEM_CAP=1.50
DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def recovery_state(data):
    close=data.close.loc[:,P.ASSETS]
    lr=np.log(close).diff()
    market_lr=lr.mean(axis=1)
    rv24=market_lr.rolling(RV_H,min_periods=RV_H).std()
    normal=rv24.shift(1).rolling(REF_H,min_periods=REF_H).median()
    ret24=market_lr.rolling(RV_H,min_periods=RV_H).sum()
    stress=((rv24>=STRESS_MULT*normal)&(ret24<0)).fillna(False)
    recent=stress.rolling(MEMORY_H,min_periods=1).max().fillna(0).astype(bool)
    recovery=(recent&(rv24<=normal)&(ret24>0)).fillna(False)
    return recovery,stress,rv24,normal,ret24

def integrated_targets(data):
    core,opp,baseline,_=O.targets(data)
    recovery,stress,rv24,normal,ret24=recovery_state(data)
    sleeve=pd.DataFrame(0.,index=baseline.index,columns=P.ASSETS)
    on=False
    decision_count=0
    for i,t in enumerate(baseline.index):
        if t<START_DECISION:
            continue
        if t.hour==DECISION_HOUR:
            on=bool(recovery.iloc[i])
            if on: decision_count+=1
        if on:
            sleeve.iloc[i]=SLEEVE_PER_ASSET
    combo=baseline+sleeve
    active=combo.index>=P.START
    if float(combo.loc[active].abs().sum(axis=1).max())>SYSTEM_CAP+1e-12:
        raise RuntimeError("system gross invariant")
    return baseline,sleeve,combo,recovery,stress,decision_count

def run(data,t,tier,cap):
    cost,debit,credit=P.TIERS[tier]
    return P.exact_fast(data,t,cost_per_side=cost,gross_guard_cap=cap,
                        funding_debit_multiplier=debit,funding_credit_multiplier=credit)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase256_vol_normalization_recovery_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if sm.get("holdout_accessed") is not False or sm.get("alpha_or_pnl_computed") is not False:
        raise RuntimeError("source firewall")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT or data.funding.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    baseline,sleeve,combo,recovery,stress,recovery_days=integrated_targets(data)
    br={z:run(data,baseline,z,1.25) for z in P.TIERS}
    ir={z:run(data,combo,z,SYSTEM_CAP) for z in P.TIERS}

    bm={z:P.metric(br[z],P.START,P.CUT) for z in P.TIERS}
    im={z:P.metric(ir[z],P.START,P.CUT) for z in P.TIERS}
    bf={y:P.metric(br["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    inf={y:P.metric(ir["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:inf[y]["return"]-bf[y]["return"] for y in P.FOLDS}
    dg=P.diag(ir["base"],data,combo)

    mask=(combo.index>=P.START)&(combo.index<P.CUT)
    active=sleeve.loc[mask].abs().sum(axis=1)>0
    stress_train=stress.loc[mask]
    recovery_train=recovery.loc[mask]

    b=im["base"];bb=bm["base"]
    failures=[]
    if b["return"]<=bb["return"]*1.03: failures.append("base_marginal_return<3pct_relative")
    if b["cagr"]<=bb["cagr"]: failures.append("base_cagr_not_above_phase252")
    if b["profit_factor_daily"]<bb["profit_factor_daily"]: failures.append("base_pf_below_phase252")
    if b["max_drawdown"]<bb["max_drawdown"]-.03: failures.append("dd_worse_by_more_than_3pp")
    if b["worst_day"]<-.20: failures.append("worst_day<-20%")
    if sum(v>0 for v in marginal.values())<2: failures.append("marginal_positive_in_fewer_than_2_folds")
    if min(marginal.values())<=-.05: failures.append("fold_underperformance>5pp")
    if im["severe"]["return"]<=bm["severe"]["return"]: failures.append("severe_not_above_phase252")
    if im["supersevere"]["return"]<=bm["supersevere"]["return"]: failures.append("supersevere_not_above_phase252")
    if recovery_days<10: failures.append("fewer_than_10_recovery_decision_days")
    if any(x["ruin"] for x in im.values()): failures.append("ruin")
    if dg["max_open_gross"]>1.500000001: failures.append("open_gross>1.5")
    if dg["max_asset_contribution_share"]>.70: failures.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45: failures.append("top10_day_concentration>45%")

    decision="VOL_NORMALIZATION_RECOVERY_CANDIDATE" if not failures else "REJECT_VOL_NORMALIZATION_RECOVERY_NO_RESCUE"
    out={
      "engine":"V98 Independent","phase":256,
      "architecture":["growth_core_structural_beta","carry_subsidized_opportunity_sleeve","volatility_normalization_recovery_sleeve"],
      "training_only":True,"validation":None,"holdout_accessed":False,
      "v14_used":False,"v15_used":False,"v99_used":False,
      "parameters":{"assets":list(P.ASSETS),"rv_hours":RV_H,"normal_reference_hours":REF_H,
                    "stress_multiple":STRESS_MULT,"recent_stress_memory_hours":MEMORY_H,
                    "recovery_rule":"recent stress AND rv24<=prior720h median rv24 AND market_ret24>0",
                    "sleeve_per_asset":SLEEVE_PER_ASSET,"system_gross_cap":SYSTEM_CAP,
                    "decision_hour_utc":DECISION_HOUR},
      "cost_funding_tiers":P.TIERS,
      "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),
      "baseline_targets_sha256":hashlib.sha256(baseline.to_csv(float_format="%.12g").encode()).hexdigest(),
      "sleeve_targets_sha256":hashlib.sha256(sleeve.to_csv(float_format="%.12g").encode()).hexdigest(),
      "integrated_targets_sha256":hashlib.sha256(combo.to_csv(float_format="%.12g").encode()).hexdigest(),
      "phase252_baseline":bm,"integrated":im,
      "phase252_folds":bf,"integrated_folds":inf,
      "marginal_return_by_fold":marginal,
      "recovery_activity":{"stress_hours":int(stress_train.sum()),"recovery_signal_hours":int(recovery_train.sum()),
                           "recovery_decision_days":int(recovery_days),"active_hour_ratio":float(active.mean()),
                           "active_hours":int(active.sum())},
      "diagnostics":dg,
      "gate":{"decision":decision,"passed":not failures,"failures":failures}
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"decision":decision,"failures":failures,"phase252":bm,"integrated":im,
      "marginal_return_by_fold":marginal,"recovery_activity":out["recovery_activity"],
      "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")}},indent=2,sort_keys=True))

if __name__=="__main__":main()
