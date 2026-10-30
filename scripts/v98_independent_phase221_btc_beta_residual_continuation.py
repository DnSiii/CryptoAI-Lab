#!/usr/bin/env python3
"""V98 Independent Phase221 — preregistered BTC-beta residual cross-sectional continuation."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
ASSETS=("ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(W,L,h) for W in (168,336) for L in (6,24) for h in (4,8)]
COSTS={"base":.0007,"severe":.0014,"supersevere":.0028}; CUTOFF=pd.Timestamp("2026-01-01",tz="UTC"); EPS=1e-12

def load_prices(root):
 out={}
 for a in ("BTCUSDT",)+ASSETS:
  x=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in x.columns if c.lower() in ("timestamp","time","datetime","date","open_time")); x[tc]=pd.to_datetime(x[tc],utc=True,errors="raise"); x=x.set_index(tc).sort_index(); x.columns=[c.lower() for c in x.columns]; x["open"]=pd.to_numeric(x["open"],errors="raise"); x["close"]=pd.to_numeric(x["close"],errors="raise")
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

def residual_scores(prices,W,L):
 idx=prices["BTCUSDT"].index
 rb=prices["BTCUSDT"].close.reindex(idx).pct_change(fill_method=None)
 out={}
 for a in ASSETS:
  ri=prices[a].close.reindex(idx).pct_change(fill_method=None)
  # shift first: every beta/score at decision t uses returns ending at t-1 only.
  xb=rb.shift(1); xi=ri.shift(1); cov=xi.rolling(W,min_periods=W).cov(xb); var=xb.rolling(W,min_periods=W).var(ddof=1); beta=cov/var.where(var.abs()>EPS)
  eps=xi-beta*xb
  out[a]=eps.rolling(L,min_periods=L).sum()
 return pd.DataFrame(out)

def run(prices,funding,W,L,hold,cost,start,stop):
 idx=prices["BTCUSDT"].index; scores=residual_scores(prices,W,L); pos=pd.DataFrame(0.,index=idx,columns=ASSETS); events=[]; active_until=-1; i=int(idx.searchsorted(start))
 while i<len(idx) and idx[i]<stop:
  if i>=active_until:
   row=scores.iloc[i]
   if row.notna().all() and np.isfinite(row.to_numpy()).all() and row.nunique()==len(ASSETS):
    lo=row.idxmin(); hi=row.idxmax(); end=min(i+hold,len(idx)); pos.iloc[i:end,pos.columns.get_loc(hi)]=.5; pos.iloc[i:end,pos.columns.get_loc(lo)]=-.5; events.append((i,end,hi,lo)); active_until=end
  i+=1
 if (pos.abs().sum(axis=1)>1+1e-12).any(): raise RuntimeError("gross exposure invariant")
 mask=(idx>=start)&(idx<stop); panel={}; ar={}; fc={}
 for a in ASSETS:
  p=pos[a]; ret=prices[a].open.reindex(idx).pct_change(fill_method=None); turn=p.diff().abs().fillna(p.abs()); fund=-p.shift(1).fillna(0.)*hourly_funding(idx,funding[a]); pnl=p.shift(1).fillna(0.)*ret.fillna(0.)-turn*cost+fund; panel[a]=pnl.loc[mask]; ar[a]=float((1+pnl.loc[mask]).prod()-1); fc[a]=float(fund.loc[mask].sum())
 panel=pd.DataFrame(panel); port=panel.sum(axis=1); trades=[]
 for j,e,_,_ in events:
  if start<=idx[j]<stop:
   last=min(idx[e-1],stop-pd.Timedelta(hours=1)); trades.append(float(port.loc[idx[j]:last].sum()))
 m=metrics(port); den=sum(abs(v) for v in ar.values()); m["asset_returns"]=ar; m["max_asset_concentration"]=float(max(abs(v) for v in ar.values())/den) if den else 0.; m["funding_contribution"]=fc; arr=np.asarray(trades,float); m["trades"]=len(arr)
 for n,q in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[n]=float(np.quantile(arr,q)) if len(arr) else 0.
 m["worst_trade"]=float(arr.min()) if len(arr) else 0.; m["best_trade"]=float(arr.max()) if len(arr) else 0.; btc=prices["BTCUSDT"].close.reindex(idx).pct_change(168,fill_method=None).shift(1).loc[port.index]; regs={"bull":btc>0.03,"bear":btc<-0.03,"sideways":btc.abs()<=0.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regs.items()}; return m

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="reports/v98_independent_phase221_results.json"); a=ap.parse_args(); prices=load_prices(Path(a.data_root)); funding=load_funding(Path(a.funding_root)); out={"phase":221,"family":"btc_beta_residual_cross_sectional_continuation","cutoff":"<2026-01-01","specs":{}}; assert len(SPECS)==8
 for W,L,h in SPECS:
  key=f"resbeta_W{W}_L{L}_hold{h}"; out["specs"][key]={}
  for fold,s,t in FOLDS:
   start=pd.Timestamp(s,tz="UTC"); stop=pd.Timestamp(t,tz="UTC"); ps={k:v.loc[v.index<stop] for k,v in prices.items()}; fm={k:v.loc[v.index<stop] for k,v in funding.items()}
   for name,c in COSTS.items(): out["specs"][key].setdefault(fold,{})[name]=run(ps,fm,W,L,h,c,start,stop)
 raw=json.dumps(out,sort_keys=True,separators=(",",":")); out["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); p=Path(a.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
