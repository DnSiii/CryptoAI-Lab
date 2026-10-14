#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"research"/"v98_independent"))
import phase244_growth_core as P

VOL_H=720
MAX_W=.40
DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def capped_inverse_vol(v: pd.Series)->pd.Series:
    if v.isna().any() or (v<=0).any():
        raise ValueError("invalid realized volatility")
    raw=1.0/v.astype(float)
    active=list(raw.index)
    out=pd.Series(0.0,index=raw.index,dtype=float)
    remaining=1.0
    while active:
        scores=raw.loc[active]
        provisional=scores/scores.sum()*remaining
        offenders=[a for a in active if provisional[a]>MAX_W+1e-15]
        if not offenders:
            out.loc[active]=provisional
            break
        for a in offenders:
            out[a]=MAX_W
            active.remove(a)
            remaining-=MAX_W
        if remaining<-1e-12:
            raise RuntimeError("allocator cap infeasible")
    if abs(float(out.sum())-1.0)>1e-10:
        raise RuntimeError("allocator weights do not sum to one")
    if float(out.max())>MAX_W+1e-12 or float(out.min())<0:
        raise RuntimeError("allocator bound failure")
    return out

def targets(data):
    c=data.close.loc[:,P.ASSETS]
    lr=np.log(c/c.shift(1))
    rv=np.sqrt(lr.pow(2).rolling(VOL_H,min_periods=VOL_H).sum())
    alloc=pd.DataFrame(0.,index=c.index,columns=P.ASSETS)
    current=None
    for i,t in enumerate(c.index):
        if t<START_DECISION:
            continue
        if t.hour==DECISION_HOUR:
            row=rv.iloc[i]
            if row.notna().all() and (row>0).all():
                current=capped_inverse_vol(row)
        if current is not None:
            alloc.iloc[i]=current.to_numpy()
    if float(alloc.abs().sum(axis=1).max())>1.000000001:
        raise RuntimeError("gross invariant")
    if float(alloc.max().max())>MAX_W+1e-12 or float(alloc.min().min())<-1e-12:
        raise RuntimeError("asset-weight invariant")
    return alloc

def core_targets(index):
    t=pd.DataFrame(0.,index=index,columns=P.ASSETS)
    t.loc[t.index>=START_DECISION,:]=P.W
    return t

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase249_inverse_vol_allocator_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if sm.get("holdout_accessed") is not False or sm.get("alpha_or_pnl_computed") is not False:
        raise RuntimeError("source firewall")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    alloc=targets(data)
    core=core_targets(data.close.index)
    ar={z:P.run(data,alloc,z) for z in P.TIERS}
    cr={z:P.run(data,core,z) for z in P.TIERS}

    am={z:P.metric(ar[z],P.START,P.CUT) for z in P.TIERS}
    cm={z:P.metric(cr[z],P.START,P.CUT) for z in P.TIERS}
    af={y:P.metric(ar["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    cf={y:P.metric(cr["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:af[y]["return"]-cf[y]["return"] for y in P.FOLDS}
    dg=P.diag(ar["base"],data,alloc)
    mask=(alloc.index>=P.START)&(alloc.index<P.CUT)
    max_target_weight=float(alloc.loc[mask,P.ASSETS].max().max())

    b=am["base"]; cb=cm["base"]
    failures=[]
    if b["return"]<=cb["return"]*1.03:
        failures.append("base_marginal_return<3pct_relative")
    if b["cagr"]<=cb["cagr"]:
        failures.append("base_cagr_not_above_core")
    if b["max_drawdown"]<cb["max_drawdown"]-.02:
        failures.append("dd_worse_by_more_than_2pp")
    if b["profit_factor_daily"]<cb["profit_factor_daily"]:
        failures.append("base_pf_below_core")
    if sum(v>0 for v in marginal.values())<2:
        failures.append("marginal_positive_in_fewer_than_2_folds")
    if min(marginal.values())<=-.05:
        failures.append("fold_underperformance>5pp")
    if am["severe"]["return"]<=cm["severe"]["return"]:
        failures.append("severe_not_above_core")
    if am["supersevere"]["return"]<=cm["supersevere"]["return"]:
        failures.append("supersevere_not_above_core")
    if any(x["ruin"] for x in am.values()):
        failures.append("ruin")
    if dg["max_open_gross"]>1.000000001:
        failures.append("open_gross>1")
    if max_target_weight>MAX_W+1e-9:
        failures.append("target_weight>40%")
    if dg["max_asset_contribution_share"]>.70:
        failures.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45:
        failures.append("top10_day_concentration>45%")

    decision="DYNAMIC_ALLOCATOR_CANDIDATE" if not failures else "REJECT_DYNAMIC_ALLOCATOR_NO_RESCUE"
    out={
        "engine":"V98 Independent","phase":249,
        "architecture":["growth_core_structural_beta","inverse_vol_dynamic_allocator"],
        "training_only":True,"validation":None,"holdout_accessed":False,
        "v14_used":False,"v15_used":False,"v99_used":False,
        "parameters":{
            "assets":list(P.ASSETS),"volatility_hours":VOL_H,
            "max_asset_weight":MAX_W,"gross_target":1.0,
            "decision_hour_utc":DECISION_HOUR,
            "score":"inverse realized volatility",
        },
        "cost_funding_tiers":P.TIERS,
        "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),
        "allocator_targets_sha256":hashlib.sha256(alloc.to_csv(float_format="%.12g").encode()).hexdigest(),
        "core":cm,"allocated":am,
        "core_folds":cf,"allocated_folds":af,
        "marginal_return_by_fold":marginal,
        "allocator_diagnostics":{
            "max_target_asset_weight":max_target_weight,
            "mean_target_weights":{x:float(alloc.loc[mask,x].mean()) for x in P.ASSETS},
        },
        "diagnostics":dg,
        "gate":{"decision":decision,"passed":not failures,"failures":failures},
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "decision":decision,"failures":failures,
        "core":cm,"allocated":am,
        "marginal_return_by_fold":marginal,
        "allocator_diagnostics":out["allocator_diagnostics"],
        "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")},
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
