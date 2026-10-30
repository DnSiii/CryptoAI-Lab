#!/usr/bin/env python3
"""V98 Independent Phase213 — preregistered close-location continuation."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
ASSETS=("ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(L,c,h) for L in (72,168) for c in (.60,.75) for h in (3,6)]
COSTS={"base":.0007,"severe":.0014,"supersevere":.0028}; CUTOFF=pd.Timestamp("2026-01-01",tz="UTC"); BODY=.35

def load_prices(root):
 out={}
 for a in ("BTCUSDT",)+ASSETS:
  d=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in d.columns if c.lower() in ("timestamp","time","datetime","date","open_time")); d[tc]=pd.to_datetime(d[tc],utc=True,errors="raise"); d=d.set_index(tc).sort_index(); d.columns=[c.lower() for c in d.columns]
  for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="raise")
  if d.index.max()>=CUTOFF or d.index.has_duplicates or not d.index.is_monotonic_increasing: raise RuntimeError(f"price invariant {a}")
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

def run(prices,funding,L,clvcut,hold,cost,start,stop):
 common=prices["BTCUSDT"].index; positions=pd.DataFrame(0.,index=common,columns=ASSETS); events={a:[] for a in ASSETS}
 for a in ASSETS:
  d=prices[a].reindex(common); rng=d.high.shift(1)-d.low.shift(1); clv=((d.close.shift(1)-d.low.shift(1))-(d.high.shift(1)-d.close.shift(1)))/rng.replace(0,np.nan); body=(d.close.shift(1)-d.open.shift(1))/rng.replace(0,np.nan); tr=rng; med=tr.rolling(L,min_periods=L).median()
  active=-1; i=int(common.searchsorted(start))
  while i<len(common) and common[i]<stop:
   if i>=active and np.isfinite(clv.iloc[i]) and np.isfinite(body.iloc[i]) and np.isfinite(med.iloc[i]) and tr.iloc[i]>=med.iloc[i]:
    s=1. if clv.iloc[i]>=clvcut and body.iloc[i]>=BODY else (-1. if clv.iloc[i]<=-clvcut and body.iloc[i]<=-BODY else 0.)
    if s:
     end=min(i+hold,len(common)); positions.iloc[i:end,positions.columns.get_loc(a)]=s/len(ASSETS); active=end; events[a].append((i,end,s))
   i+=1
 pnls={}; asset_returns={}; funding_contrib={}; led=[]; mask=(common>=start)&(common<stop)
 for a in ASSETS:
  p=positions[a]; ret=prices[a].open.reindex(common).pct_change(); turnover=p.diff().abs().fillna(p.abs()); hf=funding_hourly(common,funding[a]); fp=-p.shift(1).fillna(0.)*hf; pnl=p.shift(1).fillna(0.)*ret.fillna(0.)-turnover*cost+fp; pnl=pnl.loc[mask]; pnls[a]=pnl; asset_returns[a]=float((1+pnl).prod()-1); funding_contrib[a]=float(fp.loc[mask].sum())
 panel=pd.DataFrame(pnls); port=panel.sum(axis=1)
 for a,evs in events.items():
  for i,end,s in evs:
   ts=common[i]
   if start<=ts<stop: led.append(float(panel[a].loc[ts:min(common[end-1],stop-pd.Timedelta(hours=1))].sum()))
 m=metrics(port); denom=sum(abs(x) for x in asset_returns.values()); m["asset_returns"]=asset_returns; m["max_asset_concentration"]=float(max(abs(x) for x in asset_returns.values())/denom) if denom else 0.; m["funding_contribution"]=funding_contrib; arr=np.asarray(led,float); m["trades"]=len(arr)
 for n,q in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[n]=float(np.quantile(arr,q)) if len(arr) else 0.
 m["worst_trade"]=float(arr.min()) if len(arr) else 0.; m["best_trade"]=float(arr.max()) if len(arr) else 0.; btc=prices["BTCUSDT"].close.reindex(common).pct_change(168).shift(1).loc[port.index]; regs={"bull":btc>0.03,"bear":btc<-0.03,"sideways":btc.abs()<=0.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regs.items()}; return m

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="reports/v98_independent_phase213_results.json"); args=ap.parse_args(); prices=load_prices(Path(args.data_root)); funding=load_funding(Path(args.funding_root)); result={"phase":213,"family":"close_location_continuation","cutoff":"<2026-01-01","specs":{}}; assert len(SPECS)==8
 for L,c,h in SPECS:
  key=f"clv_L{L}_c{int(c*100):02d}_hold{h}"; result["specs"][key]={}
  for fold,s,t in FOLDS:
   start=pd.Timestamp(s,tz="UTC"); stop=pd.Timestamp(t,tz="UTC"); warm=start-pd.Timedelta(hours=L+24); ps={a:d.loc[(d.index>=warm)&(d.index<stop)] for a,d in prices.items()}; fm={a:f.loc[f.index<stop] for a,f in funding.items()}
   for name,cost in COSTS.items(): result["specs"][key].setdefault(fold,{})[name]=run(ps,fm,L,c,h,cost,start,stop)
 raw=json.dumps(result,sort_keys=True,separators=(",",":")); result["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
