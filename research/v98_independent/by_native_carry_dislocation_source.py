#!/usr/bin/env python3
"""V98 BY: preregistered source-level directional native-carry falsification.
NOT a portfolio backtest or an approved seven-slot engine. No 2025 reads.
"""
from __future__ import annotations
import argparse,hashlib,json,math
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from v98_staged_exit_viability_governor_v2 import (
    PARTICIPATION,STRESSED_QUOTE_FRACTION,EXIT_FRICTION_MULTIPLIER,
    FEES,prior_min_exit_window_quote)
from ba_ratio_reversion_governor import ENTRY_FRACTION

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=2160
EPOCH=336
FIRST_2024=9504
TOL=1e-12

def source_signal(close,rate,event,t):
    """Only completed observations through t; no future inputs."""
    mom=np.log(close[t]/close[t-EPOCH])
    carry=np.sum(rate[t-EPOCH+1:t+1]*event[t-EPOCH+1:t+1],axis=0)
    candidates=[]
    for j in range(4):
        side=(1 if mom[j]>.05 and carry[j]<0 else
              -1 if mom[j]<-.05 and carry[j]>0 else 0)
        if side:
            candidates.append((-abs(float(mom[j])),j,side))
    if not candidates:return None
    _,j,side=min(candidates)
    # Transport-only canonicalization: rank and threshold used RAW momentum above.
    # Different Linux libm versions differ at ~1e-17 in numpy.log.
    return int(j),int(side),round(float(mom[j]),14),float(carry[j])

def run():
    frames,manifest=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    episodes=[]
    for t in range(START,HOURS-EPOCH-1,EPOCH):
        signal=source_signal(c,r,e,t)
        if signal is None:continue
        j,side,momentum,prior_funding=signal
        entry=t+1;exit_t=t+EPOCH+1
        assert exit_t<HOURS and entry>t
        entry_open=float(o[entry,j]);exit_open=float(o[exit_t,j])
        price=side*(exit_open/entry_open-1.)
        funding=0.
        event_count=0
        for k in range(entry,exit_t):
            if not e[k,j]:continue
            rate=float(r[k,j])
            mark=float(mh[k,j] if side*rate>=0 else ml[k,j])
            funding-=side*rate*mark/entry_open
            event_count+=1
        gross=1.+exit_open/entry_open
        costs={fee:float(sum(FEES[fee])*gross) for fee in FEES}
        net={fee:float(price+funding-costs[fee]) for fee in FEES}
        adverse=float((np.min(l[entry:exit_t,j])/entry_open-1.)
            if side==1 else (1.-np.max(h[entry:exit_t,j])/entry_open))
        capacity=float(
            ENTRY_FRACTION*PARTICIPATION*STRESSED_QUOTE_FRACTION*
            prior_min_exit_window_quote(q,entry)[j]/
            EXIT_FRICTION_MULTIPLIER)
        if (not all(np.isfinite(list(net.values())+[capacity,adverse]))
            or capacity<0 or event_count!=EPOCH//8):
            raise ValueError("BY_EVENT_OR_CAPACITY_INTEGRITY")
        episodes.append({
            "decision_t":t,"entry_t":entry,"exit_t":exit_t,
            "entry_year":"2023" if entry<FIRST_2024 else "2024",
            "asset":ASSETS[j],"side":side,
            "past_336h_log_return":momentum,
            "past_336h_native_funding_sum":prior_funding,
            "entry_open":entry_open,"exit_open":exit_open,
            "native_funding_events":event_count,
            "price_pnl_per_entry_usd":float(price),
            "native_funding_per_entry_usd":float(funding),
            "roundtrip_cost_per_entry_usd":costs,
            "net_per_entry_usd":net,
            "worst_intrahold_adverse_per_entry_usd":adverse,
            "prior_only_authorized_max_notional_usd":capacity,
        })
    annual={}
    for yr in ("2023","2024"):
        x=[v for v in episodes if v["entry_year"]==yr]
        sums={mode:float(sum(v["net_per_entry_usd"][mode] for v in x))
              for mode in FEES}
        annual[yr]={
            "selected_episodes":len(x),"native_funding_events":sum(v["native_funding_events"] for v in x),
            "price_pnl_per_unit_episode_sum":float(sum(v["price_pnl_per_entry_usd"] for v in x)),
            "native_funding_per_unit_episode_sum":float(sum(v["native_funding_per_entry_usd"] for v in x)),
            "net_per_unit_episode_sum":sums,
            "positive_severe_episodes":sum(v["net_per_entry_usd"]["severe"]>0 for v in x),
            "worst_adverse_excursion":float(min((v["worst_intrahold_adverse_per_entry_usd"] for v in x),default=0.)),
            "median_prior_authorized_notional_usd":float(np.median(
                [v["prior_only_authorized_max_notional_usd"] for v in x])) if x else 0.,
            "by_asset_episode_counts":{asset:sum(v["asset"]==asset for v in x) for asset in ASSETS},
        }
    passed=all(annual[y]["selected_episodes"]>=4 and
               annual[y]["net_per_unit_episode_sum"]["severe"]>0 for y in annual)
    payload={
        "architecture":"BY_SOURCE_ONLY","decision":(
            "PASS_BY_SOURCE_FEASIBILITY_ONLY_REQUIRES_NEW_SEVEN_SLOT_PREREG"
            if passed else "REJECT_BY_SOURCE_MECHANISM_NO_RESCUE"),
        "historical_training_only":True,"validation_2025_read":False,
        "system_pnl_computed":False,"portfolio_cagr_claimed":False,
        "external_benchmarks_used":False,"trading_authorized":False,
        "source_manifest_sha256":hashlib.sha256(json.dumps(
            manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "fixed_decision_epoch_hours":EPOCH,"episode_count":len(episodes),
        "annual":annual,"episodes":episodes,
    }
    return payload

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    a=p.parse_args();v=run()
    with open(a.output,"w") as f:json.dump(v,f,sort_keys=True,indent=2,allow_nan=False)
    print("BY_SOURCE_DECISION",v["decision"])
    for y,d in v["annual"].items():
        print("BY_YEAR",y,"episodes",d["selected_episodes"],
              "severe_unit_episode_sum",round(d["net_per_unit_episode_sum"]["severe"],8),
              "native_funding_unit_sum",round(d["native_funding_per_unit_episode_sum"],8),
              "median_prior_cap_usd",round(d["median_prior_authorized_notional_usd"],2))
