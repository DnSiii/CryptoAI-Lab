#!/usr/bin/env python3
"""CB preregistered synchronous seven-slot source economic falsification.
Official Clean-4 Dec2022-Dec2024 ONLY. 2025 holdout sealed. No system PnL.
"""
from __future__ import annotations
import argparse,hashlib,json,math
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from v98_staged_exit_viability_governor_v2 import (
    FEES,PARTICIPATION,capacity_units,prior_min_exit_window_quote)
from ba_ratio_reversion_governor import ENTRY_FRACTION

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
BOOKS=("Growth","Opportunity","RelativeValue","StressRecovery")
WARMUP=2160
EPOCH=336
YEAR_2024=9504
CAPACITY_SHARE=.25
BUDGETS={
    "BULL":np.array([1.40,1.20,1.00,.50]),
    "MIXED":np.array([1.00,.80,.80,.70]),
    "STRESS":np.array([.60,.30,.70,1.30]),
}
INITIAL_SHARES=(.70,.12,.10,.08)

def decision(close,rate,event,t):
    """All inputs through completed close t; no future feature data."""
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or c.shape!=r.shape or c.shape!=e.shape
        or t<WARMUP or t>=len(c) or not np.isfinite(c[:t+1]).all()
        or not np.isfinite(r[:t+1]).all() or not np.isfinite(e[:t+1]).all()
        or np.any(c[:t+1]<=0)):
        raise ValueError("CB_SOURCE_INPUT")
    lc=np.log(c[t-1008:t+1])
    ret=lambda span:lc[-1]-lc[-span-1]
    r24,r72,r168,r336,r1008=(ret(s) for s in (24,72,168,336,1008))
    hourly=np.diff(lc,axis=0)
    rms336=np.sqrt(np.mean(hourly[-336:]**2,axis=0))
    rms1008=np.sqrt(np.mean(hourly**2,axis=0))
    f336=np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
    f1008=np.sum(r[t-1007:t+1]*e[t-1007:t+1],axis=0)
    state=("STRESS" if np.median(r168)<0 else
           "BULL" if np.count_nonzero(r336>0)>=3 else "MIXED")
    w=np.zeros((4,4),dtype=float)
    score=(r1008-f1008)/np.maximum(rms336,.005)
    eligible=np.flatnonzero(r1008-f1008>0)
    if len(eligible):
        ranked=sorted(eligible,key=lambda j:(-score[j],j))[:2]
        inv=1./np.maximum(rms336[ranked],.005)
        w[0,ranked]=inv/inv.sum()
    accel=r72-(lc[-73]-lc[-145])
    eligible=np.flatnonzero((r336>0)&(accel>0))
    if len(eligible):
        j=int(sorted(eligible,key=lambda k:(-accel[k],k))[0])
        w[1,j]=1.
    rvscore=r336-f336
    rank=sorted(range(4),key=lambda j:(-rvscore[j],j))
    if rvscore[rank[0]]-rvscore[rank[-1]]>.04:
        w[2,rank[0]]=.5
        w[2,rank[-1]]=-.5
    if np.median(rms336)>np.median(rms1008):
        j=int(np.argmin(r72) if np.median(r72)<0 else np.argmax(r72))
        w[3,j]=-1. if np.median(r72)<0 else 1.
    if not np.isfinite(w).all() or np.any(np.sum(abs(w),axis=1)>1.+1e-12):
        raise ValueError("CB_SOURCE_WEIGHT")
    return w,state,{"past_r72":r72.tolist(),"past_r336":r336.tolist(),
                    "past_f336":f336.tolist(),"past_vol336":rms336.tolist()}

