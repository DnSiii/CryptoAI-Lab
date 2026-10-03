#!/usr/bin/env python3
"""V98 Independent Phase223 — frozen idiosyncratic volatility-shock mean-reversion evaluator.
Contingency only: execute after Phase222 mechanical disposition. Training only 2023-2025.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(w,k,h) for w in (168,336) for k in (2.5,3.5) for h in (2,6)]
COSTS={"base":.0007,"severe":.0014,"supersevere":.0028}; CUTOFF=pd.Timestamp("2026-01-01",tz="UTC")

def load_prices(root):
 out={}
 for a in ASSETS:
  x=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in x.columns if c.lower() in ("timestamp","time","datetime","date","open_time")); x[tc]=pd.to_datetime(x[tc],utc=True,errors="raise"); x=x.set_index(tc).sort_index(); x.columns=[c.lower() for c in x.columns]
  for c in ("open","close"): x[c]=pd.to_numeric(x[c],errors="raise")
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

def feature(x,w):
 # Completed returns through t-1 only. Shift before rolling sigma.
 r=x.close.pct_change(fill_method=None); r1=r.shift(1); sig=r.shift(1).rolling(w,min_periods=w).std(); return pd.DataFrame({"r1":r1,"sigma":sig,"z":r1/sig},index=x.index)

def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1 if len(eq) else r; pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
 return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.}

def run(prices,funding,w,k,hold,cost,start,stop):
 idx=prices["BTCUSDT"].index; fs={a:feature(prices[a].reindex(idx),w) for a in ASSETS}; pos=pd.DataFrame(0.,index=idx,columns=ASSETS); events=[]; until={a:-1 for a in ASSETS}
 for i,t in enumerate(idx):
  if t<start or t>=stop: continue
  btc=fs["BTCUSDT"].r1.iloc[i]
  if not np.isfinite(btc): continue
  for a in ASSETS:
   if i<until[a]: continue
   z=fs[a].z.iloc[i]
   if not np.isfinite(z) or abs(z)<k: continue
   shock=np.sign(z)
   if shock==np.sign(btc) and abs(btc)>=.0075: continue
   side=-int(shock); end=min(i+hold,len(idx)); pos.iloc[i:end,pos.columns.get_loc(a)]=side; events.append((i,end,a)); until[a]=end
 n=pos.abs().sum(axis=1); weights=pos.div(n.where(n>0,1.),axis=0)
 if (weights.abs().sum(axis=1)>1+1e-12).any(): raise RuntimeError("gross exposure invariant")
 mask=(idx>=start)&(idx<stop); panel={}; contrib={}; fcon={}
 for a in ASSETS:
  ww=weights[a]; rr=prices[a].open.reindex(idx).pct_change(fill_method=None); turn=ww.diff().abs().fillna(ww.abs()); fund=-ww.shift(1).fillna(0.)*funding_hourly(idx,funding[a]); pnl=ww.shift(1).fillna(0.)*rr.fillna(0.)-turn*cost+fund; z=pnl.loc[mask]; panel[a]=z; contrib[a]=float(z.sum()); fcon[a]=float(fund.loc[mask].sum())
 pp=pd.DataFrame(panel); port=pp.sum(axis=1); m=metrics(port); trades=[]
 for j,e,a in events:
  if start<=idx[j]<stop and e<len(idx) and idx[e]<stop: trades.append(float(pp[a].loc[idx[j]:idx[e]].sum()))
 q=np.asarray(trades,float); m["trades"]=len(trades); m["tail_definition"]="closed_trade_asset_attributed_including_exit_turnover"
 for name,pct in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[name]=float(np.quantile(q,pct)) if len(q) else 0.
 m["worst_trade"]=float(q.min()) if len(q) else 0.; m["best_trade"]=float(q.max()) if len(q) else 0.; m["asset_pnl_contribution"]=contrib; den=sum(abs(v) for v in contrib.values()); m["max_asset_concentration"]=max((abs(v) for v in contrib.values()),default=0.)/den if den else 0.; m["funding_contribution"]=fcon
 btc168=prices["BTCUSDT"].close.reindex(idx).pct_change(168,fill_method=None).shift(1).loc[port.index]; regs={"bull":btc168>0.03,"bear":btc168<-0.03,"sideways":btc168.abs()<=0.03}; m["regimes"]={name:metrics(port[sel.fillna(False)]) for name,sel in regs.items()}; return m

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="research/v98_independent/phase223_results.json"); a=ap.parse_args(); prices=load_prices(Path(a.data_root)); funding=load_funding(Path(a.funding_root)); assert len(SPECS)==8
 out={"phase":223,"family":"idiosyncratic_volatility_shock_mean_reversion","cutoff":"<2026-01-01","specs":{}}
 for w,k,h in SPECS:
  key=f"w{w}_k{k:.1f}_h{h}"; out["specs"][key]={}
  for fold,s,t in FOLDS:
   start=pd.Timestamp(s,tz="UTC"); stop=pd.Timestamp(t,tz="UTC"); ps={x:y.loc[y.index<stop] for x,y in prices.items()}; fm={x:y.loc[y.index<stop] for x,y in funding.items()}; out["specs"][key][fold]={name:run(ps,fm,w,k,h,cost,start,stop) for name,cost in COSTS.items()}
 raw=json.dumps(out,sort_keys=True,separators=(",",":")); out["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); p=Path(a.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
