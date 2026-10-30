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
CORE_W=.25
ROUTER_COST=.0007
DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def candidate_weights(row: pd.Series)->pd.Series:
    order={a:i for i,a in enumerate(P.ASSETS)}
    ranked=sorted(P.ASSETS,key=lambda a:(float(row[a]),order[a]))
    w=pd.Series(EXPENSIVE_W,index=P.ASSETS,dtype=float)
    w.loc[ranked[:2]]=CHEAP_W
    return w

def targets(data):
    fd=data.funding.loc[:,P.ASSETS]
    trail=fd.rolling(WINDOW_H,min_periods=WINDOW_H).sum()
    core=pd.Series(CORE_W,index=P.ASSETS,dtype=float)
    out=pd.DataFrame(0.,index=fd.index,columns=P.ASSETS)
    current=core.copy()
    diagnostics=[]

    for i,t in enumerate(fd.index):
        if t<START_DECISION:
            continue
        if t.hour==DECISION_HOUR:
            row=trail.iloc[i]
            if row.notna().all():
                forecast=row/7.0
                cand=candidate_weights(row)
                core_cost=float((core*forecast).sum())
                cand_cost=float((cand*forecast).sum())
                savings=core_cost-cand_cost
                roundtrip_l1=float((current-cand).abs().sum()+(cand-core).abs().sum())
                threshold=roundtrip_l1*ROUTER_COST
                use_candidate=bool(savings>threshold)
                current=cand if use_candidate else core.copy()
                diagnostics.append({
                    "time":t.isoformat(),
                    "estimated_daily_savings":savings,
                    "roundtrip_l1":roundtrip_l1,
                    "break_even_cost":threshold,
                    "candidate_selected":use_candidate,
                })
        out.iloc[i]=current.to_numpy()

    active=out.loc[out.index>=START_DECISION]
    if float((active.sum(axis=1)-1).abs().max())>1e-12:
        raise RuntimeError("router gross invariant")
    allowed={.20,.25,.30}
    vals=set(round(float(x),10) for x in active.to_numpy().ravel())
    if not vals.issubset(allowed):
        raise RuntimeError("router target set invariant")
    return out,diagnostics

def core_targets(index):
    t=pd.DataFrame(0.,index=index,columns=P.ASSETS)
    t.loc[t.index>=START_DECISION,:]=CORE_W
    return t

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase251_funding_friction_router_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if sm.get("holdout_accessed") is not False or sm.get("alpha_or_pnl_computed") is not False:
        raise RuntimeError("source firewall")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT or data.funding.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    routed,route_diag=targets(data)
    core=core_targets(data.close.index)

    rr={z:P.run(data,routed,z) for z in P.TIERS}
    cr={z:P.run(data,core,z) for z in P.TIERS}

    rm={z:P.metric(rr[z],P.START,P.CUT) for z in P.TIERS}
    cm={z:P.metric(cr[z],P.START,P.CUT) for z in P.TIERS}
    rf={y:P.metric(rr["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    cf={y:P.metric(cr["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:rf[y]["return"]-cf[y]["return"] for y in P.FOLDS}
    dg=P.diag(rr["base"],data,routed)

    scored=[x for x in route_diag if P.START<=pd.Timestamp(x["time"])<P.CUT]
    selected=[x for x in scored if x["candidate_selected"]]
    mask=(routed.index>=P.START)&(routed.index<P.CUT)
    wt=routed.loc[mask,P.ASSETS]

    b=rm["base"]; cb=cm["base"]
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
    if rm["severe"]["return"]<=cm["severe"]["return"]:
        failures.append("severe_not_above_core")
    if rm["supersevere"]["return"]<=cm["supersevere"]["return"]:
        failures.append("supersevere_not_above_core")
    if any(x["ruin"] for x in rm.values()):
        failures.append("ruin")
    if dg["max_open_gross"]>1.000000001:
        failures.append("open_gross>1")
    if float((wt.sum(axis=1)-1).abs().max())>1e-10:
        failures.append("target_sum_not_one")
    for _,row in wt.iterrows():
        vals=sorted(round(float(x),10) for x in row)
        if vals not in ([.25,.25,.25,.25],[.20,.20,.30,.30]):
            failures.append("target_geometry_violation")
            break
    if dg["max_asset_contribution_share"]>.70:
        failures.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45:
        failures.append("top10_day_concentration>45%")

    decision="FUNDING_FRICTION_ROUTER_CANDIDATE" if not failures else "REJECT_FUNDING_FRICTION_ROUTER_NO_RESCUE"
    out={
        "engine":"V98 Independent","phase":251,
        "architecture":["growth_core_structural_beta","funding_friction_router","funding_efficiency_dynamic_allocator"],
        "training_only":True,"validation":None,"holdout_accessed":False,
        "v14_used":False,"v15_used":False,"v99_used":False,
        "parameters":{
            "assets":list(P.ASSETS),
            "funding_window_hours":WINDOW_H,
            "cheap_pair_weight":CHEAP_W,
            "expensive_pair_weight":EXPENSIVE_W,
            "core_weight":CORE_W,
            "router_base_cost_per_l1":ROUTER_COST,
            "decision_hour_utc":DECISION_HOUR,
            "rule":"select funding allocator only when estimated one-day funding savings exceed conservative round-trip BASE turnover cost",
        },
        "cost_funding_tiers":P.TIERS,
        "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),
        "router_targets_sha256":hashlib.sha256(routed.to_csv(float_format="%.12g").encode()).hexdigest(),
        "core":cm,"routed":rm,
        "core_folds":cf,"routed_folds":rf,
        "marginal_return_by_fold":marginal,
        "router_diagnostics":{
            "decision_count":len(scored),
            "allocator_selected_count":len(selected),
            "allocator_selected_ratio":float(len(selected)/len(scored)) if scored else 0.0,
            "mean_estimated_daily_savings_when_selected":float(sum(x["estimated_daily_savings"] for x in selected)/len(selected)) if selected else 0.0,
            "mean_break_even_cost_when_selected":float(sum(x["break_even_cost"] for x in selected)/len(selected)) if selected else 0.0,
            "base_funding_drag_reduction":float(cb["funding_net_cost"]-b["funding_net_cost"]),
        },
        "diagnostics":dg,
        "gate":{"decision":decision,"passed":not failures,"failures":sorted(set(failures))},
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "decision":decision,"failures":sorted(set(failures)),
        "core":cm,"routed":rm,
        "marginal_return_by_fold":marginal,
        "router_diagnostics":out["router_diagnostics"],
        "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")},
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
