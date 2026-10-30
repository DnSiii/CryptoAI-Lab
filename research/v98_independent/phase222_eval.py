#!/usr/bin/env python3
"""V98 Independent Phase222 — frozen range-compression breakout evaluator.
Training only: 2023/2024/2025. Never loads timestamps >= 2026-01-01 UTC.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(c,h,d) for c in (.55,.70) for h in (4,8) for d in ("continuation","symmetric")]
COSTS={"base":.0007,"severe":.0014,"supersevere":.0028}
CUTOFF=pd.Timestamp("2026-01-01",tz="UTC")

def load_prices(root):
 out={}
 for a in ASSETS:
  x=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in x.columns if c.lower() in ("timestamp","time","datetime","date","open_time")); x[tc]=pd.to_datetime(x[tc],utc=True,errors="raise"); x=x.set_index(tc).sort_index(); x.columns=[c.lower() for c in x.columns]
  for c in ("open","high","low","close"): x[c]=pd.to_numeric(x[c],errors="raise")
  if len(x) and (x.index.max()>=CUTOFF or x.index.has_duplicates or not x.index.is_monotonic_increasing): raise RuntimeError(f"price firewall {a}")
  out[a]=x
 return out

def load_funding(root):
 out={}
 for a in ASSETS:
  d=pd.read_csv(root/f"{a}_funding.csv"); t=pd.to_datetime(d.fundingTime_utc,utc=True,errors="raise",format="mixed"); r=pd.to_numeric(d.fundingRate,errors="raise"); x=pd.DataFrame({"rate":r.to_numpy()},index=t).sort_index()
  if len(x) and (x.index.max()>=CUTOFF or x.index.has_duplicates or not x.index.is_monotonic_increasing): raise RuntimeError(f"funding firewall {a}")
  out[a]=x
 return out

def funding_hourly(index,f):
 s=pd.Series(f.rate.to_numpy(),index=f.index.ceil("1h")).groupby(level=0).sum(); return s.reindex(index).fillna(0.)

def features(x):
 # Shift completed-bar inputs first. Nothing from high/low/close(t) enters signal(t).
 hi=x.high.shift(1).rolling(24,min_periods=24).max(); lo=x.low.shift(1).rolling(24,min_periods=24).min()
 r24=hi/lo-1.; med=r24.rolling(168,min_periods=168).median()
 mom24=x.close.shift(1)/x.close.shift(25)-1.
 return pd.DataFrame({"prior_hi":hi,"prior_lo":lo,"range24":r24,"range168_median":med,"mom24":mom24},index=x.index)

def basic_metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1 if len(eq) else r; pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
 return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.}

def run(prices,funding,c,hold,direction,cost,start,stop):
 idx=prices[ASSETS[0]].index
 feat={a:features(prices[a].reindex(idx)) for a in ASSETS}; pos=pd.DataFrame(0.,index=idx,columns=ASSETS); events=[]; until={a:-1 for a in ASSETS}
 for i,t in enumerate(idx):
  if t<start or t>=stop: continue
  for a in sorted(ASSETS):
   if i<until[a]: continue
   f=feat[a].iloc[i]; op=prices[a].open.reindex(idx).iloc[i]
   if not (np.isfinite(op) and np.isfinite(f).all() and f.range24<=c*f.range168_median): continue
   side=1 if op>f.prior_hi else (-1 if op<f.prior_lo else 0)
   if direction=="symmetric" and side and np.sign(f.mom24)!=side: side=0
   if side:
    end=min(i+hold,len(idx)); pos.iloc[i:end,pos.columns.get_loc(a)]=side; events.append((i,end,a,side)); until[a]=end
 n=pos.abs().sum(axis=1); weights=pos.div(n.where(n>0,1.),axis=0)
 if (weights.abs().sum(axis=1)>1+1e-12).any(): raise RuntimeError("gross exposure invariant")
 mask=(idx>=start)&(idx<stop); panel={}; asset_ret={}; fund_contrib={}
 for a in ASSETS:
  w=weights[a]; ret=prices[a].open.reindex(idx).pct_change(fill_method=None); turn=w.diff().abs().fillna(w.abs()); fund=-w.shift(1).fillna(0.)*funding_hourly(idx,funding[a]); pnl=w.shift(1).fillna(0.)*ret.fillna(0.)-turn*cost+fund; z=pnl.loc[mask]; panel[a]=z; asset_ret[a]=float(z.sum()); fund_contrib[a]=float(fund.loc[mask].sum())
 pnl_panel=pd.DataFrame(panel); port=pnl_panel.sum(axis=1); m=basic_metrics(port); arr=[]; trade_assets=[]
 # Clean asset-attributed CLOSED-trade tails. Include the exit/rebalance row e so
 # round-trip turnover cost is represented; exclude fold-boundary-censored trades.
 for j,e,a,side in events:
  if start<=idx[j]<stop and e<len(idx) and idx[e]<stop:
   trade_pnl=float(pnl_panel[a].loc[idx[j]:idx[e]].sum()); arr.append(trade_pnl); trade_assets.append(a)
 arr=np.asarray(arr,float); m["trades"]=int(len(arr)); m["tail_definition"]="closed_trade_asset_attributed_including_exit_turnover"
 for name,q in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[name]=float(np.quantile(arr,q)) if len(arr) else 0.
 m["worst_trade"]=float(arr.min()) if len(arr) else 0.; m["best_trade"]=float(arr.max()) if len(arr) else 0.; m["asset_pnl_contribution"]=asset_ret; den=sum(abs(v) for v in asset_ret.values()); m["max_asset_concentration"]=float(max(abs(v) for v in asset_ret.values())/den) if den else 0.; m["funding_contribution"]=fund_contrib
 btc=prices["BTCUSDT"].close.reindex(idx).pct_change(168,fill_method=None).shift(1).loc[port.index]; regs={"bull":btc>0.03,"bear":btc<-0.03,"sideways":btc.abs()<=0.03}; m["regimes"]={k:basic_metrics(port[v.fillna(False)]) for k,v in regs.items()}; return m

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="research/v98_independent/phase222_results.json"); a=ap.parse_args(); prices=load_prices(Path(a.data_root)); funding=load_funding(Path(a.funding_root)); assert len(SPECS)==8
 out={"phase":222,"family":"intraday_range_compression_breakout_continuation","cutoff":"<2026-01-01","specs":{}}
 for c,h,d in SPECS:
  key=f"compression_{c:.2f}_hold{h}_{d}"; out["specs"][key]={}
  for fold,s,t in FOLDS:
   start=pd.Timestamp(s,tz="UTC"); stop=pd.Timestamp(t,tz="UTC"); ps={k:v.loc[v.index<stop] for k,v in prices.items()}; fm={k:v.loc[v.index<stop] for k,v in funding.items()}
   out["specs"][key][fold]={name:run(ps,fm,c,h,d,cost,start,stop) for name,cost in COSTS.items()}
 raw=json.dumps(out,sort_keys=True,separators=(",",":")); out["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); p=Path(a.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
