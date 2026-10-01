#!/usr/bin/env python3
"""V98 Independent Phase207 — preregistered cross-sectional residual momentum.
Training-only; predictors are t-1 or older. Validation/final holdout is never read.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
ASSETS=("ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT"); BENCH="BTCUSDT"; ALL=(BENCH,)+ASSETS
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(r,b,h) for r in (24,72) for b in (30,90) for h in (8,24)]; COSTS={"base":0.0007,"severe":0.0014,"supersevere":0.0028}; CUTOFF=pd.Timestamp("2026-01-01",tz="UTC")
def load_prices(root):
 out={}
 for a in ALL:
  d=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in d.columns if c.lower() in ("timestamp","time","datetime","date","open_time")); d[tc]=pd.to_datetime(d[tc],utc=True,errors="raise"); d=d.set_index(tc).sort_index(); d.columns=[c.lower() for c in d.columns]
  if d.index.max()>=CUTOFF or d.index.has_duplicates or not d.index.is_monotonic_increasing: raise RuntimeError(f"price invariant {a}")
  out[a]=d
 return out
def load_funding(root):
 out={}
 for a in ASSETS:
  d=pd.read_csv(root/f"{a}_funding.csv"); t=pd.to_datetime(d["fundingTime_utc"],utc=True,errors="raise"); r=pd.to_numeric(d["fundingRate"],errors="raise"); x=pd.DataFrame({"rate":r.to_numpy()},index=t).sort_index()
  if x.index.max()>=CUTOFF or x.index.has_duplicates: raise RuntimeError(f"funding invariant {a}")
  out[a]=x
 return out
def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1; pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
 return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.}
def funding_hourly(index,f):
 x=pd.Series(f.rate.to_numpy(),index=f.index.ceil("1h")).groupby(level=0).sum(); return x.reindex(index).fillna(0.)
def run(prices,funding,res_lb,beta_days,hold,cost,eval_start):
 common=prices[BENCH].index; closes=pd.DataFrame({a:prices[a]["close"].astype(float).reindex(common) for a in ALL}).ffill(); rets=closes.pct_change(); btc=rets[BENCH]; win=beta_days*24
 beta={a:(rets[a].rolling(win,min_periods=max(168,win//4)).cov(btc)/btc.rolling(win,min_periods=max(168,win//4)).var()).shift(1) for a in ASSETS}; cum=closes.pct_change(res_lb).shift(1); residual=pd.DataFrame({a:cum[a]-beta[a]*cum[BENCH] for a in ASSETS},index=common)
 positions=pd.DataFrame(0.,index=common,columns=ASSETS); entries=[]; i=int(common.searchsorted(eval_start))
 while i<len(common):
  row=residual.iloc[i].dropna(); picks={}
  if len(row):
   hi=row.idxmax(); lo=row.idxmin()
   if row[hi]>0: picks[hi]=1.
   if row[lo]<0 and lo!=hi: picks[lo]=-1.
  if picks:
   end=min(i+hold,len(common)); scale=1/len(picks)
   for a,direction in picks.items(): positions.loc[common[i:end],a]=direction*scale; entries.append((a,i,end))
   i=end
  else: i+=1
 pnls={}; asset_returns={}; led=[]; mask=common>=eval_start
 for a in ASSETS:
  p=positions[a]; turnover=p.diff().abs().fillna(p.abs()); hf=funding_hourly(common,funding[a]); pnl=p.shift(1).fillna(0.)*rets[a].fillna(0.)-turnover*cost-p.shift(1).fillna(0.)*hf; pnl=pnl.loc[mask]; pnls[a]=pnl; asset_returns[a]=float((1+pnl).prod()-1)
 panel=pd.DataFrame(pnls); port=panel.sum(axis=1)
 for a,i,end in entries:
  ts=common[i]; te=common[min(end,len(common)-1)]; led.append(float(pnls[a].loc[(pnls[a].index>=ts)&(pnls[a].index<=te)].sum()))
 m=metrics(port); denom=sum(abs(x) for x in asset_returns.values()); m["asset_returns"]=asset_returns; m["max_asset_concentration"]=float(max(abs(x) for x in asset_returns.values())/denom) if denom else 0.; q=np.asarray(led,float); m["trades"]=len(q); m["trade_ledger_sum"]=float(q.sum()) if len(q) else 0.
 for n,pct in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[n]=float(np.quantile(q,pct)) if len(q) else 0.
 m["worst_trade"]=float(q.min()) if len(q) else 0.; m["best_trade"]=float(q.max()) if len(q) else 0.; trend=closes[BENCH].pct_change(168).shift(1).loc[port.index]; regs={"bull":trend>0.03,"bear":trend<-0.03,"sideways":trend.abs()<=0.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regs.items()}; return m
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="reports/v98_independent_phase207_results.json"); args=ap.parse_args(); prices=load_prices(Path(args.data_root)); funding=load_funding(Path(args.funding_root)); result={"phase":207,"family":"cross_sectional_residual_momentum","cutoff":"<2026-01-01","specs":{}}
 for r,b,h in SPECS:
  key=f"res{r}h_beta{b}d_hold{h}h"; result["specs"][key]={}
  for fold,s,t in FOLDS:
   start=pd.Timestamp(s,tz="UTC"); warm=start-pd.Timedelta(days=b+5); ps={a:d.loc[(d.index>=warm)&(d.index<pd.Timestamp(t,tz="UTC"))] for a,d in prices.items()}; fm={a:f.loc[f.index<pd.Timestamp(t,tz="UTC")] for a,f in funding.items()}
   for name,c in COSTS.items(): result["specs"][key].setdefault(fold,{})[name]=run(ps,fm,r,b,h,c,start)
 raw=json.dumps(result,sort_keys=True,separators=(",",":")); result["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
