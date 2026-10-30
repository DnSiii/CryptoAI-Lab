#!/usr/bin/env python3
"""V98 Independent Phase225 — frozen abnormal-volume cross-sectional reversal. Training only 2023-2025."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT")
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(v,r,h) for v in (2.,3.) for r in (.015,.025) for h in (4,8)]; COSTS={"base":.0007,"severe":.0014,"supersevere":.0028}; CUT=pd.Timestamp("2026-01-01",tz="UTC")
def load_prices(root):
 out={}
 for a in ASSETS:
  x=pd.read_csv(root/f"{a}_1h.csv"); tc=next(c for c in x if c.lower() in ("timestamp","time","datetime","date","open_time")); x[tc]=pd.to_datetime(x[tc],utc=True); x=x.set_index(tc).sort_index(); x.columns=[c.lower() for c in x.columns]
  vc=next((c for c in x if c in ("volume","vol","base_volume")),None)
  if vc is None: raise RuntimeError(f"volume missing {a}")
  for c in ("open","close",vc): x[c]=pd.to_numeric(x[c],errors="raise")
  x=x.rename(columns={vc:"volume"}) if vc!="volume" else x
  if x.index.has_duplicates or x.index.max()>=CUT: raise RuntimeError(f"price firewall {a}")
  out[a]=x
 return out
def load_funding(root):
 out={}
 for a in ASSETS:
  d=pd.read_csv(root/f"{a}_funding.csv"); t=pd.to_datetime(d.fundingTime_utc,utc=True,format="mixed"); out[a]=pd.Series(pd.to_numeric(d.fundingRate).to_numpy(),index=t).sort_index()
  if out[a].index.has_duplicates or out[a].index.max()>=CUT: raise RuntimeError(f"funding firewall {a}")
 return out
def fund_cash(idx,s):
 d=s.index.ceil("1h"); d=pd.DatetimeIndex([z if z>t else z+pd.Timedelta(hours=1) for t,z in zip(s.index,d)]); return pd.Series(s.to_numpy(),index=d).groupby(level=0).sum().reindex(idx).fillna(0.)
def metrics(r):
 r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1 if len(eq) else r; pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
 return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.}
def run(px,fd,V,R,H,cost,start,stop):
 idx=px[ASSETS[0]].index; close=pd.DataFrame({a:px[a].close.reindex(idx) for a in ASSETS}); r6=close.pct_change(6,fill_method=None).shift(1); resid=r6.sub(r6.median(axis=1),axis=0)
 vr={a:px[a].volume.reindex(idx).shift(1)/px[a].volume.reindex(idx).shift(2).rolling(168,min_periods=168).median() for a in ASSETS}; pos=pd.DataFrame(0.,index=idx,columns=ASSETS); events=[]; until={a:-1 for a in ASSETS}
 for i,t in enumerate(idx):
  if t<start or t>=stop: continue
  elig=[a for a in ASSETS if i>=until[a] and np.isfinite(vr[a].iloc[i]) and vr[a].iloc[i]>=V and np.isfinite(resid[a].iloc[i]) and abs(resid[a].iloc[i])>=R]
  if not elig: continue
  # Mechanical capacity-aware fix preregistered in phase225_exposure_invariant_audit.md.
  # Existing cohorts keep their original weights; new entrants receive only free gross capacity.
  gross=float(pos.iloc[i].abs().sum()); capacity=max(0.,1.-gross)
  if capacity<=1e-12: continue
  w=capacity/len(elig)
  for a in elig:
   end=min(i+H,len(idx)); pos.iloc[i:end,pos.columns.get_loc(a)]=-np.sign(resid[a].iloc[i])*w; events.append((i,end,a)); until[a]=end
 if (pos.abs().sum(axis=1)>1+1e-12).any(): raise RuntimeError("gross exposure invariant")
 mask=(idx>=start)&(idx<stop); panel={}; contrib={}; fcon={}
 for a in ASSETS:
  w=pos[a]; rr=px[a].open.reindex(idx).pct_change(fill_method=None); turn=w.diff().abs().fillna(w.abs()); fund=-w.shift(1).fillna(0.)*fund_cash(idx,fd[a]); pnl=w.shift(1).fillna(0.)*rr.fillna(0.)-turn*cost+fund; z=pnl.loc[mask]; panel[a]=z; contrib[a]=float(z.sum()); fcon[a]=float(fund.loc[mask].sum())
 pp=pd.DataFrame(panel); port=pp.sum(axis=1); m=metrics(port); q=[]
 for j,e,a in events:
  if start<=idx[j]<stop and e<len(idx) and idx[e]<stop: q.append(float(pp[a].loc[idx[j]:idx[e]].sum()))
 q=np.asarray(q); m["trades"]=len(q); m["tail_definition"]="closed_trade_asset_attributed_including_exit_turnover"
 for n,p in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.5),("tail_p95",.95),("tail_p99",.99)): m[n]=float(np.quantile(q,p)) if len(q) else 0.
 m["worst_trade"]=float(q.min()) if len(q) else 0.; m["best_trade"]=float(q.max()) if len(q) else 0.; m["asset_pnl_contribution"]=contrib; den=sum(abs(x) for x in contrib.values()); m["max_asset_concentration"]=max(map(abs,contrib.values()))/den if den else 0.; m["funding_contribution"]=fcon
 btc=px["BTCUSDT"].close.reindex(idx).pct_change(168,fill_method=None).shift(1).loc[port.index]; regs={"bull":btc>0.03,"bear":btc<-0.03,"sideways":btc.abs()<=.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regs.items()}; return m
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="research/v98_independent/phase225_results.json"); a=ap.parse_args(); px=load_prices(Path(a.data_root)); fd=load_funding(Path(a.funding_root)); out={"phase":225,"family":"abnormal_volume_cross_sectional_reversal","cutoff":"<2026-01-01","specs":{}}
 for V,R,H in SPECS:
  key=f"v{V:.1f}_r{R:.3f}_h{H}"; out["specs"][key]={}
  for fold,s,t in FOLDS:
   st,sp=pd.Timestamp(s,tz="UTC"),pd.Timestamp(t,tz="UTC"); out["specs"][key][fold]={n:run(px,fd,V,R,H,c,st,sp) for n,c in COSTS.items()}
 raw=json.dumps(out,sort_keys=True,separators=(",",":")); out["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
