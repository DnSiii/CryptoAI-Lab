#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/"src"))
from cryptoai_v13.data import FuturesData
from cryptoai_v13.backtest import exact_fast

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT");ENTRY=2160;EXIT=720;W=.25;CAP=1.0
START=pd.Timestamp("2023-01-01",tz="UTC");CUT=pd.Timestamp("2026-01-01",tz="UTC")
FOLDS={"2023":(pd.Timestamp("2023-01-01",tz="UTC"),pd.Timestamp("2024-01-01",tz="UTC")),
"2024":(pd.Timestamp("2024-01-01",tz="UTC"),pd.Timestamp("2025-01-01",tz="UTC")),
"2025":(pd.Timestamp("2025-01-01",tz="UTC"),CUT)}
TIERS={"base":(.0007,1.,1.),"severe":(.0012,1.25,.75),"supersevere":(.0020,1.75,.50)}

def load_data(price_root,funding_root):
 raw={}
 for a in ASSETS:
  d=pd.read_csv(price_root/f"{a}_1h.csv");d.index=pd.to_datetime(d.pop("open_time"),utc=True,errors="raise")
  if d.index.has_duplicates or not d.index.is_monotonic_increasing or d.index.max()>=CUT:raise ValueError(f"{a}: price firewall")
  raw[a]=d
 idx=raw[ASSETS[0]].index
 if any(not raw[a].index.equals(idx) for a in ASSETS):raise ValueError("calendar mismatch")
 frames={f:pd.DataFrame({a:pd.to_numeric(raw[a][f],errors="raise") for a in ASSETS},index=idx) for f in ("open","high","low","close","volume","quote_volume")}
 funding=pd.DataFrame(0.,index=idx,columns=ASSETS)
 for a in ASSETS:
  d=pd.read_csv(funding_root/f"{a}_funding.csv");ms=pd.to_numeric(d.fundingTime_ms,errors="raise").astype("int64");rate=pd.to_numeric(d.fundingRate,errors="raise").astype(float)
  ts=pd.to_datetime(ms,unit="ms",utc=True).dt.floor("8h");s=pd.Series(rate.to_numpy(),index=pd.DatetimeIndex(ts)).groupby(level=0).sum()
  if s.index.max()>=CUT:raise ValueError(f"{a}: funding firewall")
  common=idx.intersection(s.index);funding.loc[common,a]=s.reindex(common).to_numpy()
 return FuturesData(frames=frames,funding=funding,symbols=ASSETS)

def targets(data):
 c=data.close.loc[:,ASSETS];hi90=c.shift(1).rolling(ENTRY,min_periods=ENTRY).max();lo90=c.shift(1).rolling(ENTRY,min_periods=ENTRY).min()
 hi30=c.shift(1).rolling(EXIT,min_periods=EXIT).max();lo30=c.shift(1).rolling(EXIT,min_periods=EXIT).min()
 cv,h90,l90,h30,l30=[x.to_numpy(float) for x in (c,hi90,lo90,hi30,lo30)]
 state=np.zeros((len(c),len(ASSETS)),dtype=np.int8);cur=np.zeros(len(ASSETS),dtype=np.int8)
 for i in range(len(c)):
  for j in range(len(ASSETS)):
   if not all(np.isfinite(x) for x in (cv[i,j],h90[i,j],l90[i,j],h30[i,j],l30[i,j])):
    state[i,j]=cur[j];continue
   x=cv[i,j]
   if cur[j]==0:
    if x>h90[i,j]:cur[j]=1
    elif x<l90[i,j]:cur[j]=-1
   elif cur[j]>0:
    if x<l90[i,j]:cur[j]=-1
    elif x<l30[i,j]:cur[j]=0
   else:
    if x>h90[i,j]:cur[j]=1
    elif x>h30[i,j]:cur[j]=0
   state[i,j]=cur[j]
 out=pd.DataFrame(state.astype(float)*W,index=c.index,columns=ASSETS)
 if out.abs().sum(axis=1).max()>CAP+1e-12:raise RuntimeError("target gross")
 return out

def daily(result,s,e):
 eq=result.equity.loc[(result.equity.index>=s)&(result.equity.index<e)]
 return eq.resample("1D").last().pct_change(fill_method=None).dropna()

