#!/usr/bin/env python3
"""V98 PD: preregistered seven-slot risk-premium/funding/RV/convexity composition.
Only Clean-4 exposed 2022-25 training. No benchmarks, 2026+, holdout or paper.
"""
import json,math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

BOOKS={"PD_full":(0,1,2,3),"PD_core_only":(0,),
       "PD_minus_opportunity":(0,2,3),"PD_minus_RV":(0,1,3),
       "PD_minus_stress":(0,1,2)}
PRIORITY={"stress":(3,1,2),"carry":(1,2,3)}
MULT={"stress":(.5,.5,1.),"carry":(1.,1.,.5)}
CLOCK=tuple(range(WARMUP,HOURS,STEP))

def signals(d):
    c=np.asarray(d["c"],float);rate=np.asarray(d["rate"],float)
    event=np.asarray(d["event"],bool)
    if c.shape!=(HOURS,4) or rate.shape!=(HOURS,4) or event.shape!=(HOURS,4):
        raise ValueError("PD_SOURCE_SHAPE")
    if not np.isfinite(c).all() or not np.isfinite(rate).all() or np.any(c<=0):
        raise ValueError("PD_SOURCE_NONFINITE")
    p=np.log(c);out={}
    for t in CLOCK:
        r504=p[t]-p[t-504];r168=p[t]-p[t-168];r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        ret168=np.diff(p[t-168:t+1],axis=0)
        vol=np.std(ret168,axis=0)*math.sqrt(24*365.25)
        prev=np.diff(p[t-336:t-167,0])
        mode="stress" if np.std(ret168[:,0])>1.25*np.std(prev) else "carry"
        raw=np.zeros((4,4),float)
        score=(r504+.5*r168)/np.maximum(vol,.25)
        if r504[0]>0:
            raw[0,0]=.28
            eligible=[j for j in (1,2,3) if r504[j]>0]
            if eligible:raw[0,min(eligible,key=lambda j:(-score[j],j))]=.20
        elif r504[0]<0:
            raw[0,0]=-.28
            eligible=[j for j in (1,2,3) if r504[j]<0]
            if eligible:raw[0,min(eligible,key=lambda j:(score[j],j))]=-.20
        funding=np.zeros(4,float)
        for j in range(4):
            idx=np.flatnonzero(event[t-168:t,j])
            if len(idx)>=21:
                funding[j]=float(np.mean(rate[t-168:t,j][idx[-21:]]))
        chosen=min(range(4),key=lambda j:(-abs(funding[j]),j))
        if abs(funding[chosen])>=.000025:
            side=-1. if funding[chosen]>0 else 1.
            if side*r168[chosen]>0:raw[1,chosen]=side*.18
        btc=ret168[:,0]
        btcvar=float(np.mean((btc-btc.mean())**2))
        candidates=[]
        if btcvar>1e-14:
            for j in (1,2,3):
                alt=ret168[:,j]
                beta=float(np.mean((btc-btc.mean())*(alt-alt.mean()))/btcvar)
                beta=float(np.clip(beta,0.,1.5))
                residual=float(r72[j]-beta*r72[0])
                if abs(residual)>=.06:candidates.append((abs(residual),j,residual,beta))
        if candidates:
            _,j,residual,beta=min(candidates,key=lambda x:(-x[0],x[1]))
            side=-1. if residual>0 else 1.
            raw[2,j]=side*.15
            raw[2,0]=-side*.15*beta
        if r72[0]<-.07 and np.std(ret168[:,0])>np.std(prev):
            raw[3,0]=-.18
        elif r168[0]<-.10 and r24[0]>.025 and np.std(ret168[:,0])<=np.std(prev):
            raw[3,0]=.18
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("PD_DECISION_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PD_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    room=min(.36,max(0.,.84-float(np.abs(held).sum())))
    for k in PRIORITY[mode]:
        if k not in active:continue
        gross=float(np.abs(raw[k]).sum())
        if gross>0 and room>0:
            take=min(gross,room)
            held[k]=raw[k]*(take/gross)
            room-=take
    if float(np.abs(held).sum())>.84+1e-10 or float(np.abs(held[1:]).sum())>.36+1e-10:
        raise ValueError("PD_GROSS")
    return held

def target_books(decisions):
    return {book:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for book,active in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS)[:,None];j=np.arange(4)[None,:]
    c=100*np.exp(.00003*t*(1+j/6)+.05*np.sin(t/83+j))
    event=np.broadcast_to((np.arange(HOURS)%8==0)[:,None],(HOURS,4)).copy()
    rate=np.broadcast_to((.00008*np.sin(np.arange(HOURS)/73)[:,None]+.00003*j),(HOURS,4)).copy()
    a=signals({"c":c,"rate":rate,"event":event})
    c2=c.copy();c2[15000:]*=np.array([1.4,.7,1.6,.8])
    rate2=rate.copy();rate2[15000:]*=-3
    b=signals({"c":c2,"rate":rate2,"event":event})
    for t in CLOCK:
        if t<15000 and (a[t][1]!=b[t][1] or not np.array_equal(a[t][0],b[t][0])):
            raise ValueError("PD_FUTURE_LEAK")
    books=target_books(a)
    if len(books)!=5 or any(len(v)!=157 for v in books.values()):
        raise ValueError("PD_BOOKS")
    return {"decision":"PASS_PD_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "future_price_and_funding_mutation_safe":True}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from pd_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("PD_INDEPENDENT_ORACLE_MISMATCH")
    print("PD_INDEPENDENT_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PD_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PD_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill=independent_fills(d,ledger) if audit else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            key=tier+"/"+order
            if not all(x["passed"] for x in group.values()):
                failures.append(key+":physical");continue
            full=group["PD_full"]
            marginals[key]={slot:full["log_growth"]-group[book]["log_growth"] for slot,book in (
                ("Opportunity","PD_minus_opportunity"),("Relative_Value","PD_minus_RV"),("Stress_Recovery","PD_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","PD_minus_opportunity"),("Relative_Value","PD_minus_RV"),("Stress_Recovery","PD_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    delta=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if delta<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill is None or fill["independent_fee_slippage_funding_mismatches"]:failures.append("independent_fills")
    out={"architecture":"PD","preregistration":"pd_risk_premium_composition_prereg_20261101.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,"marginals":marginals,
         "audit":audit,"independent_decision_oracle":oracle,"independent_fill_oracle":fill,
         "gate_failures":failures,"decision":"REJECT_PD_TRAINING" if failures else "PASS_PROVISIONAL_PD_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PD_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
