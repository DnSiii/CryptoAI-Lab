#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"));sys.path.insert(0,str(ROOT/"research"/"v98_independent"))
import phase244_growth_core as P

LOOKBACK=720;BREADTH=3;SLEEVE_PER_ASSET=.0625;SYSTEM_CAP=1.25
DECISION_HOUR=23;START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def targets(data):
 c=data.close.loc[:,P.ASSETS];hi=c.shift(1).rolling(LOOKBACK,min_periods=LOOKBACK).max()
 core=pd.DataFrame(0.,index=c.index,columns=P.ASSETS)
 sleeve=pd.DataFrame(0.,index=c.index,columns=P.ASSETS)
 active=False
 for i,t in enumerate(c.index):
  if t<START_DECISION:continue
  core.iloc[i]=P.W
  if t.hour==DECISION_HOUR:
   ok=(c.iloc[i]>hi.iloc[i]).fillna(False)
   active=int(ok.sum())>=BREADTH
  if active:sleeve.iloc[i]=SLEEVE_PER_ASSET
 out=core+sleeve
 if float(out.abs().sum(axis=1).max())>SYSTEM_CAP+1e-12:raise RuntimeError("system gross invariant")
 return core,sleeve,out

def run(data,t,tier,cap):
 cost,debit,credit=P.TIERS[tier]
 return P.exact_fast(data,t,cost_per_side=cost,gross_guard_cap=cap,
                     funding_debit_multiplier=debit,funding_credit_multiplier=credit)

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"));ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"));ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"));ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase247_opportunity_results.json"));a=ap.parse_args()
 sm=json.loads(a.source_manifest.read_text())
 if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):raise RuntimeError("Clean-4 source required")
 data=P.load_data(a.price_root,a.funding_root)
 if data.close.index.max()>=P.CUT:raise RuntimeError("2026+ firewall")
 core,sleeve,combo=targets(data)
 cr={z:run(data,core,z,1.0) for z in P.TIERS};sr={z:run(data,combo,z,SYSTEM_CAP) for z in P.TIERS}
 core_m={z:P.metric(cr[z],P.START,P.CUT) for z in P.TIERS};sys_m={z:P.metric(sr[z],P.START,P.CUT) for z in P.TIERS}
 cf={y:P.metric(cr["base"],s,e) for y,(s,e) in P.FOLDS.items()};sf={y:P.metric(sr["base"],s,e) for y,(s,e) in P.FOLDS.items()}
 marginal={y:sf[y]["return"]-cf[y]["return"] for y in P.FOLDS};dg=P.diag(sr["base"],data,combo)
 b,pb=sys_m["base"],core_m["base"];fail=[]
 if b["return"]<=pb["return"]*1.05:fail.append("base_marginal_return<5pct_relative")
 if b["cagr"]<=pb["cagr"]:fail.append("base_cagr_not_above_core")
 if b["max_drawdown"]<pb["max_drawdown"]-.05:fail.append("dd_worse_by_more_than_5pp")
 if b["profit_factor_daily"]<1.10:fail.append("base_pf<1.10")
 if b["worst_day"]<-.20:fail.append("worst_day<-20%")
 if sum(v>0 for v in marginal.values())<2:fail.append("marginal_positive_in_fewer_than_2_folds")
 if min(marginal.values())<=-.10:fail.append("fold_underperformance>10pp")
 if sys_m["severe"]["return"]<=core_m["severe"]["return"]:fail.append("severe_not_above_core")
 if sys_m["supersevere"]["return"]<=core_m["supersevere"]["return"]:fail.append("supersevere_not_above_core")
 if any(x["ruin"] for x in sys_m.values()):fail.append("ruin")
 if dg["max_open_gross"]>1.250000001:fail.append("open_gross>1.25")
 if dg["max_asset_contribution_share"]>.70:fail.append("asset_concentration>70%")
 if dg["top10_absolute_daily_return_share"]>.45:fail.append("top10_day_concentration>45%")
 decision="OPPORTUNITY_SLEEVE_CANDIDATE" if not fail else "REJECT_OPPORTUNITY_NO_RESCUE"
 mask=(sleeve.index>=P.START)&(sleeve.index<P.CUT);active=sleeve.loc[mask].abs().sum(axis=1)>0
 out={"engine":"V98 Independent","phase":247,"architecture":["growth_core_structural_beta","synchronized_breakout_opportunity"],"training_only":True,"validation":None,"holdout_accessed":False,"v14_used":False,"v15_used":False,"v99_used":False,
 "parameters":{"assets":list(P.ASSETS),"lookback_hours":LOOKBACK,"breadth_required":BREADTH,"sleeve_per_asset":SLEEVE_PER_ASSET,"core_per_asset":P.W,"system_gross_cap":SYSTEM_CAP,"decision_hour_utc":DECISION_HOUR},
 "cost_funding_tiers":P.TIERS,"source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),"combined_targets_sha256":hashlib.sha256(combo.to_csv(float_format="%.12g").encode()).hexdigest(),
 "core":core_m,"combined":sys_m,"core_folds":cf,"combined_folds":sf,"marginal_return_by_fold":marginal,
 "opportunity_activity":{"active_hour_ratio":float(active.mean()),"active_hours":int(active.sum()),"trigger_days_equivalent":float(active.sum()/24)},
 "diagnostics":dg,"gate":{"decision":decision,"passed":not fail,"failures":fail}}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
 print(json.dumps({"decision":decision,"failures":fail,"core":core_m,"combined":sys_m,"marginal_return_by_fold":marginal,"opportunity_activity":out["opportunity_activity"],"diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")}},indent=2,sort_keys=True))
if __name__=="__main__":main()