def metric(result,s,e):
 eq=result.equity.loc[(result.equity.index>=s)&(result.equity.index<e)]
 if len(eq)<2:raise ValueError("empty window")
 total=float(eq.iloc[-1]/eq.iloc[0]-1);dayspan=max((eq.index[-1]-eq.index[0]).total_seconds()/86400,1)
 d=daily(result,s,e);pos=d[d>0];neg=d[d<0];n5=max(1,int(math.ceil(.05*len(d)))) if len(d) else 0
 pf=float(pos.sum()/(-neg.sum())) if len(neg) and -neg.sum()>0 else (999. if len(pos) else 0.)
 mask=(result.turnover.index>=s)&(result.turnover.index<e)
 return {"return":total,"cagr":float((eq.iloc[-1]/eq.iloc[0])**(365.25/dayspan)-1),"max_drawdown":float((eq/eq.cummax()-1).min()),
 "profit_factor_daily":pf,"payoff_daily":float(pos.mean()/(-neg.mean())) if len(pos) and len(neg) else 0.,"win_rate_daily":float((d>0).mean()) if len(d) else 0.,
 "positive_days":int((d>0).sum()),"negative_days":int((d<0).sum()),"days":int(len(d)),"worst_day":float(d.min()) if len(d) else 0.,"best_day":float(d.max()) if len(d) else 0.,
 "p01_day":float(d.quantile(.01)) if len(d) else 0.,"p05_day":float(d.quantile(.05)) if len(d) else 0.,"cvar05_day":float(d.nsmallest(n5).mean()) if n5 else 0.,
 "p50_day":float(d.quantile(.5)) if len(d) else 0.,"p95_day":float(d.quantile(.95)) if len(d) else 0.,"p99_day":float(d.quantile(.99)) if len(d) else 0.,
 "turnover_l1":float(result.turnover.loc[mask].sum()),"fees_paid":float(result.fees.loc[mask].sum()),"funding_net_cost":float(result.funding.loc[mask].sum()),"ruin":bool(result.ruin)}

def diag(r,data,t):
 mask=(r.equity.index>=START)&(r.equity.index<CUT);op=r.open_positions.loc[mask,ASSETS];cp=r.positions.loc[mask,ASSETS]
 contrib=(r.asset_gross.loc[mask,ASSETS]-r.asset_fees.loc[mask,ASSETS]-r.asset_funding.loc[mask,ASSETS]).sum();den=float(contrib.abs().sum())
 shares={a:(float(abs(contrib[a])/den) if den else 0.) for a in ASSETS};d=daily(r,START,CUT);ad=float(d.abs().sum())
 er=r.equity.pct_change(fill_method=None);br=data.close["BTCUSDT"].pct_change(168,fill_method=None).shift(1)
 regs={}
 for name,rm in {"bull":br>.03,"bear":br<-.03,"sideways":br.abs()<=.03}.items():
  x=er.loc[mask & rm.reindex(er.index).fillna(False)].dropna();regs[name]={"hours":int(len(x)),"return_on_classified_hours":float((1+x).prod()-1) if len(x) else 0.,"positive_hour_ratio":float((x>0).mean()) if len(x) else 0.}
 active=t.loc[mask,ASSETS].abs().sum(axis=1)
 return {"max_open_gross":float(op.abs().sum(axis=1).max()),"max_close_gross":float(cp.abs().sum(axis=1).max()),"avg_target_gross":float(active.mean()),"active_hour_ratio":float((active>0).mean()),
 "asset_net_pnl_proxy":{a:float(contrib[a]) for a in ASSETS},"absolute_asset_contribution_share":shares,"max_asset_contribution_share":max(shares.values()),"top10_absolute_daily_return_share":float(d.abs().nlargest(10).sum()/ad) if ad else 0.,"regimes":regs}

def run(data,t,tier):
 cost,debit,credit=TIERS[tier]
 return exact_fast(data,t,cost_per_side=cost,gross_guard_cap=CAP,funding_debit_multiplier=debit,funding_credit_multiplier=credit)

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--price-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"));ap.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"));ap.add_argument("--source-manifest",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"));ap.add_argument("--out",type=Path,default=Path("research/v98_independent/phase244_growth_core_results.json"));a=ap.parse_args()
 sm=json.loads(a.source_manifest.read_text())
 if sm.get("status")!="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA" or sm.get("universe")!=list(ASSETS) or sm.get("holdout_accessed") is not False:raise RuntimeError("Clean-4 source gate required")
 data=load_data(a.price_root,a.funding_root);t=targets(data);rs={z:run(data,t,z) for z in TIERS};agg={z:metric(rs[z],START,CUT) for z in TIERS};folds={y:metric(rs["base"],s,e) for y,(s,e) in FOLDS.items()};dg=diag(rs["base"],data,t)
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
 decision="GROWTH_CORE_CANDIDATE" if not fail else "REJECT_GROWTH_CORE_NO_RESCUE"
 out={"engine":"V98 Independent","phase":244,"role":"growth_core","family":"clean4_time_series_donchian_state_machine","training_only":True,"validation":None,"holdout_accessed":False,"v14_used":False,"v15_used":False,"v99_used":False,
 "parameters":{"assets":list(ASSETS),"entry_hours":ENTRY,"exit_hours":EXIT,"weight_per_active_asset":W,"gross_cap":CAP,"execution":"close(t) decision -> open(t+1)"},"cost_funding_tiers":TIERS,
 "source_manifest_sha256":hashlib.sha256(a.source_manifest.read_bytes()).hexdigest(),"targets_sha256":hashlib.sha256(t.to_csv(float_format="%.12g").encode()).hexdigest(),"aggregate":agg,"folds":folds,"diagnostics":dg,"gate":{"decision":decision,"passed":not fail,"failures":fail}}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
 print(json.dumps({"decision":decision,"failures":fail,"base":b,"severe":sv,"supersevere":ss,"folds":folds,"diagnostics":{k:dg[k] for k in ("max_open_gross","max_close_gross","max_asset_contribution_share","top10_absolute_daily_return_share")}},indent=2,sort_keys=True))
if __name__=="__main__":main()
