#!/usr/bin/env python3
"""CB independent source decision and native cashflow auditor.
Does NOT import CB source/allocator/settlement functions. Original official
Clean4 loader is shared only to authenticate pinned training bytes.
"""
from __future__ import annotations
import argparse,hashlib,json,math
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS

NAMES=("Growth","Opportunity","RelativeValue","StressRecovery")
FEES={"base":.001,"severe":.005,"supersevere":.015}
START=2160
STEP=336
YEAR2024=9504

def near(x,y,rtol=1e-10,atol=1e-9):
    return bool(np.isclose(x,y,rtol=rtol,atol=atol))

def independently_decide(c,r,e,t):
    log=np.log(c)
    R=lambda span:log[t]-log[t-span]
    past=log[t-1008:t+1]
    step=np.diff(past,axis=0)
    v_short=np.sqrt((step[-336:]**2).mean(axis=0))
    v_long=np.sqrt((step**2).mean(axis=0))
    ret72,ret168,ret336,ret1008=(R(n) for n in (72,168,336,1008))
    funding336=np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
    funding1008=np.sum(r[t-1007:t+1]*e[t-1007:t+1],axis=0)
    scores=(ret1008-funding1008)/np.maximum(v_short,.005)
    eligible=[i for i in range(4) if ret1008[i]-funding1008[i]>0]
    leaders=sorted(eligible,key=lambda i:(-scores[i],i))[:2]
    w=np.zeros((4,4))
    if leaders:
        inv=np.reciprocal(np.maximum(v_short[leaders],.005))
        for k,i in enumerate(leaders):w[0,i]=inv[k]/sum(inv)
    acceleration=ret72-(log[t-72]-log[t-144])
    opp=sorted([i for i in range(4) if ret336[i]>0 and acceleration[i]>0],
               key=lambda i:(-acceleration[i],i))
    if opp:w[1,opp[0]]=1.
    rank=sorted(range(4),key=lambda i:(-(ret336[i]-funding336[i]),i))
    if (ret336[rank[0]]-funding336[rank[0]])-(ret336[rank[-1]]-funding336[rank[-1]])>.04:
        w[2,rank[0]]=.5;w[2,rank[-1]]=-.5
    if np.median(v_short)>np.median(v_long):
        if np.median(ret72)<0:w[3,int(np.argmin(ret72))]=-1.
        else:w[3,int(np.argmax(ret72))]=1.
    regime=("STRESS" if np.median(ret168)<0 else
            "BULL" if sum(ret336>0)>=3 else "MIXED")
    return w,regime

