#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"));sys.path.insert(0,str(ROOT/"research"/"v98_independent"))
import phase244_growth_core as P

FAST=720;SLOW=2880;BREADTH=3
DECISION_HOUR=23

def market_targets(data):
 c=data.close.loc[:,P.ASSETS]
 lr=np.log(c/c.shift(1))
 market_lr=lr.mean(axis=1)
 fast=market_lr.rolling(FAST,min_periods=FAST).sum()
 slow=market_lr.rolling(SLOW,min_periods=SLOW).sum()
 asset_fast=np.log(c/c.shift(FAST))
 out=pd.DataFrame(0.,index=c.index,columns=P.ASSETS)
 state=0
 for i,t in enumerate(c.index):
  if t.hour==DECISION_HOUR and np.isfinite(fast.iloc[i]) and np.isfinite(slow.iloc[i]):
   vals=asset_fast.iloc[i].replace([np.inf,-np.inf],np.nan).dropna()
   if len(vals)==len(P.ASSETS):
    pos=int((vals>0).sum());neg=int((vals<0).sum())
    if fast.iloc[i]>0 and slow.iloc[i]>0 and pos>=BREADTH:state=1
    elif fast.iloc[i]<0 and slow.iloc[i]<0 and neg>=BREADTH:state=-1
    else:state=0
  out.iloc[i]=state*P.W
 if float(out.abs().sum(axis=1).max())>P.CAP+1e-12:raise RuntimeError("gross invariant")
 return out

def passive_targets(index):
 t=pd.DataFrame(0.,index=index,columns=P.ASSETS)
 start=pd.Timestamp("2022-12-31T23:00:00Z")
 t.loc[t.index>=start,:]=P.W
 return t

def gate(agg,folds,dg,passive):
 b,sv,ss=agg["base"],agg["severe"],agg["supersevere"];fail=[]
 if b["return"]<=1:fail.append("base_return<=100%")
 if b["cagr"]<=.25:fail.append("base_cagr<=25%")
 if b["profit_factor_daily"]<=1.10:fail.append("base_pf<=1.10")
 if b["max_drawdown"]<-.45:fail.append("base_dd<-45%")
 if b["worst_day"]<-.20:fail.append("base_worst_day<-20%")
 if sum(x["return"]>0 for x in folds.values())<2:fail.append("fewer_than_2_positive_folds")
 if min(x["return"] for x in folds.values())<=-.25:fail.append("worst_fold<=-25%")
 if sv["return"]<=.5 or sv["profit_factor_daily"]<=1.05:fail.append("severe_growth_gate")
 if ss["return"]<=0 or ss["profit_factor_daily"]<=1:fail.append("supersevere_edge_gate")
 if any(x["ruin"] for x in agg.values()):fail.append("ruin")
 if dg["max_open_gross"]>1.000000001:fail.append("open_gross>1")
 if dg["max_asset_contribution_share"]>.70:fail.append("asset_concentration>70%")
 if dg["top10_absolute_daily_return_share"]>.40:fail.append("top10_day_concentration>40%")
 if b["return"]<=passive["return"]:fail.append("base_return<=passive_clean4")
 return fail

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"));ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"));ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"));ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase245_market_state_core_results.json"));a=ap.parse_args()
 sm=json.loads(a.source_manifest.read_text())
 if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):raise RuntimeError("Clean-4 source required")
 data=P.load_data(a.price_root,a.funding_root)
 if data.close.index.max()>=P.CUT:raise RuntimeError("2026+ firewall")
 t=market_targets(data);rs={z:P.run(data,t,z) for z in P.TIERS}
 agg={z:P.metric(rs[z],P.START,P.CUT) for z in P.TIERS};folds={y:P.metric(rs["base"],s,e) for y,(s,e) in P.FOLDS.items()};dg=P.diag(rs["base"],data,t)
 pt=passive_targets(data.close.index);pr=P.run(data,pt,"base");passive=P.metric(pr,P.START,P.CUT)
 fail=gate(agg,folds,dg,passive);decision="GROWTH_CORE_CANDIDATE" if not fail else "REJECT_GROWTH_CORE_NO_RESCUE"
 out={"engine":"V98 Independent","phase":245,"role":"growth_core","family":"clean4_broad_market_dual_horizon_breadth_state","training_only":True,"validation":None,"holdout_accessed":False,"v14_used":False,"v15_used":False,"v99_used":False,
 "parameters":{"assets":list(P.ASSETS),"fast_hours":FAST,"slow_hours":SLOW,"breadth_assets_required":BREADTH,"decision_hour_utc":DECISION_HOUR,"weight_per_asset":P.W,"gross_cap":P.CAP,"execution":"23:00 close(t) decision -> 00:00 open(t+1)"},
 "cost_funding_tiers":P.TIERS,"passive_reference":{"definition":"Clean-4 equal-weight long-only from first 2023 open","base":passive},
 "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),"targets_sha256":hashlib.sha256(t.to_csv(float_format="%.12g").encode()).hexdigest(),"aggregate":agg,"folds":folds,"diagnostics":dg,"gate":{"decision":decision,"passed":not fail,"failures":fail}}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
 print(json.dumps({"decision":decision,"failures":fail,"base":agg["base"],"passive_base":passive,"severe":agg["severe"],"supersevere":agg["supersevere"],"folds":folds,"diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")}},indent=2,sort_keys=True))
if __name__=="__main__":main()
