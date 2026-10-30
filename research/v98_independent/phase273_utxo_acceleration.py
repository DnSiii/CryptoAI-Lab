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

SLEEVE_PER_ASSET=.0625
SYSTEM_CAP=1.50
DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def file_sha(path:Path): return hashlib.sha256(path.read_bytes()).hexdigest()

def acceleration_signal(csv_path:Path):
    d=pd.read_csv(csv_path)
    if list(d.columns)!=["date","utxo_count","source_points"]:
        raise RuntimeError("Phase272 normalized schema mismatch")
    d["date"]=pd.to_datetime(d["date"],utc=True,errors="raise").dt.normalize()
    d["utxo_count"]=pd.to_numeric(d["utxo_count"],errors="raise")
    if d["date"].duplicated().any() or (d["utxo_count"]<=0).any():
        raise RuntimeError("Phase272 normalized invariant")
    idx=pd.date_range("2023-01-01","2025-12-31",freq="D",tz="UTC")
    s=d.set_index("date")["utxo_count"].reindex(idx)
    recent=s.shift(1)/s.shift(31)-1
    prior=s.shift(31)/s.shift(61)-1
    exact=s.shift(1).notna()&s.shift(31).notna()&s.shift(61).notna()
    on=exact&(recent>0)&(recent>prior)
    return on,recent,prior,s

def integrated_targets(data,csv_path:Path):
    _,_,baseline,_=O.targets(data)
    on,_,_,_=acceleration_signal(csv_path)
    sleeve=pd.DataFrame(0.,index=baseline.index,columns=P.ASSETS)
    active=False;active_decisions=0
    for i,t in enumerate(baseline.index):
        if t<START_DECISION: continue
        if t.hour==DECISION_HOUR:
            active=bool(on.get(t.normalize(),False))
            if active and t>=P.START: active_decisions+=1
        if active: sleeve.iloc[i]=SLEEVE_PER_ASSET
    combo=baseline+sleeve
    train=(combo.index>=P.START)&(combo.index<P.CUT)
    if float(combo.loc[train].abs().sum(axis=1).max())>SYSTEM_CAP+1e-12:
        raise RuntimeError("system gross invariant")
    return baseline,sleeve,combo,on,active_decisions

