#!/usr/bin/env python3
"""V98 OT independent pre-result oracle: weekly signal and physical ledger.
No import of OT signal/allocator/planner functions, no benchmarks or holdout.
"""
import math
import numpy as np

def independent_decisions(d,primary,targets):
    c=np.asarray(d["c"],float);q=np.asarray(d["q"],float)
    l=np.log(c)
    modes={};raws={}
    for t in range(744,27048,168):
        r28=np.log(c[t]/c[t-672])
        r7=np.log(c[t]/c[t-168])
        r3=np.log(c[t]/c[t-72])
        r1=np.log(c[t]/c[t-24])
        hourly=np.log(c[t-671:t+1]/c[t-672:t])
        sigma=np.sqrt(np.mean((hourly-hourly.mean(axis=0))**2,axis=0))*math.sqrt(672)
        score=(r28+0.5*r7)/np.maximum(sigma,.04)
        breadth=sum(r28>0)
        mode="positive" if breadth>=3 else ("negative" if breadth<=1 else "mixed")
        raw=np.zeros((4,4))
        if breadth>=2:
            best=sorted(range(4),key=lambda k:(-score[k],k))[:2]
            for k,weight in zip(best,(.34,.22)):
                if score[k]>0:raw[0,k]=weight
        else:
            worst=sorted(range(4),key=lambda k:(score[k],k))[:2]
            for k,weight in zip(worst,(-.30,-.20)):
                if score[k]<0:raw[0,k]=weight
        eligible=[k for k in range(4) if r3[k]<0 and r1[k]>0
                  and sum(q[t-23:t+1,k])>sum(q[t-47:t-23,k])]
        if eligible:
            best=min(eligible,key=lambda k:(-r1[k],k))
            raw[1,best]=.12
        best=min(range(4),key=lambda k:(-r7[k],k))
        worst=min(range(4),key=lambda k:(r7[k],k))
        if r7[best]-r7[worst]>.16 and r1[best]<0 and r1[worst]>0:
            raw[2,best]=-.10;raw[2,worst]=.10
        if sum(r1<-.06)>=3:
            worst=min(range(4),key=lambda k:(r3[k],k))
            raw[3,worst]=-.14
        elif sum(r3<-.08)>=3 and sum(r1>0)>=3:
            best=min(range(4),key=lambda k:(-r1[k],k))
            raw[3,best]=.14
        factors={"positive":(1.,.75,.5),"negative":(.5,1.,1.),
                 "mixed":(.75,1.,.75)}[mode]
        for k in (1,2,3):raw[k]*=factors[k-1]
        modes[t]=mode;raws[t]=raw
    if len(modes)!=157 or set(modes)!=set(primary):
        raise ValueError("OT_ORACLE_WEEKLY_CALENDAR")
    max_err=0.;mismatches=0
    for t in modes:
        p,m=primary[t]
        error=float(np.max(np.abs(raws[t]-p)))
        max_err=max(max_err,error)
        if error>1e-10 or m!=modes[t]:mismatches+=1
    priority={"positive":(1,2,3),"negative":(3,2,1),"mixed":(2,1,3)}
    books={"OT_full":(0,1,2,3),"OT_core_only":(0,),
           "OT_minus_opportunity":(0,2,3),"OT_minus_RV":(0,1,3),
           "OT_minus_stress":(0,1,2)}
    for book,active in books.items():
        if set(targets[book])!=set(modes):raise ValueError("OT_ORACLE_BOOK_CLOCK")
        for t in modes:
            raw=raws[t];w=np.zeros((4,4))
            w[0]=raw[0]
            remaining=min(.28,.84-float(np.abs(w).sum()))
            for k in priority[modes[t]]:
                if k not in active:continue
                gross=float(np.abs(raw[k]).sum())
                if gross>0 and remaining>0:
                    portion=min(gross,remaining)
                    w[k]=raw[k]*(portion/gross)
                    remaining-=portion
            error=float(np.max(np.abs(w-targets[book][t])))
            max_err=max(max_err,error)
            if error>1e-10:mismatches+=1
    return {"decisions":157,"books":5,"signal_and_allocation_mismatches":mismatches,
            "max_weight_error":max_err,"source_future_accessed":False,
            "independent_implementation":True}

def independent_fills(d,ledger,fee=.0004,slip=.0002,order="carried_before_fill"):
    if len(ledger)!=27048-744-1:raise ValueError("OT_ORACLE_LEDGER_LENGTH")
    old=np.zeros((4,4))
    mismatches=0;funding_events=0;fills=0;turnover=0.;max_error=0.
    for t,before,nav,cash,fees,slippage,new,gap in ledger:
        px=d["o"][t];new=np.asarray(new,float)
        delta=new.sum(axis=0)-old.sum(axis=0)
        turn=float(np.dot(np.abs(delta),px))
        turnover+=turn
        if turn>1e-8:fills+=1
        if np.any((np.abs(delta)>1e-12)&(~d["execution_allowed"][t])):
            mismatches+=1
        expected_fee=turn*fee
        expected_slip=turn*slip
        err=max(abs(expected_fee-fees),abs(expected_slip-slippage))
        if d["event"][t].any():
            funding_events+=1
            payer=old.sum(axis=0) if order=="carried_before_fill" else new.sum(axis=0)
            obligations=payer*d["rate"][t]
            marks=np.where(obligations>=0,d["mark_upper"][t],d["mark_lower"][t])
            expected_cash=-float(np.dot(obligations,marks))
            err=max(err,abs(expected_cash-cash))
        else:err=max(err,abs(cash))
        max_error=max(max_error,err)
        if err>1e-6:mismatches+=1
        old=new
    return {"hours":len(ledger),"funding_hours":funding_events,
            "net_fill_events":fills,"net_turnover":turnover,
            "independent_fee_slippage_funding_mismatches":mismatches,
            "max_absolute_cash_error":max_error,
            "no_future_signals_used":True,"exact_tick_mark_attested":False}