def economic_episode(frames,t,w,state):
    o,h,l,c,q,r,e,ml,mh=frames
    entry_t=t+1;exit_t=t+EPOCH+1
    if exit_t>=len(o):raise ValueError("CB_EXIT_OUT_OF_RANGE")
    entry=o[entry_t].astype(float)
    exit_price=o[exit_t].astype(float)
    out=[]
    # Source-only ledger: one unit gross notional per active book; no system
    # compounding, no invented fills, no claims about executable NAV.
    for i in range(4):
        weight=w[i]
        active=bool(np.any(weight))
        units=np.divide(weight,entry)
        price=float(np.dot(units,exit_price-entry))
        funding=0.;events=0
        for k in range(entry_t,exit_t):
            if not np.any(e[k]*abs(units)):continue
            obligation=units*r[k]*e[k]
            mark=np.where(obligation>=0,mh[k],ml[k])
            funding-=float(np.dot(obligation,mark))
            events+=int(np.count_nonzero(e[k]*abs(units)))
        cost={tier:float((fee+slip)*np.dot(abs(units),entry+exit_price))
              for tier,(fee,slip) in FEES.items()}
        net={tier:float(price+funding-cost[tier]) for tier in FEES}
        if active:
            adverse=np.where(units>=0,l[entry_t:exit_t],h[entry_t:exit_t])
            adverse_path=(adverse-entry)@units
            worst=float(np.min(adverse_path))
            prior_q=prior_min_exit_window_quote(q,entry_t)*CAPACITY_SHARE
            max_units=ENTRY_FRACTION*capacity_units(entry,prior_q)
            per_asset_capacity=np.where(abs(weight)>0,
                max_units*entry/np.maximum(abs(weight),1e-100),np.inf)
            entry_quote_limit=PARTICIPATION*CAPACITY_SHARE*q[t]
            per_asset_quote=np.where(abs(weight)>0,
                entry_quote_limit/np.maximum(abs(weight),1e-100),np.inf)
            capacity=float(min(np.min(per_asset_capacity),np.min(per_asset_quote)))
        else:
            worst=0.;capacity=0.
        if not np.isfinite([price,funding,*cost.values(),*net.values(),worst,capacity]).all() or capacity<0:
            raise ValueError("CB_SOURCE_NONFINITE")
        out.append({"book":BOOKS[i],"active":active,
                    "weights":weight.tolist(),"entry_open":entry.tolist(),
                    "exit_open":exit_price.tolist(),"price_pnl_per_gross_usd":price,
                    "native_funding_per_gross_usd":funding,
                    "native_funding_asset_events":events,
                    "roundtrip_cost_per_gross_usd":cost,
                    "net_per_gross_usd":net,
                    "worst_intrahold_adverse_per_gross_usd":worst,
                    "prior_only_max_entry_notional_usd":capacity})
    return {"decision_t":t,"entry_t":entry_t,"exit_t":exit_t,
            "entry_year":"2023" if entry_t<YEAR_2024 else "2024",
            "regime":state,"books":out}

def run():
    frames,manifest=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    episodes=[]
    for t in range(WARMUP,HOURS-EPOCH-1,EPOCH):
        w,state,_=decision(c,r,e,t)
        episodes.append(economic_episode(frames,t,w,state))
    annual={}
    for yr in ("2023","2024"):
        annual[yr]={}
        for book in BOOKS:
            rows=[b for ep in episodes if ep["entry_year"]==yr
                  for b in ep["books"] if b["book"]==book and b["active"]]
            nets={tier:float(sum(b["net_per_gross_usd"][tier] for b in rows))
                  for tier in FEES}
            annual[yr][book]={
                "active_episodes":len(rows),
                "net_per_gross_usd_episode_sum":nets,
                "native_funding_sum":float(sum(b["native_funding_per_gross_usd"] for b in rows)),
                "positive_severe_episodes":sum(b["net_per_gross_usd"]["severe"]>0 for b in rows),
                "worst_intrahold_adverse":min((b["worst_intrahold_adverse_per_gross_usd"] for b in rows),default=0.),
                "median_prior_only_capacity_usd":float(np.median([b["prior_only_max_entry_notional_usd"] for b in rows])) if rows else 0.,
                "asset_active_counts":{asset:sum(abs(b["weights"][j])>0 for b in rows)
                    for j,asset in enumerate(ASSETS)},
            }
    gates={book:all(annual[yr][book]["active_episodes"]>=4 and
                    annual[yr][book]["net_per_gross_usd_episode_sum"]["severe"]>0
                    for yr in annual) for book in BOOKS}
    return {"architecture":"CB_SOURCE_ONLY","historical_training_only":True,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "system_pnl_computed":False,"portfolio_cagr_claimed":False,
            "trading_authorized":False,"source_manifest_sha256":hashlib.sha256(
                json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            "epoch_hours":EPOCH,"episode_count":len(episodes),
            "annual":annual,"source_gates":gates,"episodes":episodes,
            "decision":("PASS_CB_SOURCE_ONLY_REQUIRES_FULL_SEVEN_SLOT_INTEGRATION"
                        if all(gates.values()) else "REJECT_CB_SOURCE_ECONOMICS_NO_RESCUE")}

def static_check():
    n=2800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])
                 +.05*np.sin(t[:,None]/100.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    before=decision(c,r,e,2400)
    changed=c.copy();changed[2401:]*=1.5
    assert np.array_equal(before[0],decision(changed,r,e,2400)[0])
    assert before[1]==decision(changed,r,e,2400)[1]
    assert np.allclose(np.sum(abs(before[0]),axis=1),
                       np.minimum(1,np.sum(abs(before[0]),axis=1)))
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    args=p.parse_args()
    assert static_check()
    result=run()
    with open(args.output,"w") as f:json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)
    print("CB_SOURCE",result["decision"],"episodes",result["episode_count"])
    for yr,books in result["annual"].items():
        for book,row in books.items():
            print("CB_YEAR",yr,book,"active",row["active_episodes"],
                  "severe_net",round(row["net_per_gross_usd_episode_sum"]["severe"],9))
    raise SystemExit(0 if all(result["source_gates"].values()) else 2)
