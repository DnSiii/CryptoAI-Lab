#!/usr/bin/env python3
"""V98 BZ preregistered volume-confirmed closing-high continuation, source ONLY.
No system PnL, no holdout, no external engine inputs or live orders.
"""
from __future__ import annotations
import argparse, hashlib, json, math
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official, HOURS
from v98_staged_exit_viability_governor_v2 import (
    FEES, PARTICIPATION, STRESSED_QUOTE_FRACTION,
    EXIT_FRICTION_MULTIPLIER, prior_min_exit_window_quote)
from ba_ratio_reversion_governor import ENTRY_FRACTION

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
FIRST=2160
SPAN=168
YEAR_2024=9504

def pick(close,quote,t):
    candidates=[]
    for j in range(4):
        p=float(close[t,j])
        ret72=math.log(p/float(close[t-72,j]))
        ret336=math.log(p/float(close[t-336,j]))
        recent=float(np.sum(quote[t-23:t+1,j]))
        older=quote[t-335:t-23,j]
        assert len(older)==312
        # Exactly 289 contiguous 24h windows ending at or before t-24.
        windows=np.convolve(older,np.ones(24,dtype=float),mode="valid")
        assert len(windows)==289
        median=float(np.median(windows))
        ratio=recent/median if median>0 else 0.
        if (ret72>.02 and ret336>0 and
            p>float(np.max(close[t-168:t,j])) and ratio>1.10):
            candidates.append((-ret72*min(ratio,3.),j,ret72,ret336,ratio))
    if not candidates:return None
    _,j,a,b,ratio=min(candidates)
    # Only diagnostic transport is rounded; decision and ranking used raw floats.
    return j,round(a,12),round(b,12),round(ratio,12)

def run():
    frames,manifest=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    episodes=[]
    for t in range(FIRST,HOURS-SPAN-1,SPAN):
        found=pick(c,q,t)
        if found is None:continue
        j,ret72,ret336,ratio=found
        a=t+1;b=t+SPAN+1
        entry=float(o[a,j]);exit_price=float(o[b,j])
        price=exit_price/entry-1.
        funding=0.;count=0
        for k in range(a,b):
            if not e[k,j]:continue
            rate=float(r[k,j])
            mark=float(mh[k,j] if rate>=0 else ml[k,j])
            funding-=rate*mark/entry
            count+=1
        if count!=21:raise ValueError("BZ_NATIVE_EVENT_COUNT")
        friction={mode:float(sum(fees)*(1.+exit_price/entry))
                  for mode,fees in FEES.items()}
        net={mode:float(price+funding-friction[mode]) for mode in FEES}
        cap=float(ENTRY_FRACTION*PARTICIPATION*
                  STRESSED_QUOTE_FRACTION*
                  prior_min_exit_window_quote(q,a)[j]/
                  EXIT_FRICTION_MULTIPLIER)
        worst=float(np.min(l[a:b,j])/entry-1.)
        if (not np.isfinite([price,funding,cap,worst,*net.values()]).all()
            or cap<0):raise ValueError("BZ_SOURCE_NONFINITE")
        episodes.append({
            "decision_t":t,"entry_t":a,"exit_t":b,
            "entry_year":"2023" if a<YEAR_2024 else "2024",
            "asset":ASSETS[j],"side":1,
            "past_72h_log_return":ret72,"past_336h_log_return":ret336,
            "past_volume_ratio":ratio,
            "entry_open":entry,"exit_open":exit_price,
            "native_funding_events":count,
            "price_pnl_per_entry_usd":price,
            "native_funding_per_entry_usd":funding,
            "roundtrip_cost_per_entry_usd":friction,
            "net_per_entry_usd":net,
            "worst_intrahold_adverse_per_entry_usd":worst,
            "prior_only_authorized_max_notional_usd":cap,
        })
    annual={}
    for yr in ("2023","2024"):
        rows=[v for v in episodes if v["entry_year"]==yr]
        annual[yr]={
            "selected_episodes":len(rows),
            "native_funding_events":sum(v["native_funding_events"] for v in rows),
            "price_pnl_per_unit_episode_sum":float(sum(v["price_pnl_per_entry_usd"] for v in rows)),
            "native_funding_per_unit_episode_sum":float(sum(v["native_funding_per_entry_usd"] for v in rows)),
            "net_per_unit_episode_sum":{mode:float(sum(v["net_per_entry_usd"][mode] for v in rows)) for mode in FEES},
            "positive_severe_episodes":sum(v["net_per_entry_usd"]["severe"]>0 for v in rows),
            "worst_adverse_excursion":min((v["worst_intrahold_adverse_per_entry_usd"] for v in rows),default=0.),
            "median_prior_authorized_notional_usd":float(np.median([v["prior_only_authorized_max_notional_usd"] for v in rows])) if rows else 0.,
            "by_asset_episode_counts":{asset:sum(v["asset"]==asset for v in rows) for asset in ASSETS},
        }
    passed=all(annual[yr]["selected_episodes"]>=4 and
               annual[yr]["net_per_unit_episode_sum"]["severe"]>0
               for yr in annual)
    return {
        "architecture":"BZ_SOURCE_ONLY",
        "decision":("PASS_BZ_SOURCE_FEASIBILITY_ONLY_NEEDS_NEW_SEVENSLOT_PREREG"
                    if passed else "REJECT_BZ_SOURCE_NO_RESCUE"),
        "historical_training_only":True,
        "validation_2025_read":False,"system_pnl_computed":False,
        "portfolio_cagr_claimed":False,"external_benchmarks_used":False,
        "trading_authorized":False,
        "source_manifest_sha256":hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "decision_epoch_hours":SPAN,"episode_count":len(episodes),
        "annual":annual,"episodes":episodes,
    }

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    args=p.parse_args();result=run()
    with open(args.output,"w") as f:json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
    print("BZ_SOURCE_DECISION",result["decision"])
    for y,a in result["annual"].items():
        print("BZ_YEAR",y,"episodes",a["selected_episodes"],
              "severe_unit_episode_sum",round(a["net_per_unit_episode_sum"]["severe"],8),
              "median_capacity_usd",round(a["median_prior_authorized_notional_usd"],2))
