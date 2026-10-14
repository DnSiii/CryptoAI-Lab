#!/usr/bin/env python3
"""V98 Phase263 — preregistered developer-acceleration relative-value sleeve.

Execution is refused unless Phase262 is PASS_DATA_ONLY. No parameter search.
"""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"research"/"v98_independent"))
import phase244_growth_core as P
import phase252_carry_subsidized_opportunity as O

RECENT_MONTHS=3
PRIOR_MONTHS=3
LONG_BUDGET=.125
SHORT_BUDGET=.125
OVERLAY_GROSS_CAP=.25
SYSTEM_CAP=1.25
DECISION_HOUR=23

def file_sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_monthly(csv_path:Path)->pd.DataFrame:
    d=pd.read_csv(csv_path)
    required=["asset","repo","branch","month","commit_count","first_commit","last_commit"]
    if list(d.columns)!=required:
        raise RuntimeError("Phase262 normalized schema mismatch")
    if set(d["asset"])!=set(P.ASSETS):
        raise RuntimeError("Phase262 asset universe mismatch")
    d["commit_count"]=pd.to_numeric(d["commit_count"],errors="raise").astype(int)
    if (d["commit_count"]<0).any():
        raise RuntimeError("negative commit count")
    if d.duplicated(["asset","month"]).any():
        raise RuntimeError("duplicate asset/month")
    counts=d.pivot(index="month",columns="asset",values="commit_count").sort_index()
    counts=counts.reindex(columns=P.ASSETS)
    if counts.isna().any().any():
        raise RuntimeError("incomplete monthly panel")
    return counts

def monthly_scores(counts:pd.DataFrame)->pd.DataFrame:
    # Score for decision month M uses only M-1..M-6 completed calendar months.
    idx=pd.PeriodIndex(counts.index,freq="M")
    c=counts.copy();c.index=idx
    decision_months=pd.period_range(idx.min()+6,idx.max()+1,freq="M")
    rows=[]
    for m in decision_months:
        hist=c.loc[:m-1]
        if len(hist)<6:
            continue
        recent=hist.iloc[-3:].mean()
        prior=hist.iloc[-6:-3].mean()
        score=np.log((recent+1.0)/(prior+1.0))
        row={"decision_month":str(m)}
        row.update({a:float(score[a]) for a in P.ASSETS})
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=P.ASSETS,dtype=float)
    out=pd.DataFrame(rows).set_index("decision_month")
    return out.reindex(columns=P.ASSETS)

def overlay_from_scores(scores:pd.DataFrame,index:pd.DatetimeIndex):
    overlay=pd.DataFrame(0.,index=index,columns=P.ASSETS)
    active_decisions=0
    current=pd.Series(0.,index=P.ASSETS,dtype=float)
    for i,t in enumerate(index):
        if t.hour==DECISION_HOUR and t.day==1:
            key=t.strftime("%Y-%m")
            if key not in scores.index:
                current[:]=0.
            else:
                s=scores.loc[key].astype(float)
                if not np.isfinite(s.to_numpy()).all():
                    raise RuntimeError("nonfinite developer score")
                hi=float(s.max());lo=float(s.min())
                current[:]=0.
                if not math.isclose(hi,lo,rel_tol=0,abs_tol=1e-15):
                    highs=s.index[np.isclose(s.to_numpy(),hi,rtol=0,atol=1e-15)]
                    lows=s.index[np.isclose(s.to_numpy(),lo,rtol=0,atol=1e-15)]
                    current.loc[highs]=LONG_BUDGET/len(highs)
                    current.loc[lows]=-SHORT_BUDGET/len(lows)
                    active_decisions+=1
            overlay.iloc[i]=current.to_numpy()
        elif i>0:
            overlay.iloc[i]=current.to_numpy()
    net=overlay.sum(axis=1)
    gross=overlay.abs().sum(axis=1)
    if float(net.abs().max())>1e-12:
        raise RuntimeError("overlay net invariant")
    if float(gross.max())>OVERLAY_GROSS_CAP+1e-12:
        raise RuntimeError("overlay gross invariant")
    return overlay,active_decisions

def integrated_targets(data,monthly_csv:Path):
    _,_,baseline,_=O.targets(data)
    counts=load_monthly(monthly_csv)
    scores=monthly_scores(counts)
    overlay,active_decisions=overlay_from_scores(scores,baseline.index)
    combo=baseline+overlay
    train=(combo.index>=P.START)&(combo.index<P.CUT)
    if float(combo.loc[train].min().min())<-1e-12:
        raise RuntimeError("integrated target became negative")
    bg=baseline.loc[train].abs().sum(axis=1)
    cg=combo.loc[train].abs().sum(axis=1)
    if float((cg-bg).abs().max())>1e-10:
        raise RuntimeError("RV overlay changed integrated gross")
    if float(cg.max())>SYSTEM_CAP+1e-12:
        raise RuntimeError("system gross invariant")
    return baseline,overlay,combo,scores,active_decisions

