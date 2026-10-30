#!/usr/bin/env python3
"""V98 Independent Phase211 — preregistered BTC->alts causal lead-lag continuation."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
ASSETS=("ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT"); BENCH="BTCUSDT"; ALL=(BENCH,)+ASSETS
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01")); SPECS=[(l,z,h) for l in (6,12) for z in (2.,2.5) for h in (6,12)]; COSTS={"base":0.0007,"severe":0.0014,"supersevere":0.0028}; CUTOFF=pd.Timestamp("2026-01-01",tz="UTC")
def load_prices(root):
 out={}
 for a in ALL:
  d=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in d.columns if c.lower() in ("timestamp","time","datetime","date","open_time")); d[tc]=pd.to_datetime(d[tc],utc=True,errors="raise"); d=d.set_index(tc).sort_index(); d.columns=[c.lower() for c in d.columns]; d["open"]=pd.to_numeric(d["open"],errors="raise"); d["close"]=pd.to_numeric(d["close"],errors="raise")
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
def run(prices,funding,L,zcut,hold,cost,eval_start):
 common=prices[BENCH].index; opens=pd.DataFrame({a:prices[a].open.reindex(common) for a in ALL}); closes=prices[BENCH].close.reindex(common); rets=opens.pct_change(); impulse=closes.shift(1)/closes.shift(1+L)-1
 med=impulse.shift(1).rolling(2160,min_periods=2160).median(); mad=(impulse.shift(1)-med).abs().rolling(2160,min_periods=2160).median(); z=(impulse-med)/(1.4826*mad.replace(0,np.nan))
 positions=pd.DataFrame(0.,index=common,columns=ASSETS); events=[]; active_until=-1; i=int(common.searchsorted(eval_start))
 while i<len(common):
  if i>=active_until and np.isfinite(z.iloc[i]) and abs(z.iloc[i])>=zcut:
   end=min(i+hold,len(common)); s=float(np.sign(z.iloc[i])); positions.iloc[i:end,:]=s/len(ASSETS); active_until=end; events.append((i,end,s))
  i+=1
 pnls={}; asset_returns={}; funding_contrib={}; mask=common>=eval_start
 for a in ASSETS:
  p=positions[a]; turnover=p.diff().abs().fillna(p.abs()); hf=funding_hourly(common,funding[a]); fp=-p.shift(1).fillna(0.)*hf; pnl=p.shift(1).fillna(0.)*rets[a].fillna(0.)-turnover*cost+fp; pnl=pnl.loc[mask]; pnls[a]=pnl; asset_returns[a]=float((1+pnl).prod()-1); funding_contrib[a]=float(fp.loc[mask].sum())
 panel=pd.DataFrame(pnls); port=panel.sum(axis=1); led=[]
 for i,end,s in events:
  if common[i]<eval_start: continue
  led.append(float(port.iloc[i:min(end,len(port))].sum()))
 m=metrics(port); denom=sum(abs(x) for x in asset_returns.values()); m["asset_returns"]=asset_returns; m["max_asset_concentration"]=float(max(abs(x) for x in asset_returns.values())/denom) if denom else 0.; m["funding_contribution"]=funding_contrib; arr=np.asarray(led,float); m["trades"]=len(arr)
 for n,pct in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[n]=float(np.quantile(arr,pct)) if len(arr) else 0.
 m["worst_trade"]=float(arr.min()) if len(arr) else 0.; m["best_trade"]=float(arr.max()) if len(arr) else 0.; btc=closes.pct_change(168).shift(1).loc[port.index]; regs={"bull":btc>0.03,"bear":btc<-0.03,"sideways":btc.abs()<=0.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regs.items()}; return m
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="reports/v98_independent_phase211_results.json"); args=ap.parse_args(); prices=load_prices(Path(args.data_root)); funding=load_funding(Path(args.funding_root)); result={"phase":211,"family":"btc_alt_leadlag_continuation","cutoff":"<2026-01-01","specs":{}}
 assert len(SPECS)==8
 for L,z,h in SPECS:
  key=f"leadbtc_L{L}_z{int(z*10):02d}_hold{h}"; result["specs"][key]={}
  for fold,s,t in FOLDS:
   start=pd.Timestamp(s,tz="UTC"); stop=pd.Timestamp(t,tz="UTC"); warm=start-pd.Timedelta(days=120); ps={a:d.loc[(d.index>=warm)&(d.index<stop)] for a,d in prices.items()}; fm={a:f.loc[f.index<stop] for a,f in funding.items()}
   for name,c in COSTS.items(): result["specs"][key].setdefault(fold,{})[name]=run(ps,fm,L,z,h,c,start)
 raw=json.dumps(result,sort_keys=True,separators=(",",":")); result["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
