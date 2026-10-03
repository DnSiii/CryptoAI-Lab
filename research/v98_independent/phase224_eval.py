#!/usr/bin/env python3
"""V98 Independent Phase224 — preregistered realized-funding dislocation convergence.
Training only: 2023-2025. 2026+ is a hard firewall.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

ASSETS=("ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
ALL=("BTCUSDT",)+ASSETS
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(L,z,h) for L in (63,126) for z in (1.5,2.5) for h in (4,8)]
COSTS={"base":.0007,"severe":.0014,"supersevere":.0028}
CUTOFF=pd.Timestamp("2026-01-01",tz="UTC")

def load_prices(root):
 out={}
 for a in ALL:
  x=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in x.columns if c.lower() in ("timestamp","time","datetime","date","open_time"))
  x[tc]=pd.to_datetime(x[tc],utc=True,errors="raise"); x=x.set_index(tc).sort_index(); x.columns=[c.lower() for c in x.columns]
  x["open"]=pd.to_numeric(x.open,errors="raise"); x["close"]=pd.to_numeric(x.close,errors="raise")
  if x.index.has_duplicates or not x.index.is_monotonic_increasing or x.index.max()>=CUTOFF: raise RuntimeError(f"price firewall {a}")
  out[a]=x
 return out

def load_funding(root):
 out={}
 for a in ALL:
  d=pd.read_csv(root/f"{a}_funding.csv")
  req={"fundingTime_utc","fundingRate"}
  if not req.issubset(d.columns): raise RuntimeError(f"funding schema {a}")
  t=pd.to_datetime(d.fundingTime_utc,utc=True,errors="raise",format="mixed"); r=pd.to_numeric(d.fundingRate,errors="raise")
  x=pd.DataFrame({"rate":r.to_numpy()},index=t).sort_index()
  if x.index.has_duplicates or not x.index.is_monotonic_increasing or x.index.max()>=CUTOFF: raise RuntimeError(f"funding firewall {a}")
  out[a]=x
 return out

def signal_series(index,f,L):
 # Current realized settlement is excluded from its reference window; decision is first hourly open strictly after settlement.
 r=f.rate; mu=r.shift(1).rolling(L,min_periods=L).mean(); sd=r.shift(1).rolling(L,min_periods=L).std(ddof=1); z=(r-mu)/sd
 decision=f.index.ceil("1h"); decision=pd.DatetimeIndex([d if d>t else d+pd.Timedelta(hours=1) for t,d in zip(f.index,decision)])
 s=pd.Series(z.to_numpy(),index=decision).groupby(level=0).last()
 return s.reindex(index)

def funding_cash(index,f):
 # Settlement inside (previous open, current open] is booked at current-open PnL timestamp.
 decision=f.index.ceil("1h"); decision=pd.DatetimeIndex([d if d>t else d+pd.Timedelta(hours=1) for t,d in zip(f.index,decision)])
 return pd.Series(f.rate.to_numpy(),index=decision).groupby(level=0).sum().reindex(index).fillna(0.)

def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1 if len(eq) else r; pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
 return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.}

def run(prices,funding,L,thr,hold,cost,start,stop):
 idx=prices["BTCUSDT"].index; sig={a:signal_series(idx,funding[a],L) for a in ASSETS}; pos=pd.DataFrame(0.,index=idx,columns=ASSETS); events=[]; until={a:-1 for a in ASSETS}
 for i,t in enumerate(idx):
  if t<start or t>=stop: continue
  eligible=[]
  for a in ASSETS:
   if i<until[a]: continue
   zz=sig[a].iloc[i]
   if np.isfinite(zz) and abs(zz)>=thr: eligible.append((a,-int(np.sign(zz))))
  if not eligible: continue
  for a,side in eligible:
   end=min(i+hold,len(idx)); pos.iloc[i:end,pos.columns.get_loc(a)]=side; events.append((i,end,a)); until[a]=end
 n=pos.abs().sum(axis=1); w=pos.div(n.where(n>0,1.),axis=0)
 if (w.abs().sum(axis=1)>1+1e-12).any(): raise RuntimeError("gross exposure invariant")
 mask=(idx>=start)&(idx<stop); panel={}; contrib={}; fcon={}
 for a in ASSETS:
  ww=w[a]; rr=prices[a].open.reindex(idx).pct_change(fill_method=None); turn=ww.diff().abs().fillna(ww.abs()); fc=funding_cash(idx,funding[a]); fund=-ww.shift(1).fillna(0.)*fc
  pnl=ww.shift(1).fillna(0.)*rr.fillna(0.)-turn*cost+fund; z=pnl.loc[mask]; panel[a]=z; contrib[a]=float(z.sum()); fcon[a]=float(fund.loc[mask].sum())
 pp=pd.DataFrame(panel); port=pp.sum(axis=1); m=metrics(port); trades=[]
 for j,e,a in events:
  if start<=idx[j]<stop and e<len(idx) and idx[e]<stop: trades.append(float(pp[a].loc[idx[j]:idx[e]].sum()))
 q=np.asarray(trades,float); m["trades"]=len(q); m["tail_definition"]="closed_trade_asset_attributed_including_exit_turnover"
 for name,p in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[name]=float(np.quantile(q,p)) if len(q) else 0.
 m["worst_trade"]=float(q.min()) if len(q) else 0.; m["best_trade"]=float(q.max()) if len(q) else 0.; m["asset_pnl_contribution"]=contrib; den=sum(abs(v) for v in contrib.values()); m["max_asset_concentration"]=max((abs(v) for v in contrib.values()),default=0.)/den if den else 0.; m["funding_contribution"]=fcon
 btc168=prices["BTCUSDT"].close.reindex(idx).pct_change(168,fill_method=None).shift(1).loc[port.index]; regs={"bull":btc168>0.03,"bear":btc168<-0.03,"sideways":btc168.abs()<=0.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regs.items()}; return m

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="research/v98_independent/phase224_results.json"); a=ap.parse_args()
 prices=load_prices(Path(a.data_root)); funding=load_funding(Path(a.funding_root)); assert len(SPECS)==8
 out={"phase":224,"family":"realized_funding_dislocation_convergence","cutoff":"<2026-01-01","specs":{}}
 for L,z,h in SPECS:
  key=f"L{L}_z{z:.1f}_h{h}"; out["specs"][key]={}
  for fold,s,t in FOLDS:
   start=pd.Timestamp(s,tz="UTC"); stop=pd.Timestamp(t,tz="UTC"); ps={x:y.loc[y.index<stop] for x,y in prices.items()}; fm={x:y.loc[y.index<stop] for x,y in funding.items()}; out["specs"][key][fold]={n:run(ps,fm,L,z,h,c,start,stop) for n,c in COSTS.items()}
 raw=json.dumps(out,sort_keys=True,separators=(",",":")); out["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); p=Path(a.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
