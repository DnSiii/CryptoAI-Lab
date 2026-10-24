#!/usr/bin/env python3
"""Independent BY original-receipt audit: no BY signal, cost or execution imports.
Rebuilds every episode directly from authenticated 2022-24 source, then cross-OS.
"""
from __future__ import annotations
import argparse,glob,json,math
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
MODES={"base":.001,"severe":.005,"supersevere":.015}
START=2160
SPAN=336

def checkclose(a,b,label):
    if not math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-9):
        raise ValueError("BY_INDEPENDENT_"+label+":"+str(a)+":"+str(b))

def audit(receipt,frames):
    o,h,l,c,q,r,e,ml,mh=frames
    actual=receipt["episodes"]
    expected=[]
    for t in range(START,HOURS-SPAN-1,SPAN):
        options=[]
        for j in range(4):
            trend=float(math.log(float(c[t,j]/c[t-SPAN,j])))
            past=float(np.sum(r[t-SPAN+1:t+1,j]*e[t-SPAN+1:t+1,j]))
            if trend>.05 and past<0:options.append((-abs(trend),j,1))
            if trend<-.05 and past>0:options.append((-abs(trend),j,-1))
        if options:
            _,j,s=min(options)
            expected.append((t,j,s))
    if len(actual)!=len(expected):raise ValueError("BY_INDEPENDENT_EPISODE_INVENTORY")
    annual={yr:{"count":0,"net":{k:0. for k in MODES},"funding":0.,"price":0.}
            for yr in ("2023","2024")}
    for ep,(t,j,s) in zip(actual,expected):
        a=t+1;b=t+SPAN+1
        if (ep["decision_t"]!=t or ep["entry_t"]!=a or ep["exit_t"]!=b
            or ep["asset"]!=ASSETS[j] or ep["side"]!=s):
            raise ValueError("BY_INDEPENDENT_SIGNAL_OR_CAUSAL_CALENDAR")
        p=float(o[a,j]);p1=float(o[b,j])
        price=float(s*(p1/p-1))
        funding=0.;n=0
        for k in range(a,b):
            if e[k,j]==0:continue
            rate=float(r[k,j])
            mark=float(mh[k,j] if s*rate>=0 else ml[k,j])
            funding+=-s*rate*mark/p
            n+=1
        if n!=42 or ep["native_funding_events"]!=n:
            raise ValueError("BY_INDEPENDENT_FUNDING_EVENTS")
        checkclose(price,ep["price_pnl_per_entry_usd"],"PRICE")
        checkclose(funding,ep["native_funding_per_entry_usd"],"NATIVE_FUNDING")
        worst=(float(np.min(l[a:b,j])/p-1) if s==1
               else float(1-np.max(h[a:b,j])/p))
        checkclose(worst,ep["worst_intrahold_adverse_per_entry_usd"],"EXCURSION")
        # Independently enumerate 313 complete 24h windows ending before entry.
        quotes=q[a-336:a,j]
        cap=.25*.0025*.5*min(float(np.sum(quotes[i:i+24]))
                             for i in range(313))/2.2
        checkclose(cap,ep["prior_only_authorized_max_notional_usd"],"CAPACITY")
        yr="2023" if a<9504 else "2024"
        if ep["entry_year"]!=yr:raise ValueError("BY_INDEPENDENT_YEAR")
        annual[yr]["count"]+=1
        annual[yr]["funding"]+=funding
        annual[yr]["price"]+=price
        for mode,cost_rate in MODES.items():
            cost=(1+p1/p)*cost_rate
            checkclose(cost,ep["roundtrip_cost_per_entry_usd"][mode],"COST_"+mode)
            net=price+funding-cost
            checkclose(net,ep["net_per_entry_usd"][mode],"NET_"+mode)
            annual[yr]["net"][mode]+=net
    for yr,calc in annual.items():
        rec=receipt["annual"][yr]
        if rec["selected_episodes"]!=calc["count"]:
            raise ValueError("BY_INDEPENDENT_YEAR_COUNT")
        checkclose(calc["funding"],rec["native_funding_per_unit_episode_sum"],"ANNUAL_FUNDING")
        checkclose(calc["price"],rec["price_pnl_per_unit_episode_sum"],"ANNUAL_PRICE")
        for mode in MODES:
            checkclose(calc["net"][mode],rec["net_per_unit_episode_sum"][mode],"ANNUAL_"+mode)
    pass_gate=all(annual[yr]["count"]>=4 and annual[yr]["net"]["severe"]>0
                  for yr in annual)
    decision=("PASS_BY_SOURCE_FEASIBILITY_ONLY_REQUIRES_NEW_SEVEN_SLOT_PREREG"
              if pass_gate else "REJECT_BY_SOURCE_MECHANISM_NO_RESCUE")
    if receipt["decision"]!=decision or not receipt["historical_training_only"] or receipt["validation_2025_read"]:
        raise ValueError("BY_INDEPENDENT_DECISION_OR_FIREWALL")
    return {"episodes":len(expected),"annual":annual,"decision":decision}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True)
    p.add_argument("--output",required=True);a=p.parse_args()
    files=sorted(glob.glob(str(Path(a.root)/"**"/"by_source_receipt.json"),recursive=True))
    if len(files)!=2:raise ValueError("BY_CROSS_OS_ARTIFACT_INVENTORY:"+str(files))
    receipts=[json.load(open(f)) for f in files]
    if receipts[0]!=receipts[1]:raise ValueError("BY_CROSS_OS_FULL_RECEIPT_MISMATCH")
    frames,manifest=load_official()
    result=audit(receipts[0],frames)
    result["cross_os_identical"]=True
    result["independent_signal_and_native_cashflow_audited"]=True
    result["2025_holdout_read"]=False
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    print("BY_INDEPENDENT_AUDIT",result["decision"],"episodes",result["episodes"])
    for year,v in result["annual"].items():
        print("BY_AUDIT_YEAR",year,"episodes",v["count"],
              "severe_sum",round(v["net"]["severe"],8))