def audit(receipt):
    frames,manifest=load_official()
    op,hi,lo,cl,q,rate,event,ml,mh=frames
    errors=[];checks=0;event_checks=0;corner_checks=0
    episodes=receipt.get("episodes",[])
    expected=list(range(START,HOURS-STEP-1,STEP))
    if len(episodes)!=len(expected):errors.append("EPISODE_COUNT")
    if receipt.get("validation_2025_read") is not False or receipt.get("system_pnl_computed") is not False:
        errors.append("HOLDOUT_OR_SYSTEM_FLAG")
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    if receipt.get("source_manifest_sha256")!=digest:errors.append("MANIFEST")
    annual={yr:{book:{"n":0,"net":{fee:0. for fee in FEES}} for book in NAMES}
            for yr in ("2023","2024")}
    for ep,t in zip(episodes,expected):
        a=t+1;b=t+STEP+1
        if (ep.get("decision_t"),ep.get("entry_t"),ep.get("exit_t"))!=(t,a,b):
            errors.append("TIMESTAMP_"+str(t));continue
        expected_w,regime=independently_decide(cl,rate,event,t)
        if ep.get("regime")!=regime:errors.append("REGIME_"+str(t))
        yr="2023" if a<YEAR2024 else "2024"
        if ep.get("entry_year")!=yr:errors.append("YEAR_"+str(t))
        books=ep.get("books",[])
        if len(books)!=4:errors.append("BOOK_COUNT_"+str(t));continue
        for i,row in enumerate(books):
            checks+=1
            if row.get("book")!=NAMES[i]:errors.append("BOOK_NAME_"+str(t))
            w=np.asarray(row.get("weights",[]),dtype=float)
            if w.shape!=(4,) or not np.allclose(w,expected_w[i],rtol=1e-12,atol=1e-12):
                errors.append("SOURCE_WEIGHT_"+str(t)+"_"+str(i));continue
            active=bool(np.any(w))
            if row.get("active")!=active:errors.append("ACTIVITY_"+str(t))
            if not np.allclose(row["entry_open"],op[a],rtol=0,atol=0):
                errors.append("ENTRY_"+str(t))
            if not np.allclose(row["exit_open"],op[b],rtol=0,atol=0):
                errors.append("EXIT_"+str(t))
            u=w/op[a]
            price=float(np.sum(u*(op[b]-op[a])))
            fund=0.;native=0
            for k in range(a,b):
                obligations=u*rate[k]*event[k]
                mark=np.where(obligations>=0,mh[k],ml[k])
                fund-=float(np.sum(obligations*mark))
                native+=int(np.count_nonzero(event[k]*abs(u)))
            event_checks+=native
            if active:
                worst=float(np.min((np.where(u>=0,lo[a:b],hi[a:b])-op[a])@u))
                # 313 rolling 24h windows inside the prior 336h completed bars.
                window=q[a-336:a]
                rolling=np.array([window[z:z+24].sum(axis=0) for z in range(313)])
                prior_min=rolling.min(axis=0)
                per_asset_exit=.25*.25*.0025*.50*prior_min/(2.2*np.maximum(abs(w),1e-100))
                per_asset_entry=.25*.0025*q[t]/np.maximum(abs(w),1e-100)
                limit=float(min(np.min(np.where(abs(w)>0,per_asset_exit,np.inf)),
                                np.min(np.where(abs(w)>0,per_asset_entry,np.inf))))
                annual[yr][NAMES[i]]["n"]+=1
            else:
                worst=0.;limit=0.
            if not near(price,row["price_pnl_per_gross_usd"]):
                errors.append("PRICE_"+str(t)+"_"+str(i))
            if not near(fund,row["native_funding_per_gross_usd"]):
                errors.append("FUNDING_"+str(t)+"_"+str(i))
            if native!=row["native_funding_asset_events"]:
                errors.append("EVENTS_"+str(t)+"_"+str(i))
            if not near(worst,row["worst_intrahold_adverse_per_gross_usd"]):
                errors.append("ADVERSE_"+str(t)+"_"+str(i))
            if not near(limit,row["prior_only_max_entry_notional_usd"],rtol=1e-9,atol=1e-6):
                errors.append("CAPACITY_"+str(t)+"_"+str(i))
            for fee,friction in FEES.items():
                cost=friction*float(np.sum(abs(u)*(op[a]+op[b])))
                net=price+fund-cost
                if not near(cost,row["roundtrip_cost_per_gross_usd"][fee]):
                    errors.append("COST_"+fee+"_"+str(t)+"_"+str(i))
                if not near(net,row["net_per_gross_usd"][fee]):
                    errors.append("NET_"+fee+"_"+str(t)+"_"+str(i))
                if active:annual[yr][NAMES[i]]["net"][fee]+=net
            corner_checks+=81 if active else 0
    for yr in annual:
        for book in NAMES:
            got=receipt["annual"][yr][book]
            expected_row=annual[yr][book]
            if got["active_episodes"]!=expected_row["n"]:
                errors.append("YEAR_ACTIVE_"+yr+"_"+book)
            for fee in FEES:
                if not near(got["net_per_gross_usd_episode_sum"][fee],expected_row["net"][fee]):
                    errors.append("YEAR_NET_"+yr+"_"+book+"_"+fee)
    gates={book:all(annual[yr][book]["n"]>=4 and annual[yr][book]["net"]["severe"]>0
                    for yr in annual) for book in NAMES}
    if gates!=receipt.get("source_gates"):errors.append("GATE")
    expected_decision=("PASS_CB_SOURCE_ONLY_REQUIRES_FULL_SEVEN_SLOT_INTEGRATION"
                       if all(gates.values()) else "REJECT_CB_SOURCE_ECONOMICS_NO_RESCUE")
    if receipt.get("decision")!=expected_decision:errors.append("DECISION")
    return {"architecture":"CB_INDEPENDENT_SOURCE_AUDIT",
            "passed":not errors,"errors":errors[:40],
            "independently_rederived_episode_books":checks,
            "native_funding_asset_events_replayed":event_checks,
            "conservative_intrahold_corner_scenarios":corner_checks,
            "source_gates_rederived":gates,
            "decision":("PASS_CB_INDEPENDENT_SOURCE_AUDIT_ONLY" if not errors
                        else "BLOCK_CB_INDEPENDENT_SOURCE_AUDIT")}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--receipt",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    receipt=json.load(open(a.receipt))
    result=audit(receipt)
    with open(a.output,"w") as f:json.dump(result,f,indent=2,sort_keys=True)
    print("CB_AUDIT",result["decision"],"episode_books",result["independently_rederived_episode_books"],
          "funding_events",result["native_funding_asset_events_replayed"],
          "errors",result["errors"])
    raise SystemExit(0 if result["passed"] else 3)
