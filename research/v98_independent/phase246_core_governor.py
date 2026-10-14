#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"));sys.path.insert(0,str(ROOT/"research"/"v98_independent"))
import phase244_growth_core as P

PEAK_H=2160;CONFIRM_H=168;CRASH_DD=-.20;DECISION_HOUR=23
START_DECISION=pd.Timestamp("2022-12-31T23:00:00Z")

def governed_targets(data):
 c=data.close.loc[:,P.ASSETS]
 lr=np.log(c/c.shift(1));mret=lr.mean(axis=1).fillna(0.)
 level=np.exp(mret.cumsum())
 peak=level.shift(1).rolling(PEAK_H,min_periods=PEAK_H).max()
 dd=level/peak-1
 r7=mret.rolling(CONFIRM_H,min_periods=CONFIRM_H).sum()
 out=pd.DataFrame(0.,index=c.index,columns=P.ASSETS)
 state=1
 for i,t in enumerate(c.index):
  if t<START_DECISION:continue
  if t.hour==DECISION_HOUR and np.isfinite(dd.iloc[i]) and np.isfinite(r7.iloc[i]):
   state=-1 if (dd.iloc[i]<=CRASH_DD and r7.iloc[i]<0) else 1
  out.iloc[i]=state*P.W
 if float(out.abs().sum(axis=1).max())>P.CAP+1e-12:raise RuntimeError("gross invariant")
 return out

def passive_targets(index):
 t=pd.DataFrame(0.,index=index,columns=P.ASSETS);t.loc[t.index>=START_DECISION,:]=P.W;return t

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"));ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"));ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"));ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase246_core_governor_results.json"));a=ap.parse_args()
 sm=json.loads(a.source_manifest.read_text())
 if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(P.ASSETS):raise RuntimeError("Clean-4 source required")
 data=P.load_data(a.price_root,a.funding_root)
 if data.close.index.max()>=P.CUT:raise RuntimeError("2026+ firewall")
 gt=governed_targets(data);pt=passive_targets(data.close.index)
 gr={z:P.run(data,gt,z) for z in P.TIERS};pr={z:P.run(data,pt,z) for z in P.TIERS}
 agg={z:P.metric(gr[z],P.START,P.CUT) for z in P.TIERS};pas={z:P.metric(pr[z],P.START,P.CUT) for z in P.TIERS}
 folds={y:P.metric(gr["base"],s,e) for y,(s,e) in P.FOLDS.items()};dg=P.diag(gr["base"],data,gt)
 fail=[];b=agg["base"];pb=pas["base"]
 if b["return"]<=pb["return"]:fail.append("base_return_not_above_passive")
 if b["cagr"]<=pb["cagr"]:fail.append("base_cagr_not_above_passive")
 if b["max_drawdown"]<=pb["max_drawdown"]:fail.append("base_dd_not_better_than_passive")
 if b["profit_factor_daily"]<pb["profit_factor_daily"]:fail.append("base_pf_below_passive")
 if b["worst_day"]<pb["worst_day"]:fail.append("worst_day_worse_than_passive")
 if sum(x["return"]>0 for x in folds.values())<2:fail.append("fewer_than_2_positive_folds")
 if min(x["return"] for x in folds.values())<=-.25:fail.append("worst_fold<=-25%")
 if agg["severe"]["return"]<=pas["severe"]["return"]:fail.append("severe_return_not_above_passive")
 if agg["supersevere"]["return"]<=pas["supersevere"]["return"]:fail.append("supersevere_return_not_above_passive")
 if any(x["ruin"] for x in agg.values()):fail.append("ruin")
 if dg["max_open_gross"]>1.000000001:fail.append("open_gross>1")
 if dg["max_asset_contribution_share"]>.70:fail.append("asset_concentration>70%")
 if dg["top10_absolute_daily_return_share"]>.40:fail.append("top10_day_concentration>40%")
 decision="CORE_GOVERNOR_ARCHITECTURE_CANDIDATE" if not fail else "REJECT_CORE_GOVERNOR_NO_RESCUE"
 out={"engine":"V98 Independent","phase":246,"architecture":["growth_core_structural_beta","crash_risk_governor"],"training_only":True,"validation":None,"holdout_accessed":False,"v14_used":False,"v15_used":False,"v99_used":False,
 "parameters":{"assets":list(P.ASSETS),"peak_hours":PEAK_H,"confirmation_hours":CONFIRM_H,"crash_drawdown":CRASH_DD,"decision_hour_utc":DECISION_HOUR,"normal_target":"+0.25 each","crash_target":"-0.25 each","gross_cap":P.CAP},
 "cost_funding_tiers":P.TIERS,"source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),"targets_sha256":hashlib.sha256(gt.to_csv(float_format="%.12g").encode()).hexdigest(),
 "governed":agg,"passive":pas,"folds":folds,"diagnostics":dg,"gate":{"decision":decision,"passed":not fail,"failures":fail}}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
 print(json.dumps({"decision":decision,"failures":fail,"governed":agg,"passive":pas,"folds":folds,"diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")}},indent=2,sort_keys=True))
if __name__=="__main__":main()
