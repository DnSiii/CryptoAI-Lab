#!/usr/bin/env python3
"""V98 Independent Phase206 — preregistered funding-dislocation mean reversion.
Training-only. Funding snapshot is frozen under research/v98_independent/data/phase206_funding.
Signals use only funding known through t-1; validation/final holdout is never read.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT")
FOLDS=(("2023","2023-01-01","2024-01-01"),("2024","2024-01-01","2025-01-01"),("2025","2025-01-01","2026-01-01"))
SPECS=[(lb,z,h) for lb in (30,90) for z in (1.5,2.5) for h in (8,24)]
COSTS={"base":0.0007,"severe":0.0014,"supersevere":0.0028}
CUTOFF=pd.Timestamp("2026-01-01",tz="UTC")


def load_prices(root:Path):
    out={}
    for a in ASSETS:
        d=pd.read_csv(root/f"{a}_1h.csv")
        tc=next(c for c in d.columns if c.lower() in ("timestamp","time","datetime","date","open_time"))
        d[tc]=pd.to_datetime(d[tc],utc=True,errors="raise"); d=d.set_index(tc).sort_index(); d.columns=[c.lower() for c in d.columns]
        if d.index.max()>=CUTOFF: raise RuntimeError(f"price cutoff violation {a}")
        if not d.index.is_monotonic_increasing or d.index.has_duplicates: raise RuntimeError(f"price index invariant {a}")
        out[a]=d
    if set(out)!=set(ASSETS): raise RuntimeError("frozen universe mismatch")
    return out


def load_funding(root:Path):
    out={}
    for a in ASSETS:
        d=pd.read_csv(root/f"{a}_funding.csv")
        t=pd.to_datetime(d["fundingTime_utc"],utc=True,errors="raise"); r=pd.to_numeric(d["fundingRate"],errors="raise")
        x=pd.DataFrame({"rate":r.to_numpy()},index=t).sort_index()
        if x.index.max()>=CUTOFF: raise RuntimeError(f"funding cutoff violation {a}")
        if not x.index.is_monotonic_increasing or x.index.has_duplicates: raise RuntimeError(f"funding index invariant {a}")
        out[a]=x
    return out


def metrics(r:pd.Series):
    r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1
    pos=r[r>0].sum(); neg=-r[r<0].sum(); days=r.resample("1D").sum() if len(r) else r
    return {"return":float(eq.iloc[-1]-1) if len(eq) else 0.,"max_drawdown":float(dd.min()) if len(dd) else 0.,"profit_factor":float(pos/neg) if neg>0 else (999. if pos>0 else 0.),"payoff":float(r[r>0].mean()/(-r[r<0].mean())) if (r>0).any() and (r<0).any() else 0.,"win_rate":float((r>0).mean()) if len(r) else 0.,"positive_days":float((days>0).mean()) if len(days) else 0.}


def causal_z(hourly_index:pd.DatetimeIndex,f:pd.DataFrame,lookback_days:int):
    # Time-window rolling statistics are computed only at realized funding timestamps.
    s=f["rate"]
    mu=s.rolling(f"{lookback_days}D",min_periods=20).mean()
    sd=s.rolling(f"{lookback_days}D",min_periods=20).std(ddof=1)
    z=(s-mu)/sd.replace(0,np.nan)
    obs=pd.DataFrame({"funding_z":z,"source_ts":s.index},index=s.index).dropna()
    q=pd.DataFrame({"cutoff":hourly_index-pd.Timedelta(hours=1)},index=hourly_index)
    m=pd.merge_asof(q.reset_index(names="bar_ts").sort_values("cutoff"),obs.reset_index(names="obs_ts").sort_values("obs_ts"),left_on="cutoff",right_on="obs_ts",direction="backward")
    if ((m["source_ts"].notna()) & (m["source_ts"]>m["cutoff"])).any(): raise RuntimeError("funding causality violation")
    return pd.Series(m["funding_z"].to_numpy(),index=m["bar_ts"]), pd.Series(m["source_ts"].to_numpy(),index=m["bar_ts"])


def hourly_funding(index:pd.DatetimeIndex,f:pd.DataFrame):
    # Event at 00:00:00.006 belongs to price interval (00:00,01:00]; no future fill/imputation.
    bucket=f.index.ceil("1h")
    x=pd.Series(f["rate"].to_numpy(),index=bucket).groupby(level=0).sum()
    return x.reindex(index).fillna(0.)


def run(prices,funding,lookback,zthr,hold,cost):
    pieces=[]; by_asset={}; trade_pnls=[]; causality_max_lag_h=[]
    for a in ASSETS:
        d=prices[a]; close=d["close"].astype(float); ret=close.pct_change().fillna(0.)
        z,src=causal_z(d.index,funding[a],lookback)
        known=src.notna(); lag=((pd.Series(d.index,index=d.index)-src)/pd.Timedelta(hours=1))[known]
        if len(lag): causality_max_lag_h.append(float(lag.max()))
        long=z<=-zthr; short=z>=zthr
        pos=pd.Series(0.,index=d.index); entries=[]; i=0
        while i<len(d):
            direction=1. if bool(long.iloc[i]) else (-1. if bool(short.iloc[i]) else 0.)
            if direction:
                end=min(i+hold,len(d)); pos.iloc[i:end]=direction; entries.append((i,end,direction)); i=end
            else: i+=1
        turnover=pos.diff().abs().fillna(pos.abs())
        hf=hourly_funding(d.index,funding[a])
        pnl=pos.shift(1).fillna(0.)*ret - turnover*cost - pos.shift(1).fillna(0.)*hf
        # Ledger reconciles complete trade PnL: entry cost + held price/funding + exit cost when available.
        for i,end,_ in entries:
            j=min(end,len(pnl)-1); trade_pnls.append(float(pnl.iloc[i:j+1].sum()))
        by_asset[a]=float((1+pnl).prod()-1); pieces.append(pnl.rename(a))
    panel=pd.concat(pieces,axis=1).fillna(0.); port=panel.mean(axis=1); m=metrics(port)
    denom=sum(abs(x) for x in by_asset.values()); m["asset_returns"]=by_asset; m["max_asset_concentration"]=float(max(abs(x) for x in by_asset.values())/denom) if denom else 0.
    q=np.asarray(trade_pnls,float); m["trades"]=int(len(q)); m["trade_ledger_sum"]=float(q.sum()) if len(q) else 0.
    for name,p in (("tail_p01",.01),("tail_p05",.05),("tail_p50",.50),("tail_p95",.95),("tail_p99",.99)): m[name]=float(np.quantile(q,p)) if len(q) else 0.
    m["worst_trade"]=float(q.min()) if len(q) else 0.; m["best_trade"]=float(q.max()) if len(q) else 0.; m["max_signal_source_lag_hours"]=max(causality_max_lag_h) if causality_max_lag_h else None
    btc=prices["BTCUSDT"]["close"].reindex(port.index); trend=btc.pct_change(168).shift(1)
    regimes={"bull":trend>0.03,"bear":trend<-0.03,"sideways":trend.abs()<=0.03}; m["regimes"]={k:metrics(port[v.fillna(False)]) for k,v in regimes.items()}
    return m


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-root",default="data/canonical"); ap.add_argument("--funding-root",default="research/v98_independent/data/phase206_funding"); ap.add_argument("--out",default="reports/v98_independent_phase206_results.json"); args=ap.parse_args()
    prices=load_prices(Path(args.data_root)); funding=load_funding(Path(args.funding_root))
    result={"phase":206,"family":"funding_dislocation_mean_reversion","cutoff":"<2026-01-01","assets":list(ASSETS),"specs":{}}
    for lb,z,h in SPECS:
        key=f"lb{lb}d_z{str(z).replace('.','p')}_h{h}"; result["specs"][key]={}
        for fold,s,t in FOLDS:
            ps={a:d.loc[(d.index>=s)&(d.index<t)] for a,d in prices.items()}
            # Keep pre-fold funding history for causal rolling z; evaluation prices remain strictly inside fold.
            result["specs"][key][fold]={name:run(ps,funding,lb,z,h,c) for name,c in COSTS.items()}
    raw=json.dumps(result,sort_keys=True,separators=(",",":")); result["deterministic_payload_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
    p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")

if __name__=="__main__": main()
