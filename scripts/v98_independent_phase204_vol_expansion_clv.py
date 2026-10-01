#!/usr/bin/env python3
"""V98 Independent Phase204 — preregistered volatility-expansion + CLV continuation.
Training-only. Never reads validation/final holdout. Entry state is computed through t-1.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(w,x,h) for w in (12,24) for x in (1.25,1.75) for h in (3,6)]
COSTS={"base":0.0007,"severe":0.0014,"supersevere":0.0028}
BASELINE=168; CLV_THR=0.5

def load(root:Path):
    out={}
    for a in ASSETS:
        p=root/f"{a}_1h.csv"; d=pd.read_csv(p)
        tc=next(c for c in d.columns if c.lower() in ("timestamp","time","datetime","date","open_time"))
        d[tc]=pd.to_datetime(d[tc],utc=True); d=d.set_index(tc).sort_index(); d.columns=[c.lower() for c in d.columns]
        if d.index.max()>=pd.Timestamp("2026-01-01",tz="UTC"): raise RuntimeError(f"cutoff violation {a}")
        if not d.index.is_monotonic_increasing or d.index.has_duplicates: raise RuntimeError(f"index invariant {a}")
        out[a]=d
    return out

def metrics(r):
    r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1; pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
    return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.}

def run(data,w,exp_thr,hold,cost):
    pieces=[]; by_asset={}; trade_pnls=[]
    for a,d in data.items():
        c=d["close"].astype(float); hi=d["high"].astype(float); lo=d["low"].astype(float); ret=c.pct_change().fillna(0); lr=np.log(c).diff()
        rv=lr.rolling(w,min_periods=w).std(); baseline=rv.rolling(BASELINE,min_periods=BASELINE).median().shift(1); expansion=rv/baseline.replace(0,np.nan)
        rng=(hi-lo).replace(0,np.nan); clv=((2*c-hi-lo)/rng).clip(-1,1).fillna(0); disp=c/c.shift(w)-1
        long=((expansion>=exp_thr)&(clv>=CLV_THR)&(disp>0)).shift(1).fillna(False)
        short=((expansion>=exp_thr)&(clv<=-CLV_THR)&(disp<0)).shift(1).fillna(False)
        pos=pd.Series(0.,index=d.index); cooldown=0
        for i in range(len(d)):
            if cooldown>0: cooldown-=1; continue
            direction=1. if bool(long.iloc[i]) else (-1. if bool(short.iloc[i]) else 0.)
            if direction:
                pos.iloc[i:min(i+hold,len(d))]=direction; cooldown=hold
        turnover=pos.diff().abs().fillna(pos.abs()); funding=d["funding_rate"].astype(float).fillna(0) if "funding_rate" in d else pd.Series(0.,index=d.index)
        pnl=pos.shift(1).fillna(0)*ret-turnover*cost-pos.shift(1).fillna(0)*funding
        by_asset[a]=float((1+pnl).prod()-1); pieces.append(pnl.rename(a)); starts=pos.ne(0)&pos.shift(1).fillna(0).eq(0); trade_pnls.extend(pnl[starts].tolist())
    panel=pd.concat(pieces,axis=1).fillna(0); port=panel.mean(axis=1); m=metrics(port); denom=sum(abs(x) for x in by_asset.values())
    m["asset_returns"]=by_asset; m["max_asset_concentration"]=float(max(abs(x) for x in by_asset.values())/denom) if denom else 0.; q=np.array(trade_pnls,float); m["tail_p01"]=float(np.quantile(q,.01)) if len(q) else 0.; m["tail_p99"]=float(np.quantile(q,.99)) if len(q) else 0.; m["trades"]=len(q)
    btc=data["BTCUSDT"]["close"].reindex(port.index).ffill(); trend=btc.pct_change(168).shift(1); regimes={"bull":trend>0.03,"bear":trend<-0.03,"sideways":trend.abs()<=0.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regimes.items()}
    return m

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--out",default="reports/v98_independent_phase204_results.json"); args=ap.parse_args(); data=load(Path(args.data_root))
    result={"phase":204,"family":"relative_volatility_expansion_clv_continuation","cutoff":"<2026-01-01","baseline_hours":BASELINE,"clv_threshold":CLV_THR,"specs":{}}
    for w,x,h in SPECS:
        key=f"rv{w}_x{int(x*100)}_h{h}"; result["specs"][key]={}
        for fold,s,t in FOLDS:
            subset={a:d.loc[(d.index>=s)&(d.index<t)] for a,d in data.items()}; result["specs"][key][fold]={name:run(subset,w,x,h,cost) for name,cost in COSTS.items()}
    raw=json.dumps(result,sort_keys=True,separators=(",",":")); result["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); Path(args.out).parent.mkdir(parents=True,exist_ok=True); Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
