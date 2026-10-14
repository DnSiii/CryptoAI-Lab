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
CHEAP_W=.30
EXPENSIVE_W=.20
DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def targets(data):
    fd=data.funding.loc[:,P.ASSETS]
    trail=fd.rolling(WINDOW_H,min_periods=WINDOW_H).sum()
    out=pd.DataFrame(0.,index=fd.index,columns=P.ASSETS)
    current=None
    order={a:i for i,a in enumerate(P.ASSETS)}

    for i,t in enumerate(fd.index):
        if t<START_DECISION:
            continue
        if t.hour==DECISION_HOUR:
            row=trail.iloc[i]
            if row.notna().all():
                ranked=sorted(P.ASSETS,key=lambda a:(float(row[a]),order[a]))
                w={a:EXPENSIVE_W for a in P.ASSETS}
                for a in ranked[:2]:
                    w[a]=CHEAP_W
                current=pd.Series(w,index=P.ASSETS,dtype=float)
        if current is not None:
            out.iloc[i]=current.to_numpy()

    active=out.abs().sum(axis=1)>0
    if active.any():
        if float((out.loc[active].sum(axis=1)-1).abs().max())>1e-12:
            raise RuntimeError("allocator gross invariant")
        vals=set(round(float(x),10) for x in out.loc[active].to_numpy().ravel())
        if not vals.issubset({CHEAP_W,EXPENSIVE_W}):
            raise RuntimeError("allocator weight invariant")
    return out

def core_targets(index):
    t=pd.DataFrame(0.,index=index,columns=P.ASSETS)
    t.loc[t.index>=START_DECISION,:]=P.W
    return t

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase250_funding_efficiency_allocator_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if sm.get("holdout_accessed") is not False or sm.get("alpha_or_pnl_computed") is not False:
        raise RuntimeError("source firewall")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT or data.funding.index.max()>=P.CUT:
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
    active=alloc.loc[mask].abs().sum(axis=1)>0
    weights=alloc.loc[mask & active,P.ASSETS]

    b=am["base"]; cb=cm["base"]
    failures=[]
    if b["return"]<=cb["return"]*1.03:
        failures.append("base_marginal_return<3pct_relative")
    if b["cagr"]<=cb["cagr"]:
        failures.append("base_cagr_not_above_core")
    if b["profit_factor_daily"]<cb["profit_factor_daily"]:
        failures.append("base_pf_below_core")
    if b["max_drawdown"]<cb["max_drawdown"]-.02:
        failures.append("dd_worse_by_more_than_2pp")
    if b["funding_net_cost"]>=cb["funding_net_cost"]:
        failures.append("funding_drag_not_reduced")
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
    if len(weights):
        vals=set(round(float(x),10) for x in weights.to_numpy().ravel())
        if not vals.issubset({CHEAP_W,EXPENSIVE_W}):
            failures.append("target_weight_set_violation")
        if float((weights.sum(axis=1)-1).abs().max())>1e-10:
            failures.append("target_sum_not_one")
    if dg["max_asset_contribution_share"]>.70:
        failures.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45:
        failures.append("top10_day_concentration>45%")

    decision="FUNDING_EFFICIENCY_ALLOCATOR_CANDIDATE" if not failures else "REJECT_FUNDING_EFFICIENCY_ALLOCATOR_NO_RESCUE"
    out={
        "engine":"V98 Independent","phase":250,
        "architecture":["growth_core_structural_beta","funding_efficiency_dynamic_allocator"],
        "training_only":True,"validation":None,"holdout_accessed":False,
        "v14_used":False,"v15_used":False,"v99_used":False,
        "parameters":{
            "assets":list(P.ASSETS),
            "funding_window_hours":WINDOW_H,
            "cheap_pair_weight":CHEAP_W,
            "expensive_pair_weight":EXPENSIVE_W,
            "gross_target":1.0,
            "decision_hour_utc":DECISION_HOUR,
            "ranking":"ascending trailing realized funding sum; stable symbol-order tie break",
        },
        "cost_funding_tiers":P.TIERS,
        "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),
        "allocator_targets_sha256":hashlib.sha256(alloc.to_csv(float_format="%.12g").encode()).hexdigest(),
        "core":cm,"allocated":am,
        "core_folds":cf,"allocated_folds":af,
        "marginal_return_by_fold":marginal,
        "allocator_diagnostics":{
            "active_hour_ratio":float(active.mean()),
            "mean_target_weights":{x:float(weights[x].mean()) if len(weights) else 0.0 for x in P.ASSETS},
            "base_funding_drag_reduction":float(cb["funding_net_cost"]-b["funding_net_cost"]),
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