def run(data,t,tier):
    return O.run(data,t,tier,SYSTEM_CAP)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    ap.add_argument("--developer-manifest",type=Path,default=Path("research/v98_independent/phase262_developer_activity_manifest.json"))
    ap.add_argument("--developer-csv",type=Path,default=Path("research/v98_independent/data/phase262_developer_activity/monthly_commits.csv"))
    ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase263_developer_acceleration_rv_results.json"))
    a=ap.parse_args()

    sm=json.loads(a.source_manifest.read_text())
    dm=json.loads(a.developer_manifest.read_text())
    if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):
        raise RuntimeError("Clean-4 source required")
    if dm.get("phase")!=262 or dm.get("decision")!="PASS_DATA_ONLY":
        raise RuntimeError("Phase262 PASS_DATA_ONLY required")
    if dm.get("pnl_executed") is not False or dm.get("crypto_price_join") is not False or dm.get("holdout_accessed") is not False:
        raise RuntimeError("Phase262 firewall")
    if file_sha(a.developer_csv)!=dm.get("normalized_csv_sha256"):
        raise RuntimeError("Phase262 CSV SHA mismatch")

    data=P.load_data(a.price_root,a.funding_root)
    if data.close.index.max()>=P.CUT or data.funding.index.max()>=P.CUT:
        raise RuntimeError("2026+ firewall")

    baseline,overlay,combo,scores,active_decisions=integrated_targets(data,a.developer_csv)
    br={z:run(data,baseline,z) for z in P.TIERS}
    ir={z:run(data,combo,z) for z in P.TIERS}
    bm={z:P.metric(br[z],P.START,P.CUT) for z in P.TIERS}
    im={z:P.metric(ir[z],P.START,P.CUT) for z in P.TIERS}
    bf={y:P.metric(br["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    inf={y:P.metric(ir["base"],s,e) for y,(s,e) in P.FOLDS.items()}
    marginal={y:inf[y]["return"]-bf[y]["return"] for y in P.FOLDS}
    dg=P.diag(ir["base"],data,combo)

    mask=(overlay.index>=P.START)&(overlay.index<P.CUT)
    ot=overlay.loc[mask,P.ASSETS]
    net=ot.sum(axis=1);gross=ot.abs().sum(axis=1)
    b=im["base"];bb=bm["base"];fail=[]
    if b["return"]<=bb["return"]*1.03:fail.append("base_marginal_return<3pct_relative")
    if b["cagr"]<=bb["cagr"]:fail.append("base_cagr_not_above_phase252")
    if b["profit_factor_daily"]<bb["profit_factor_daily"]:fail.append("base_pf_below_phase252")
    if b["max_drawdown"]<bb["max_drawdown"]-.03:fail.append("dd_worse_by_more_than_3pp")
    if b["worst_day"]<-.20:fail.append("worst_day<-20%")
    if sum(v>0 for v in marginal.values())<2:fail.append("marginal_positive_in_fewer_than_2_folds")
    if min(marginal.values())<=-.05:fail.append("fold_underperformance>5pp")
    if im["severe"]["return"]<=bm["severe"]["return"]:fail.append("severe_not_above_phase252")
    if im["supersevere"]["return"]<=bm["supersevere"]["return"]:fail.append("supersevere_not_above_phase252")
    if active_decisions<18:fail.append("fewer_than_18_active_monthly_decisions")
    if any(x["ruin"] for x in im.values()):fail.append("ruin")
    if dg["max_open_gross"]>1.250000001:fail.append("open_gross>1.25")
    if float(net.abs().max())>1e-12:fail.append("overlay_net_nonzero")
    if float(gross.max())>0.250000001:fail.append("overlay_gross>0.25")
    if float(combo.loc[mask].min().min())<0:fail.append("integrated_target_negative")
    if dg["max_asset_contribution_share"]>.70:fail.append("asset_concentration>70%")
    if dg["top10_absolute_daily_return_share"]>.45:fail.append("top10_day_concentration>45%")

    decision="DEVELOPER_ACCELERATION_RV_CANDIDATE" if not fail else "REJECT_DEVELOPER_ACCELERATION_RV_NO_RESCUE"
    out={
      "engine":"V98 Independent","phase":263,
      "architecture":["growth_core_structural_beta","carry_subsidized_opportunity_sleeve","developer_acceleration_relative_value"],
      "training_only":True,"validation":None,"holdout_accessed":False,
      "v14_used":False,"v15_used":False,"v99_used":False,
      "parameters":{"recent_months":RECENT_MONTHS,"prior_months":PRIOR_MONTHS,
        "score":"log((recent3+1)/(prior3+1))","long_budget":LONG_BUDGET,"short_budget":SHORT_BUDGET,
        "overlay_gross_cap":OVERLAY_GROSS_CAP,"system_gross_cap":SYSTEM_CAP,
        "decision":"first UTC day of month at 23:00 close -> next 00:00 open","tie_policy":"split budget equally among exact extrema"},
      "cost_funding_tiers":P.TIERS,
      "phase262_manifest_sha256":file_sha(a.developer_manifest),
      "phase262_csv_sha256":file_sha(a.developer_csv),
      "baseline_targets_sha256":hashlib.sha256(baseline.to_csv(float_format="%.12g").encode()).hexdigest(),
      "overlay_targets_sha256":hashlib.sha256(overlay.to_csv(float_format="%.12g").encode()).hexdigest(),
      "integrated_targets_sha256":hashlib.sha256(combo.to_csv(float_format="%.12g").encode()).hexdigest(),
      "scores_sha256":hashlib.sha256(scores.to_csv(float_format="%.12g").encode()).hexdigest(),
      "phase252_baseline":bm,"integrated":im,"phase252_folds":bf,"integrated_folds":inf,
      "marginal_return_by_fold":marginal,
      "rv_activity":{"active_monthly_decisions":int(active_decisions),"max_abs_overlay_net":float(net.abs().max()),
        "max_overlay_gross":float(gross.max()),"active_hour_ratio":float((gross>0).mean())},
      "diagnostics":dg,"gate":{"decision":decision,"passed":not fail,"failures":fail}
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"decision":decision,"failures":fail,"phase252":bm,"integrated":im,
      "marginal_return_by_fold":marginal,"rv_activity":out["rv_activity"],
      "diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")}},indent=2,sort_keys=True))
if __name__=="__main__":main()
