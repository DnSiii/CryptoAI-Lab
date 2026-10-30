#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np,pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"research"/"v98_independent"))
import phase244_growth_core as P
import phase252_carry_subsidized_opportunity as O

EDGE_H=720
EXTRA_PER_ASSET=.0625
SYSTEM_CAP=1.50
DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def shadow_edge(data,core,baseline):
    core_shadow=O.run(data,core,"base",1.0)
    p252_shadow=O.run(data,baseline,"base",1.25)
    ratio=(p252_shadow.equity/core_shadow.equity).replace([np.inf,-np.inf],np.nan)
    edge=np.log(ratio/ratio.shift(EDGE_H))
    return edge,core_shadow,p252_shadow

def allocated_targets(data):
    core,sleeve,baseline,_=O.targets(data)
    edge,core_shadow,p252_shadow=shadow_edge(data,core,baseline)
    boost=pd.DataFrame(0.,index=baseline.index,columns=P.ASSETS)
    on=False;boost_decisions=0
    for i,t in enumerate(baseline.index):
        if t<START_DECISION: continue
        if t.hour==DECISION_HOUR:
            opp_on=bool(sleeve.iloc[i].abs().sum()>1e-12)
            e=edge.iloc[i]
            on=bool(opp_on and pd.notna(e) and e>0)
            if on and t>=P.START: boost_decisions+=1
        if on:
            boost.iloc[i]=EXTRA_PER_ASSET
    integrated=baseline+boost
    train=(integrated.index>=P.START)&(integrated.index<P.CUT)
    if float(integrated.loc[train].abs().sum(axis=1).max())>SYSTEM_CAP+1e-12:
        raise RuntimeError("system gross invariant")
    if (integrated.loc[train]-baseline.loc[train] < -1e-12).any().any():
        raise RuntimeError("allocator reduced frozen Phase252")
    return core,sleeve,baseline,boost,integrated,edge,boost_decisions

def run(data,t,tier,cap):
    cost,debit,credit=P.TIERS[tier]
    return P.exact_fast(data,t,cost_per_side=cost,gross_guard_cap=cap,
                        funding_debit_multiplier=debit,funding_credit_multiplier=credit)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase274_edge_persistence_allocator_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if sm.get("holdout_accessed") is not False or sm.get("alpha_or_pnl_computed") is not False:
        raise RuntimeError("source firewall")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT or data.funding.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    core,sleeve,baseline,boost,integrated,edge,boost_decisions=allocated_targets(data)
    br={z:run(data,baseline,z,1.25) for z in P.TIERS}
    ir={z:run(data,integrated,z,SYSTEM_CAP) for z in P.TIERS}
    base_m={z:P.metric(br[z],P.START,P.CUT) for z in P.TIERS}
    int_m={z:P.metric(ir[z],P.START,P.CUT) for z in P.TIERS}
    base_f={y:P.metric(br["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    int_f={y:P.metric(ir["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:int_f[y]["return"]-base_f[y]["return"] for y in P.FOLDS}
    dg=P.diag(ir["base"],data,integrated)

    mask=(integrated.index>=P.START)&(integrated.index<P.CUT)
    boost_active=boost.loc[mask].abs().sum(axis=1)>0
    edge_train=edge.loc[mask]
    b=int_m["base"];bb=base_m["base"];fail=[]
    if b["return"]<=bb["return"]*1.05: fail.append("base_marginal_return<5pct_relative")
    if b["cagr"]<=bb["cagr"]: fail.append("base_cagr_not_above_phase252")
    if b["profit_factor_daily"]<bb["profit_factor_daily"]: fail.append("base_pf_below_phase252")
    if b["max_drawdown"]<bb["max_drawdown"]-.05: fail.append("dd_worse_by_more_than_5pp")
    if b["worst_day"]<-.20: fail.append("worst_day<-20%")
    if sum(v>0 for v in marginal.values())<2: fail.append("marginal_positive_in_fewer_than_2_folds")
    if min(marginal.values())<=-.10: fail.append("fold_underperformance>10pp")
    if int_m["severe"]["return"]<=base_m["severe"]["return"]: fail.append("severe_not_above_phase252")
    if int_m["supersevere"]["return"]<=base_m["supersevere"]["return"]: fail.append("supersevere_not_above_phase252")
    if boost_decisions<50: fail.append("fewer_than_50_boost_decision_days")
    if any(x["ruin"] for x in int_m.values()): fail.append("ruin")
    if dg["max_open_gross"]>1.500000001: fail.append("open_gross>1.5")
    if dg["max_asset_contribution_share"]>.70: fail.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45: fail.append("top10_day_concentration>45%")

    decision="EDGE_PERSISTENCE_ALLOCATOR_CANDIDATE" if not fail else "REJECT_EDGE_PERSISTENCE_ALLOCATOR_NO_RESCUE"
    out={"engine":"V98 Independent","phase":274,
      "architecture":["growth_core_structural_beta","carry_subsidized_opportunity_sleeve","edge_persistence_dynamic_allocator"],
      "training_only":True,"validation":None,"holdout_accessed":False,
      "v14_used":False,"v15_used":False,"v99_used":False,
      "parameters":{"edge_hours":EDGE_H,
                    "edge":"log((Phase252_shadow/core_shadow)_t / (Phase252_shadow/core_shadow)_(t-720h))",
                    "activation":"original Phase252 opportunity ON and edge30>0",
                    "extra_per_asset":EXTRA_PER_ASSET,"system_gross_cap":SYSTEM_CAP,
                    "decision_hour_utc":DECISION_HOUR,"shadow_tier":"BASE"},
      "cost_funding_tiers":P.TIERS,
      "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),
      "baseline_targets_sha256":hashlib.sha256(baseline.to_csv(float_format="%.12g").encode()).hexdigest(),
      "boost_targets_sha256":hashlib.sha256(boost.to_csv(float_format="%.12g").encode()).hexdigest(),
      "integrated_targets_sha256":hashlib.sha256(integrated.to_csv(float_format="%.12g").encode()).hexdigest(),
      "edge_series_sha256":hashlib.sha256(edge.to_csv(float_format="%.12g").encode()).hexdigest(),
      "phase252_baseline":base_m,"integrated":int_m,"phase252_folds":base_f,"integrated_folds":int_f,
      "marginal_return_by_fold":marginal,
      "allocator_activity":{"boost_decision_days":int(boost_decisions),"boost_active_hour_ratio":float(boost_active.mean()),
                            "boost_active_hours":int(boost_active.sum()),
                            "edge_positive_hour_ratio":float((edge_train>0).mean())},
      "diagnostics":dg,"gate":{"decision":decision,"passed":not fail,"failures":fail}}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"decision":decision,"failures":fail,"phase252":base_m,"integrated":int_m,
      "marginal_return_by_fold":marginal,"allocator_activity":out["allocator_activity"],
      "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")}},indent=2,sort_keys=True))

if __name__=="__main__":main()
