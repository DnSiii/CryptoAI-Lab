#!/usr/bin/env python3
"""V98 Independent Phase219 — preregistered funding-extreme post-settlement mean reversion."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
ASSETS=("ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(L,Z,h) for L in (90,270) for Z in (1.5,2.0) for h in (4,8)]
COSTS={"base":.0007,"severe":.0014,"supersevere":.0028}; CUTOFF=pd.Timestamp("2026-01-01",tz="UTC")
def load_prices(root):
 out={}
 for a in ("BTCUSDT",)+ASSETS:
  x=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in x.columns if c.lower() in ("timestamp","time","datetime","date","open_time")); x[tc]=pd.to_datetime(x[tc],utc=True,errors="raise"); x=x.set_index(tc).sort_index(); x.columns=[c.lower() for c in x.columns]
  x["open"]=pd.to_numeric(x["open"],errors="raise"); x["close"]=pd.to_numeric(x["close"],errors="raise")
  if x.index.max()>=CUTOFF or x.index.has_duplicates or not x.index.is_monotonic_increasing: raise RuntimeError(f"price invariant {a}")
  out[a]=x
 return out
def load_funding(root):
 out={}
 for a in ASSETS:
  d=pd.read_csv(root/f"{a}_funding.csv"); t=pd.to_datetime(d.fundingTime_utc,utc=True,errors="raise",format="mixed"); r=pd.to_numeric(d.fundingRate,errors="raise"); x=pd.DataFrame({"rate":r.to_numpy()},index=t).sort_index()
  if x.index.max()>=CUTOFF or x.index.has_duplicates or not x.index.is_monotonic_increasing: raise RuntimeError(f"funding invariant {a}")
  out[a]=x
 return out
def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1; pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
 return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.}
def hourly_funding(index,f):
 s=pd.Series(f.rate.to_numpy(),index=f.index.ceil("1h")).groupby(level=0).sum(); return s.reindex(index).fillna(0.)
def funding_signal(index,f,L,Z):
 # settlement at hour h becomes eligible only from h+1 onward: strict fundingTime <= t-1h
 obs=f.rate.astype(float); mu=obs.rolling(L,min_periods=L).mean(); sd=obs.rolling(L,min_periods=L).std(ddof=0); z=(obs-mu)/sd.replace(0,np.nan)
 known=pd.Series(z.to_numpy(),index=z.index.ceil("1h")+pd.Timedelta(hours=1)).groupby(level=0).last().reindex(index).ffill()
 return pd.Series(np.where(known>=Z,-1.,np.where(known<=-Z,1.,0.)),index=index),known
def run(prices,funding,L,Z,hold,cost,start,stop):
 idx=prices["BTCUSDT"].index; pos=pd.DataFrame(0.,index=idx,columns=ASSETS); events=[]
 for a in ASSETS:
  sig,z=funding_signal(idx,funding[a],L,Z); active=-1; i=int(idx.searchsorted(start))
  while i<len(idx) and idx[i]<stop:
   if i>=active and sig.iloc[i]!=0:
    end=min(i+hold,len(idx)); pos.iloc[i:end,pos.columns.get_loc(a)]=sig.iloc[i]; events.append((i,end,a,float(z.iloc[i]))); active=end
   i+=1
 gross=pos.abs().sum(axis=1); pos=pos.div(gross.where(gross>1,1),axis=0); mask=(idx>=start)&(idx<stop); panel={}; ar={}; fc={}
 for a in ASSETS:
  p=pos[a]; ret=prices[a].open.reindex(idx).pct_change(fill_method=None); turn=p.diff().abs().fillna(p.abs()); fund=-p.shift(1).fillna(0.)*hourly_funding(idx,funding[a]); pnl=p.shift(1).fillna(0.)*ret.fillna(0.)-turn*cost+fund; panel[a]=pnl.loc[mask]; ar[a]=float((1+pnl.loc[mask]).prod()-1); fc[a]=float(fund.loc[mask].sum())
 panel=pd.DataFrame(panel); port=panel.sum(axis=1); trade=[]
 for i,e,a,_ in events:
  if start<=idx[i]<stop:
   last=min(idx[e-1],stop-pd.Timedelta(hours=1)); trade.append(float(panel[a].loc[idx[i]:last].sum()))
 m=metrics(port); den=sum(abs(v) for v in ar.values()); m["asset_returns"]=ar; m["max_asset_concentration"]=float(max(abs(v) for v in ar.values())/den) if den else 0.; m["funding_contribution"]=fc; arr=np.asarray(trade,float); m["trades"]=len(arr)
 for n,q in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[n]=float(np.quantile(arr,q)) if len(arr) else 0.
 m["worst_trade"]=float(arr.min()) if len(arr) else 0.; m["best_trade"]=float(arr.max()) if len(arr) else 0.; btc=prices["BTCUSDT"].close.reindex(idx).pct_change(168,fill_method=None).shift(1).loc[port.index]; regs={"bull":btc>0.03,"bear":btc<-0.03,"sideways":btc.abs()<=0.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regs.items()}; return m
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="reports/v98_independent_phase219_results.json"); a=ap.parse_args(); prices=load_prices(Path(a.data_root)); funding=load_funding(Path(a.funding_root)); out={"phase":219,"family":"funding_extreme_post_settlement_mean_reversion","cutoff":"<2026-01-01","specs":{}}; assert len(SPECS)==8
 for L,Z,h in SPECS:
  key=f"fund_L{L}_Z{int(Z*10):02d}_hold{h}"; out["specs"][key]={}
  for fold,s,t in FOLDS:
   start=pd.Timestamp(s,tz="UTC"); stop=pd.Timestamp(t,tz="UTC"); ps={k:v.loc[v.index<stop] for k,v in prices.items()}; fm={k:v.loc[v.index<stop] for k,v in funding.items()}
   for name,c in COSTS.items(): out["specs"][key].setdefault(fold,{})[name]=run(ps,fm,L,Z,h,c,start,stop)
 raw=json.dumps(out,sort_keys=True,separators=(",",":")); out["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); p=Path(a.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
