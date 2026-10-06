#!/usr/bin/env python3
"""V98 Independent Phase242 — preregistered illiquidity/price-impact reversal. Training only 2023-2025."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=tuple((iw,1,H) for iw in (168,336) for H in (4,8))
COSTS={"base":.0007,"severe":.0014,"supersevere":.0028}; CUT=pd.Timestamp("2026-01-01",tz="UTC")
def load_prices(root):
 out={}
 for a in ASSETS:
  x=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in x if c.lower() in ("timestamp","time","datetime","date","open_time")); x[tc]=pd.to_datetime(x[tc],utc=True); x=x.set_index(tc).sort_index(); x.columns=[c.lower() for c in x.columns]
  q=next((c for c in x.columns if c in ("quote_volume","quote_asset_volume","quotevolume")),None)
  if q is None: raise RuntimeError(f"quote-volume missing {a}")
  for c in ("open","close",q): x[c]=pd.to_numeric(x[c],errors="raise")
  x=x.rename(columns={q:"quote_volume"})
  if x.index.has_duplicates or not x.index.is_monotonic_increasing or x.index.max()>=CUT: raise RuntimeError(f"price firewall {a}")
  if (x.quote_volume<0).any(): raise RuntimeError(f"negative quote-volume {a}")
  out[a]=x
 return out
def load_funding(root):
 out={}
 for a in ASSETS:
  d=pd.read_csv(root/f"{a}_funding.csv"); t=pd.to_datetime(d.fundingTime_utc,utc=True,format="mixed"); out[a]=pd.Series(pd.to_numeric(d.fundingRate).to_numpy(),index=t).sort_index()
  if out[a].index.has_duplicates or not out[a].index.is_monotonic_increasing or out[a].index.max()>=CUT: raise RuntimeError(f"funding firewall {a}")
 return out
def fund_cash(idx,s):
 d=s.index.ceil("1h"); d=pd.DatetimeIndex([z if z>t else z+pd.Timedelta(hours=1) for t,z in zip(s.index,d)])
 return pd.Series(s.to_numpy(),index=d).groupby(level=0).sum().reindex(idx).fillna(0.)
def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1 if len(eq) else r; pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
 return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.,"worst_day":float(days.min()) if len(days) else 0.,"best_day":float(days.max()) if len(days) else 0.}
def features(px,iw):
 idx=px["BTCUSDT"].index; op=pd.DataFrame({a:px[a].open.reindex(idx) for a in ASSETS}); score=pd.DataFrame(index=idx,columns=ASSETS,dtype=float)
 for a in ASSETS:
  cl=px[a].close.reindex(idx); qv=px[a].quote_volume.reindex(idx); r1=cl.pct_change(fill_method=None)
  impact=r1.abs()/qv.clip(lower=1e-12); li=np.log1p(impact)
  med=li.rolling(iw,min_periods=iw).median().shift(1); mad=li.rolling(iw,min_periods=iw).apply(lambda x: float(np.median(np.abs(x-np.median(x)))),raw=True).shift(1).clip(lower=1e-9)
  norm=(li-med)/mad; score[a]=-np.sign(r1)*norm
 return op,score
def run(px,fd,iw,k,H,cost,start,stop):
 op,score=features(px,iw); idx=op.index; rr=op.pct_change(fill_method=None); pos=pd.DataFrame(0.,index=idx,columns=ASSETS); events=[]
 for i,t in enumerate(idx):
  if i<1 or t<start or t>=stop: continue
  s=score.iloc[i-1].dropna()
  if len(s)<2*k: continue
  ranked=sorted(((float(v),a) for a,v in s.items()),key=lambda z:(z[0],z[1])); shorts=[a for _,a in ranked[:k]]; longs=[a for _,a in ranked[-k:]]; end=min(i+H,len(idx)); w=1./(2*k)
  for a in longs: pos.iloc[i:end,pos.columns.get_loc(a)]+=w; events.append((i,end,a,1))
  for a in shorts: pos.iloc[i:end,pos.columns.get_loc(a)]-=w; events.append((i,end,a,-1))
 gross=pos.abs().sum(axis=1); pos=pos.div(gross.where(gross>1,1),axis=0)
 if (pos.abs().sum(axis=1)>1+1e-12).any(): raise RuntimeError("gross exposure invariant")
 mask=(idx>=start)&(idx<stop); panel={}; contrib={}; fcon={}; total_turn=0.
 for a in ASSETS:
  w=pos[a]; turn=w.diff().abs().fillna(w.abs()); fund=-w.shift(1).fillna(0.)*fund_cash(idx,fd[a]); pnl=w.shift(1).fillna(0.)*rr[a].fillna(0.)-turn*cost+fund; z=pnl.loc[mask]; panel[a]=z; contrib[a]=float(z.sum()); fcon[a]=float(fund.loc[mask].sum()); total_turn+=float(turn.loc[mask].sum())
 port=pd.DataFrame(panel).sum(axis=1); m=metrics(port); m["turnover_l1"]=total_turn; m["signal_events"]=len([e for e in events if start<=idx[e[0]]<stop])
 daily=port.resample("1D").sum()
 for n,p in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[n]=float(daily.quantile(p)) if len(daily) else 0.
 m["tail_frequency"]="daily"; m["asset_pnl_contribution"]=contrib; den=sum(abs(x) for x in contrib.values()); m["max_asset_concentration"]=max(map(abs,contrib.values()))/den if den else 0.; m["funding_contribution"]=fcon
 br=op["BTCUSDT"].pct_change(168,fill_method=None).shift(1).loc[port.index]; regs={"bull":br>0.03,"bear":br<-0.03,"sideways":br.abs()<=.03}; m["regimes"]={n:metrics(port[v.fillna(False)]) for n,v in regs.items()}
 return m
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="research/v98_independent/phase242_results.json"); a=ap.parse_args()
 px=load_prices(Path(a.data_root)); fd=load_funding(Path(a.funding_root)); out={"phase":242,"family":"illiquidity_price_impact_reversal","cutoff":"<2026-01-01","information_set":"decision open(t) uses normalized impact(t-1) and sign(r1(t-1)); impact normalization history ends at u-1","specs":{}}
 if len(SPECS)!=4 or len(set(SPECS))!=4 or any(k!=1 for _,k,_ in SPECS): raise RuntimeError("frozen grid invariant")
 for iw,k,H in SPECS:
  key=f"pir_iw{iw}_k{k}_h{H}"; out["specs"][key]={}
  for fold,s,t in FOLDS:
   st,sp=pd.Timestamp(s,tz="UTC"),pd.Timestamp(t,tz="UTC"); out["specs"][key][fold]={n:run(px,fd,iw,k,H,c,st,sp) for n,c in COSTS.items()}
 raw=json.dumps(out,sort_keys=True,separators=(",",":")); out["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
