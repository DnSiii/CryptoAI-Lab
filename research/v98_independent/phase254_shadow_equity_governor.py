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

PEAK_H=2160
BLOCK_DD=-.20
DECISION_HOUR=23
SYSTEM_CAP=1.25

def governor_mask(shadow_equity: pd.Series)->pd.Series:
    peak=shadow_equity.rolling(PEAK_H,min_periods=PEAK_H).max()
    dd=shadow_equity/peak-1
    blocked=False
    out=pd.Series(False,index=shadow_equity.index,dtype=bool)
    for i,t in enumerate(shadow_equity.index):
        if t.hour==DECISION_HOUR and pd.notna(dd.iloc[i]):
            blocked=bool(dd.iloc[i]<=BLOCK_DD)
        out.iloc[i]=blocked
    return out

def governed_targets(core,sleeve,shadow_equity):
    blocked=governor_mask(shadow_equity)
    governed=core+sleeve.where(~blocked,0.0)
    active=governed.index>=P.START
    if float(governed.loc[active].abs().sum(axis=1).max())>SYSTEM_CAP+1e-12:
        raise RuntimeError("governed gross invariant")
    if float(governed.loc[active].sum(axis=1).min())<1.0-1e-12:
        raise RuntimeError("core gross was reduced")
    return governed,blocked

def run(data,t,tier):
    return O.run(data,t,tier,SYSTEM_CAP)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase254_shadow_equity_governor_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if sm.get("holdout_accessed") is not False or sm.get("alpha_or_pnl_computed") is not False:
        raise RuntimeError("source firewall")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT or data.funding.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    core,sleeve,baseline,_=O.targets(data)
    shadow=O.run(data,baseline,"base",SYSTEM_CAP)
    governed,blocked=governed_targets(core,sleeve,shadow.equity)

    br={z:run(data,baseline,z) for z in P.TIERS}
    gr={z:run(data,governed,z) for z in P.TIERS}
    bm={z:P.metric(br[z],P.START,P.CUT) for z in P.TIERS}
    gm={z:P.metric(gr[z],P.START,P.CUT) for z in P.TIERS}
    bf={y:P.metric(br["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    gf={y:P.metric(gr["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:gf[y]["return"]-bf[y]["return"] for y in P.FOLDS}
    dg=P.diag(gr["base"],data,governed)

    train=(blocked.index>=P.START)&(blocked.index<P.CUT)
    blocked_train=blocked.loc[train]
    base_gross=baseline.loc[train].abs().sum(axis=1)
    gov_gross=governed.loc[train].abs().sum(axis=1)
    sleeve_suppressed=(base_gross-gov_gross)>.01

    b=gm["base"];bb=bm["base"]
    failures=[]
    if b["return"]<bb["return"]: failures.append("base_return_below_phase252")
    if b["cagr"]<bb["cagr"]: failures.append("base_cagr_below_phase252")
    if b["profit_factor_daily"]<bb["profit_factor_daily"]: failures.append("base_pf_below_phase252")
    if b["max_drawdown"]>bb["max_drawdown"]-.03: failures.append("dd_improvement<3pp")
    if b["worst_day"]<bb["worst_day"]: failures.append("worst_day_worse")
    if sum(v>=0 for v in marginal.values())<2: failures.append("marginal_nonnegative_in_fewer_than_2_folds")
    if min(marginal.values())<-.05: failures.append("fold_underperformance>5pp")
    if gm["severe"]["return"]<bm["severe"]["return"]: failures.append("severe_return_below_phase252")
    if gm["supersevere"]["return"]<bm["supersevere"]["return"]: failures.append("supersevere_return_below_phase252")
    if any(x["ruin"] for x in gm.values()): failures.append("ruin")
    if dg["max_open_gross"]>1.250000001: failures.append("open_gross>1.25")
    if float(gov_gross.min())<1.0-1e-12: failures.append("core_gross_below_1")
    if dg["max_asset_contribution_share"]>.70: failures.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45: failures.append("top10_day_concentration>45%")

    decision="SHADOW_EQUITY_RISK_GOVERNOR_CANDIDATE" if not failures else "REJECT_SHADOW_EQUITY_GOVERNOR_NO_RESCUE"
    out={
      "engine":"V98 Independent","phase":254,
      "architecture":["growth_core_structural_beta","carry_subsidized_opportunity_sleeve","shadow_equity_opportunity_risk_governor"],
      "training_only":True,"validation":None,"holdout_accessed":False,
      "v14_used":False,"v15_used":False,"v99_used":False,
      "parameters":{"peak_hours":PEAK_H,"block_drawdown":BLOCK_DD,"decision_hour_utc":DECISION_HOUR,
                    "governed_component":"Phase252 opportunity sleeve only","core_floor_gross":1.0,
                    "system_gross_cap":SYSTEM_CAP,"shadow_tier":"canonical BASE"},
      "cost_funding_tiers":P.TIERS,
      "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),
      "baseline_targets_sha256":hashlib.sha256(baseline.to_csv(float_format="%.12g").encode()).hexdigest(),
      "governed_targets_sha256":hashlib.sha256(governed.to_csv(float_format="%.12g").encode()).hexdigest(),
      "governor_mask_sha256":hashlib.sha256(blocked.astype(int).to_csv().encode()).hexdigest(),
      "phase252_baseline":bm,"governed":gm,
      "phase252_folds":bf,"governed_folds":gf,
      "marginal_return_by_fold":marginal,
      "governor_activity":{"blocked_hour_ratio":float(blocked_train.mean()),"blocked_hours":int(blocked_train.sum()),
                           "suppressed_opportunity_hour_ratio":float(sleeve_suppressed.mean()),"suppressed_opportunity_hours":int(sleeve_suppressed.sum())},
      "diagnostics":dg,
      "gate":{"decision":decision,"passed":not failures,"failures":failures},
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"decision":decision,"failures":failures,"phase252":bm,"governed":gm,
                      "marginal_return_by_fold":marginal,"governor_activity":out["governor_activity"],
                      "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")}},
                     indent=2,sort_keys=True))

if __name__=="__main__":
    main()
