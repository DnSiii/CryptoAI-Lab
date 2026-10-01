#!/usr/bin/env python3
"""V98 Independent Phase205 — preregistered BTC→alt lead/lag underreaction.
Training-only. Never reads validation/final holdout. All entry state is available through t-1.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

DRIVER="BTCUSDT"
RESPONDERS=("ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
ASSETS=(DRIVER,)+RESPONDERS
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(w,z,h) for w in (3,6) for z in (1.5,2.0) for h in (3,6)]
COSTS={"base":0.0007,"severe":0.0014,"supersevere":0.0028}
SCALE_WINDOW=168
UNDERREACTION_MAX=0.50


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


def metrics(r:pd.Series):
    r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1
    pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
    return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.}


def run(data,w,z,hold,cost):
    btc=data[DRIVER]["close"].astype(float)
    btc_lr=np.log(btc).diff()
    # shift(1) freezes the volatility estimate through t-1; impulse is also shifted before entry use.
    scale=btc_lr.rolling(SCALE_WINDOW,min_periods=SCALE_WINDOW).std().shift(1)*np.sqrt(w)
    btc_imp=(btc/btc.shift(w)-1).shift(1)
    norm=(btc_imp/scale.replace(0,np.nan))
    pieces=[]; by_asset={}; trade_pnls=[]
    for a in RESPONDERS:
        d=data[a]; c=d["close"].astype(float); ret=c.pct_change().fillna(0)
        alt_imp=(c/c.shift(w)-1).shift(1).reindex(d.index)
        b=btc_imp.reindex(d.index); n=norm.reindex(d.index)
        same=(np.sign(alt_imp)==np.sign(b)) & b.ne(0)
        ratio=(alt_imp.abs()/b.abs()).replace([np.inf,-np.inf],np.nan)
        long=(n>=z)&(b>0)&(alt_imp>0)&same&(ratio<=UNDERREACTION_MAX)
        short=(n<=-z)&(b<0)&(alt_imp<0)&same&(ratio<=UNDERREACTION_MAX)
        pos=pd.Series(0.,index=d.index); entries=[]; cooldown=0
        for i in range(len(d)):
            if cooldown>0:
                cooldown-=1; continue
            direction=1. if bool(long.iloc[i]) else (-1. if bool(short.iloc[i]) else 0.)
            if direction:
                pos.iloc[i:min(i+hold,len(d))]=direction; entries.append(i); cooldown=hold
        turnover=pos.diff().abs().fillna(pos.abs())
        funding=d["funding_rate"].astype(float).fillna(0) if "funding_rate" in d else pd.Series(0.,index=d.index)
        pnl=pos.shift(1).fillna(0)*ret-turnover*cost-pos.shift(1).fillna(0)*funding
        # Complete trade PnL includes entry cost, held returns/funding, and exit cost when present.
        for i in entries:
            j=min(i+hold,len(pnl)-1); trade_pnls.append(float(pnl.iloc[i:j+1].sum()))
        by_asset[a]=float((1+pnl).prod()-1); pieces.append(pnl.rename(a))
    panel=pd.concat(pieces,axis=1).fillna(0); port=panel.mean(axis=1); m=metrics(port)
    denom=sum(abs(x) for x in by_asset.values()); m["asset_returns"]=by_asset; m["max_asset_concentration"]=float(max(abs(x) for x in by_asset.values())/denom) if denom else 0.
    q=np.array(trade_pnls,float); m["trades"]=int(len(q))
    for name,p in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.50),("tail_p95",.95),("tail_p99",.99)):
        m[name]=float(np.quantile(q,p)) if len(q) else 0.
    m["worst_trade"]=float(q.min()) if len(q) else 0.; m["best_trade"]=float(q.max()) if len(q) else 0.
    trend=(btc.reindex(port.index).pct_change(168).shift(1)); regimes={"bull":trend>0.03,"bear":trend<-0.03,"sideways":trend.abs()<=0.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regimes.items()}
    return m


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--out",default="reports/v98_independent_phase205_results.json"); args=ap.parse_args(); data=load(Path(args.data_root))
    result={"phase":205,"family":"btc_alt_leadlag_underreaction","cutoff":"<2026-01-01","driver":DRIVER,"responders":list(RESPONDERS),"scale_window_hours":SCALE_WINDOW,"underreaction_max":UNDERREACTION_MAX,"specs":{}}
    for w,z,h in SPECS:
        key=f"w{w}_z{str(z).replace('.','p')}_h{h}"; result["specs"][key]={}
        for fold,s,t in FOLDS:
            subset={a:d.loc[(d.index>=s)&(d.index<t)] for a,d in data.items()}; result["specs"][key][fold]={name:run(subset,w,z,h,cost) for name,cost in COSTS.items()}
    raw=json.dumps(result,sort_keys=True,separators=(",",":")); result["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); Path(args.out).parent.mkdir(parents=True,exist_ok=True); Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")

if __name__=="__main__": main()
