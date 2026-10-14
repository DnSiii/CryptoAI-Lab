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

WINDOW=720
ENTRY_Z=2.0
EXIT_Z=.5
RV_GROSS=.50
SYSTEM_CAP=1.25
DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")
PAIRS=(
    ("BTCUSDT","ETHUSDT"),
    ("BTCUSDT","BNBUSDT"),
    ("BTCUSDT","SOLUSDT"),
    ("ETHUSDT","BNBUSDT"),
    ("ETHUSDT","SOLUSDT"),
    ("BNBUSDT","SOLUSDT"),
)

def rv_overlay(data):
    close=data.close.loc[:,P.ASSETS]
    ratios={}
    means={}
    stds={}
    for a,b in PAIRS:
        r=np.log(close[a]/close[b])
        ratios[(a,b)]=r
        means[(a,b)]=r.shift(1).rolling(WINDOW,min_periods=WINDOW).mean()
        stds[(a,b)]=r.shift(1).rolling(WINDOW,min_periods=WINDOW).std(ddof=0)

    states={pair:0 for pair in PAIRS}
    overlay=pd.DataFrame(0.,index=close.index,columns=P.ASSETS)
    active_pair_count=pd.Series(0,index=close.index,dtype=int)

    for i,t in enumerate(close.index):
        if t<START_DECISION:
            continue
        if t.hour==DECISION_HOUR:
            for pair in PAIRS:
                r=ratios[pair].iloc[i];m=means[pair].iloc[i];s=stds[pair].iloc[i]
                if not (np.isfinite(r) and np.isfinite(m) and np.isfinite(s) and s>0):
                    continue
                z=float((r-m)/s)
                st=states[pair]
                if st==0:
                    if z<=-ENTRY_Z: st=1
                    elif z>=ENTRY_Z: st=-1
                elif st>0:
                    if z>=ENTRY_Z: st=-1
                    elif z>=-EXIT_Z: st=0
                else:
                    if z<=-ENTRY_Z: st=1
                    elif z<=EXIT_Z: st=0
                states[pair]=st

        raw=pd.Series(0.,index=P.ASSETS,dtype=float)
        count=0
        for (a,b),st in states.items():
            if st:
                raw[a]+=float(st)
                raw[b]-=float(st)
                count+=1
        gross=float(raw.abs().sum())
        if gross>0:
            raw*=RV_GROSS/gross
        if abs(float(raw.sum()))>1e-12:
            raise RuntimeError("RV net exposure invariant")
        if float(raw.abs().sum())>RV_GROSS+1e-12:
            raise RuntimeError("RV gross invariant")
        overlay.iloc[i]=raw.to_numpy()
        active_pair_count.iloc[i]=count
    return overlay,active_pair_count

