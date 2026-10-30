#!/usr/bin/env python3
"""Independent BZ receipt verifier. Does not import BZ strategy or accounting."""
from __future__ import annotations
import argparse, glob, json, math
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official, HOURS

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
MODES={"base":.001,"severe":.005,"supersevere":.015}
FIRST=2160
SPAN=168

def same(x,y,name):
    if not math.isclose(float(x),float(y),rel_tol=1e-9,abs_tol=1e-9):
        raise ValueError("BZ_INDEPENDENT_"+name+":"+repr(x)+":"+repr(y))

def reconstruct(receipt,frames):
    o,h,l,c,q,r,e,ml,mh=frames
    selections=[]
    for t in range(FIRST,HOURS-SPAN-1,SPAN):
        eligible=[]
        for j in range(4):
            price=float(c[t,j])
            r72=math.log(price/float(c[t-72,j]))
            r336=math.log(price/float(c[t-336,j]))
            last24=sum(float(q[k,j]) for k in range(t-23,t+1))
            prior=[sum(float(q[k,j]) for k in range(end-23,end+1))
                   for end in range(t-312,t-23)]
            if len(prior)!=289:raise ValueError("BZ_PRIOR_WINDOW")
            med=float(np.median(prior))
            ratio=last24/med if med>0 else 0.
            if (r72>.02 and r336>0 and
                price>max(float(c[k,j]) for k in range(t-168,t))
                and ratio>1.10):
                eligible.append((-r72*min(ratio,3.),j,r72,r336,ratio))
        if eligible:
            _,j,r72,r336,ratio=min(eligible)
            selections.append((t,j,r72,r336,ratio))
    if len(selections)!=len(receipt["episodes"]):
        raise ValueError("BZ_EPISODE_INVENTORY")
    annual={y:{"count":0,"native_events":0,"price":0.,"funding":0.,
               "net":{mode:0. for mode in MODES},"asset":{a:0 for a in ASSETS},
               "positive_severe":0,"adverse":[],"capacity":[]}
            for y in ("2023","2024")}
    for row,(t,j,r72,r336,ratio) in zip(receipt["episodes"],selections):
        a=t+1;b=t+SPAN+1
        if (row["decision_t"]!=t or row["entry_t"]!=a or
            row["exit_t"]!=b or row["asset"]!=ASSETS[j] or
            row["side"]!=1):
            raise ValueError("BZ_CAUSAL_SIGNAL")
        for name,value in [("past_72h_log_return",r72),
                           ("past_336h_log_return",r336),
                           ("past_volume_ratio",ratio)]:
            if row[name]!=round(value,12):
                raise ValueError("BZ_SIGNAL_TRANSPORT_"+name)
        p=float(o[a,j]);end=float(o[b,j])
        price=end/p-1.
        funding=0.;events=0
        for k in range(a,b):
            if e[k,j]:
                rate=float(r[k,j])
                mark=float(mh[k,j] if rate>=0 else ml[k,j])
                funding+=-rate*mark/p
                events+=1
        if events!=21 or row["native_funding_events"]!=events:
            raise ValueError("BZ_NATIVE_EVENTS")
        same(p,row["entry_open"],"ENTRY_OPEN")
        same(end,row["exit_open"],"EXIT_OPEN")
        same(price,row["price_pnl_per_entry_usd"],"PRICE")
        same(funding,row["native_funding_per_entry_usd"],"FUNDING")
        worst=min(float(l[k,j])/p-1 for k in range(a,b))
        same(worst,row["worst_intrahold_adverse_per_entry_usd"],"ADVERSE")
        # Independent 313 rolling 24h windows in the 336h completed source.
        minimum=min(sum(float(q[k,j]) for k in range(start,start+24))
                    for start in range(a-336,a-23))
        cap=.25*.0025*.5*minimum/2.2
        same(cap,row["prior_only_authorized_max_notional_usd"],"CAPACITY")
        year="2023" if a<9504 else "2024"
        if row["entry_year"]!=year:raise ValueError("BZ_YEAR")
        acc=annual[year]
        acc["count"]+=1;acc["native_events"]+=events
        acc["price"]+=price;acc["funding"]+=funding
        acc["asset"][ASSETS[j]]+=1
        acc["adverse"].append(worst);acc["capacity"].append(cap)
        for mode,rate in MODES.items():
            cost=rate*(1+end/p)
            same(cost,row["roundtrip_cost_per_entry_usd"][mode],"COST_"+mode)
            net=price+funding-cost
            same(net,row["net_per_entry_usd"][mode],"NET_"+mode)
            acc["net"][mode]+=net
        acc["positive_severe"]+=row["net_per_entry_usd"]["severe"]>0
    for year,acc in annual.items():
        report=receipt["annual"][year]
        for name,expected in [
            ("selected_episodes",acc["count"]),
            ("native_funding_events",acc["native_events"]),
            ("positive_severe_episodes",acc["positive_severe"])]:
            if report[name]!=expected:raise ValueError("BZ_YEAR_"+name)
        if report["by_asset_episode_counts"]!=acc["asset"]:
            raise ValueError("BZ_ASSET_COUNTS")
        same(report["price_pnl_per_unit_episode_sum"],acc["price"],"YEAR_PRICE")
        same(report["native_funding_per_unit_episode_sum"],acc["funding"],"YEAR_FUNDING")
        same(report["worst_adverse_excursion"],min(acc["adverse"],default=0.),"YEAR_ADVERSE")
        same(report["median_prior_authorized_notional_usd"],
             float(np.median(acc["capacity"])) if acc["capacity"] else 0.,"YEAR_CAPACITY")
        for mode in MODES:
            same(report["net_per_unit_episode_sum"][mode],acc["net"][mode],"YEAR_NET_"+mode)
    passed=all(v["count"]>=4 and v["net"]["severe"]>0 for v in annual.values())
    expected=("PASS_BZ_SOURCE_FEASIBILITY_ONLY_NEEDS_NEW_SEVENSLOT_PREREG"
              if passed else "REJECT_BZ_SOURCE_NO_RESCUE")
    if (receipt["decision"]!=expected or
        not receipt["historical_training_only"] or receipt["validation_2025_read"]
        or receipt["system_pnl_computed"] or receipt["portfolio_cagr_claimed"]
        or receipt["external_benchmarks_used"] or receipt["trading_authorized"]):
        raise ValueError("BZ_FIREWALL_OR_DECISION")
    return {"decision":expected,"episodes":len(selections),"annual":annual,
            "cross_os_identical":True,"independent_signals_and_native_cashflows":True,
            "holdout_2025_read":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    args=p.parse_args()
    files=sorted(glob.glob(str(Path(args.root)/"**"/"bz_source_receipt.json"),recursive=True))
    if len(files)!=2:raise ValueError("BZ_CROSS_OS_ARTIFACT_COUNT:"+str(files))
    receipts=[json.loads(Path(f).read_text()) for f in files]
    if receipts[0]!=receipts[1]:
        raise ValueError("BZ_CROSS_OS_RECEIPT_DIFFERENCE")
    frames,manifest=load_official()
    result=reconstruct(receipts[0],frames)
    Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    print("BZ_INDEPENDENT_AUDIT",result["decision"],"episodes",result["episodes"])
    for year,acc in result["annual"].items():
        print("BZ_YEAR",year,"episodes",acc["count"],
              "severe_net_unit_sum",round(acc["net"]["severe"],8))