def run(data,t,tier,cap):
    cost,debit,credit=P.TIERS[tier]
    return P.exact_fast(data,t,cost_per_side=cost,gross_guard_cap=cap,
                        funding_debit_multiplier=debit,funding_credit_multiplier=credit)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--utxo-manifest",type=Path,default=Path("research/v98_independent/phase272_utxo_manifest.json"))
    ap.add_argument("--utxo-csv",type=Path,default=Path("research/v98_independent/data/phase272_utxo/utxo_daily.csv"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase273_utxo_acceleration_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text()); um=json.loads(a.utxo_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if um.get("decision")!="PASS_DATA_ONLY" or um.get("phase")!=272:
        raise RuntimeError("Phase272 PASS_DATA_ONLY required")
    if um.get("holdout_accessed") is not False or um.get("pnl_executed") is not False:
        raise RuntimeError("Phase272 firewall")
    if file_sha(a.utxo_csv)!=um.get("normalized_csv_sha256"):
        raise RuntimeError("Phase272 CSV SHA mismatch")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT or data.funding.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    baseline,sleeve,combo,on,active_decisions=integrated_targets(data,a.utxo_csv)
    br={z:run(data,baseline,z,1.25) for z in P.TIERS}
    ir={z:run(data,combo,z,SYSTEM_CAP) for z in P.TIERS}
    base_m={z:P.metric(br[z],P.START,P.CUT) for z in P.TIERS}
    int_m={z:P.metric(ir[z],P.START,P.CUT) for z in P.TIERS}
    base_f={y:P.metric(br["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    int_f={y:P.metric(ir["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:int_f[y]["return"]-base_f[y]["return"] for y in P.FOLDS}
    dg=P.diag(ir["base"],data,combo)

    mask=(sleeve.index>=P.START)&(sleeve.index<P.CUT)
    active=sleeve.loc[mask].abs().sum(axis=1)>0
    b=int_m["base"];bb=base_m["base"];fail=[]
    if b["return"]<=bb["return"]*1.03: fail.append("base_marginal_return<3pct_relative")
    if b["cagr"]<=bb["cagr"]: fail.append("base_cagr_not_above_phase252")
    if b["profit_factor_daily"]<bb["profit_factor_daily"]: fail.append("base_pf_below_phase252")
    if b["max_drawdown"]<bb["max_drawdown"]-.05: fail.append("dd_worse_by_more_than_5pp")
    if b["worst_day"]<-.20: fail.append("worst_day<-20%")
    if sum(v>0 for v in marginal.values())<2: fail.append("marginal_positive_in_fewer_than_2_folds")
    if min(marginal.values())<=-.10: fail.append("fold_underperformance>10pp")
    if int_m["severe"]["return"]<=base_m["severe"]["return"]: fail.append("severe_not_above_phase252")
    if int_m["supersevere"]["return"]<=base_m["supersevere"]["return"]: fail.append("supersevere_not_above_phase252")
    if active_decisions<60: fail.append("fewer_than_60_active_decision_days")
    if any(x["ruin"] for x in int_m.values()): fail.append("ruin")
    if dg["max_open_gross"]>1.500000001: fail.append("open_gross>1.5")
    if dg["max_asset_contribution_share"]>.70: fail.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45: fail.append("top10_day_concentration>45%")

    decision="UTXO_ACCELERATION_OPPORTUNITY_CANDIDATE" if not fail else "REJECT_UTXO_ACCELERATION_NO_RESCUE"
    out={"engine":"V98 Independent","phase":273,
      "architecture":["growth_core_structural_beta","carry_subsidized_opportunity_sleeve","utxo_acceleration_opportunity_sleeve"],
      "training_only":True,"validation":None,"holdout_accessed":False,"v14_used":False,"v15_used":False,"v99_used":False,
      "parameters":{"recent_growth":"UTXO(D-1)/UTXO(D-31)-1","prior_growth":"UTXO(D-31)/UTXO(D-61)-1",
                    "activation":"recent_growth>0 and recent_growth>prior_growth; exact dates only; no imputation",
                    "sleeve_per_asset":SLEEVE_PER_ASSET,"system_gross_cap":SYSTEM_CAP,"decision_hour_utc":DECISION_HOUR},
      "cost_funding_tiers":P.TIERS,
      "phase272_manifest_sha256":file_sha(a.utxo_manifest),"phase272_csv_sha256":file_sha(a.utxo_csv),
      "baseline_targets_sha256":hashlib.sha256(baseline.to_csv(float_format="%.12g").encode()).hexdigest(),
      "sleeve_targets_sha256":hashlib.sha256(sleeve.to_csv(float_format="%.12g").encode()).hexdigest(),
      "integrated_targets_sha256":hashlib.sha256(combo.to_csv(float_format="%.12g").encode()).hexdigest(),
      "phase252_baseline":base_m,"integrated":int_m,"phase252_folds":base_f,"integrated_folds":int_f,
      "marginal_return_by_fold":marginal,
      "utxo_activity":{"active_decision_days":int(active_decisions),"active_hour_ratio":float(active.mean()),
                       "active_hours":int(active.sum()),"daily_on_ratio":float(on.mean())},
      "diagnostics":dg,"gate":{"decision":decision,"passed":not fail,"failures":fail}}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"decision":decision,"failures":fail,"phase252":base_m,"integrated":int_m,
      "marginal_return_by_fold":marginal,"utxo_activity":out["utxo_activity"],
      "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")}},indent=2,sort_keys=True))

if __name__=="__main__":main()
