#!/usr/bin/env python3
"""V98 Independent Phase208 — preregistered volatility-compression breakout.
Training-only; every predictor at decision t uses t-1 or older. Holdout is never read.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(w,q,h) for w in (24,72) for q in (.10,.25) for h in (8,24)]
COSTS={"base":0.0007,"severe":0.0014,"supersevere":0.0028}; CUTOFF=pd.Timestamp("2026-01-01",tz="UTC")
def load_prices(root):
 out={}
 for a in ASSETS:
  d=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in d.columns if c.lower() in ("timestamp","time","datetime","date","open_time")); d[tc]=pd.to_datetime(d[tc],utc=True,errors="raise"); d=d.set_index(tc).sort_index(); d.columns=[c.lower() for c in d.columns]
  if d.index.max()>=CUTOFF or d.index.has_duplicates or not d.index.is_monotonic_increasing: raise RuntimeError(f"price invariant {a}")
  for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="raise")
  out[a]=d
 return out
def load_funding(root):
 out={}
 for a in ASSETS:
  d=pd.read_csv(root/f"{a}_funding.csv"); t=pd.to_datetime(d["fundingTime_utc"],utc=True,errors="raise",format="mixed"); r=pd.to_numeric(d["fundingRate"],errors="raise"); x=pd.DataFrame({"rate":r.to_numpy()},index=t).sort_index()
  if x.index.max()>=CUTOFF or x.index.has_duplicates or not x.index.is_monotonic_increasing: raise RuntimeError(f"funding invariant {a}")
  out[a]=x
 return out
def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1; pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
 return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.}
def funding_hourly(index,f):
 x=pd.Series(f.rate.to_numpy(),index=f.index.ceil("1h")).groupby(level=0).sum(); return x.reindex(index).fillna(0.)
def run(prices,funding,w,q,hold,cost,eval_start):
 common=prices["BTCUSDT"].index; positions=pd.DataFrame(0.,index=common,columns=ASSETS); entries=[]
 for a in ASSETS:
  d=prices[a].reindex(common); lr=np.log(d.close).diff(); rv=lr.rolling(w,min_periods=w).std().shift(1); threshold=rv.shift(1).rolling(2160,min_periods=2160).quantile(q); compressed=rv<=threshold
  prev_close=d.close.shift(1); prior_hi=d.high.shift(2).rolling(24,min_periods=24).max(); prior_lo=d.low.shift(2).rolling(24,min_periods=24).min(); sig=pd.Series(0.,index=common); sig[compressed & (prev_close>prior_hi)]=1.; sig[compressed & (prev_close<prior_lo)]=-1.
  i=int(common.searchsorted(eval_start))
  while i<len(common):
   direction=float(sig.iloc[i]) if pd.notna(sig.iloc[i]) else 0.
   if direction:
    end=min(i+hold,len(common)); positions.loc[common[i:end],a]=direction; entries.append((a,i,end,direction)); i=end
   else: i+=1
 pnls={}; asset_returns={}; led=[]; mask=common>=eval_start
 for a in ASSETS:
  d=prices[a].reindex(common); ret=d.close.pct_change().fillna(0.); p=positions[a]; turnover=p.diff().abs().fillna(p.abs()); hf=funding_hourly(common,funding[a]); pnl=p.shift(1).fillna(0.)*ret-turnover*cost-p.shift(1).fillna(0.)*hf; pnl=pnl.loc[mask]/len(ASSETS); pnls[a]=pnl; asset_returns[a]=float((1+pnl).prod()-1)
 panel=pd.DataFrame(pnls); port=panel.sum(axis=1)
 for a,i,end,direction in entries:
  ts=common[i]; te=common[min(end,len(common)-1)]; led.append(float(pnls[a].loc[(pnls[a].index>=ts)&(pnls[a].index<=te)].sum()))
 m=metrics(port); denom=sum(abs(x) for x in asset_returns.values()); m["asset_returns"]=asset_returns; m["max_asset_concentration"]=float(max(abs(x) for x in asset_returns.values())/denom) if denom else 0.; arr=np.asarray(led,float); m["trades"]=len(arr); m["trade_ledger_sum"]=float(arr.sum()) if len(arr) else 0.
 for n,pct in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[n]=float(np.quantile(arr,pct)) if len(arr) else 0.
 m["worst_trade"]=float(arr.min()) if len(arr) else 0.; m["best_trade"]=float(arr.max()) if len(arr) else 0.; btc=prices["BTCUSDT"].close.reindex(common).pct_change(168).shift(1).loc[port.index]; regs={"bull":btc>0.03,"bear":btc<-0.03,"sideways":btc.abs()<=0.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regs.items()}; return m
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="reports/v98_independent_phase208_results.json"); args=ap.parse_args(); prices=load_prices(Path(args.data_root)); funding=load_funding(Path(args.funding_root)); result={"phase":208,"family":"volatility_compression_breakout","cutoff":"<2026-01-01","specs":{}}
 for w,q,h in SPECS:
  key=f"rv{w}h_q{int(q*100):02d}_hold{h}h"; result["specs"][key]={}
  for fold,s,t in FOLDS:
   start=pd.Timestamp(s,tz="UTC"); stop=pd.Timestamp(t,tz="UTC"); warm=start-pd.Timedelta(days=100); ps={a:d.loc[(d.index>=warm)&(d.index<stop)] for a,d in prices.items()}; fm={a:f.loc[f.index<stop] for a,f in funding.items()}
   for name,c in COSTS.items(): result["specs"][key].setdefault(fold,{})[name]=run(ps,fm,w,q,h,c,start)
 raw=json.dumps(result,sort_keys=True,separators=(",",":")); result["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