def integrated_targets(data):
    _,_,baseline,_=O.targets(data)
    rv,pair_count=rv_overlay(data)
    combo=baseline+rv
    active=combo.index>=START_DECISION
    if float(combo.loc[active].min().min())<-1e-12:
        raise RuntimeError("integrated target became short")
    base_gross=baseline.loc[active].abs().sum(axis=1)
    combo_gross=combo.loc[active].abs().sum(axis=1)
    if float((combo_gross-base_gross).abs().max())>1e-10:
        raise RuntimeError("RV overlay changed integrated gross")
    if float(combo_gross.max())>SYSTEM_CAP+1e-12:
        raise RuntimeError("system gross invariant")
    return baseline,rv,combo,pair_count

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase253_all_pairs_relative_value_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if sm.get("holdout_accessed") is not False or sm.get("alpha_or_pnl_computed") is not False:
        raise RuntimeError("source firewall")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    baseline,rv,combo,pair_count=integrated_targets(data)
    br={z:O.run(data,baseline,z,SYSTEM_CAP) for z in P.TIERS}
    ir={z:O.run(data,combo,z,SYSTEM_CAP) for z in P.TIERS}

    bm={z:P.metric(br[z],P.START,P.CUT) for z in P.TIERS}
    im={z:P.metric(ir[z],P.START,P.CUT) for z in P.TIERS}
    bf={y:P.metric(br["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    inf={y:P.metric(ir["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:inf[y]["return"]-bf[y]["return"] for y in P.FOLDS}
    dg=P.diag(ir["base"],data,combo)

    mask=(rv.index>=P.START)&(rv.index<P.CUT)
    rv_train=rv.loc[mask,P.ASSETS]
    rv_net=rv_train.sum(axis=1)
    rv_gross=rv_train.abs().sum(axis=1)
    pc=pair_count.loc[mask]

    b=im["base"];bb=bm["base"]
    failures=[]
    if b["return"]<=bb["return"]*1.03:
        failures.append("base_marginal_return<3pct_relative")
    if b["cagr"]<=bb["cagr"]:
        failures.append("base_cagr_not_above_phase252")
    if b["profit_factor_daily"]<bb["profit_factor_daily"]:
        failures.append("base_pf_below_phase252")
    if b["max_drawdown"]<bb["max_drawdown"]-.03:
        failures.append("dd_worse_by_more_than_3pp")
    if b["worst_day"]<-.20:
        failures.append("worst_day<-20%")
    if sum(v>0 for v in marginal.values())<2:
        failures.append("marginal_positive_in_fewer_than_2_folds")
    if min(marginal.values())<=-.05:
        failures.append("fold_underperformance>5pp")
    if im["severe"]["return"]<=bm["severe"]["return"]:
        failures.append("severe_not_above_phase252")
    if im["supersevere"]["return"]<=bm["supersevere"]["return"]:
        failures.append("supersevere_not_above_phase252")
    if any(x["ruin"] for x in im.values()):
        failures.append("ruin")
    if dg["max_open_gross"]>1.250000001:
        failures.append("open_gross>1.25")
    if float(rv_net.abs().max())>1e-12:
        failures.append("rv_net_exposure_nonzero")
    if float(rv_gross.max())>0.500000001:
        failures.append("rv_gross>0.50")
    if dg["max_asset_contribution_share"]>.70:
        failures.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45:
        failures.append("top10_day_concentration>45%")

    decision="RELATIVE_VALUE_SLEEVE_CANDIDATE" if not failures else "REJECT_RELATIVE_VALUE_NO_RESCUE"
    out={
        "engine":"V98 Independent","phase":253,
        "architecture":["growth_core_structural_beta","carry_subsidized_opportunity_sleeve","all_pairs_relative_value_mean_reversion"],
        "training_only":True,"validation":None,"holdout_accessed":False,
        "v14_used":False,"v15_used":False,"v99_used":False,
        "parameters":{
            "assets":list(P.ASSETS),"pairs":[list(x) for x in PAIRS],
            "reference_hours":WINDOW,"entry_z":ENTRY_Z,"exit_z":EXIT_Z,
            "rv_gross":RV_GROSS,"system_gross_cap":SYSTEM_CAP,"decision_hour_utc":DECISION_HOUR,
            "construction":"all six log-price-ratio state machines; aggregate net-zero overlay normalized to 0.50 gross"
        },
        "cost_funding_tiers":P.TIERS,
        "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),
        "baseline_targets_sha256":hashlib.sha256(baseline.to_csv(float_format="%.12g").encode()).hexdigest(),
        "rv_targets_sha256":hashlib.sha256(rv.to_csv(float_format="%.12g").encode()).hexdigest(),
        "integrated_targets_sha256":hashlib.sha256(combo.to_csv(float_format="%.12g").encode()).hexdigest(),
        "phase252_baseline":bm,"integrated":im,
        "phase252_folds":bf,"integrated_folds":inf,
        "marginal_return_by_fold":marginal,
        "rv_activity":{
            "active_hour_ratio":float((rv_gross>0).mean()),
            "mean_active_pair_count":float(pc.mean()),
            "max_active_pair_count":int(pc.max()),
            "max_overlay_gross":float(rv_gross.max()),
            "max_abs_overlay_net":float(rv_net.abs().max()),
        },
        "diagnostics":dg,
        "gate":{"decision":decision,"passed":not failures,"failures":failures},
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "decision":decision,"failures":failures,
        "phase252":bm,"integrated":im,
        "marginal_return_by_fold":marginal,
        "rv_activity":out["rv_activity"],
        "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")},
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
