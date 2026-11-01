#!/usr/bin/env python3
"""V98 PB preregistered funding-dislocation / cross-asset leadership seven-slot complete engine.
Only exposed Clean-4 2022-25 training; no V99/benchmarks/2026+/paper/holdout.
"""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate, physical, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP
from ot_independent_oracle import independent_fills

BOOKS={"PB_full":(0,1,2,3),"PB_core_only":(0,),
       "PB_minus_opportunity":(0,2,3),"PB_minus_RV":(0,1,3),
       "PB_minus_stress":(0,1,2)}
PRIORITY={"risk_on":(1,2,3),"risk_off":(3,2,1),"mixed":(2,1,3)}
MULT={"risk_on":(1.,1.,.50),"risk_off":(.50,.75,1.),"mixed":(.75,1.,.75)}
CLOCK=tuple(range(WARMUP,HOURS,STEP))

def signals(d):
    c=np.asarray(d["c"],float)
    rate=np.asarray(d["rate"],float)
    if c.shape!=(HOURS,4) or rate.shape!=(HOURS,4) or not np.isfinite(c).all() or not np.isfinite(rate).all() or np.any(c<=0):
        raise ValueError("PB_BAD_CLOSE_OR_FUNDING")
    p=np.log(c);out={}
    for t in CLOCK:
        r672=p[t]-p[t-672]
        r168=p[t]-p[t-168]
        r24=p[t]-p[t-24]
        # Only the 21 funding events that settled BEFORE the decision t.
        past=rate[t-168:t:8]
        if past.shape!=(21,4):raise ValueError("PB_FUNDING_WINDOW")
        mean_funding=np.mean(past,axis=0)
        score=r672+.65*r168-120.*mean_funding
        positive=int(np.sum(r168>0))
        negative=int(np.sum(r168<0))
        mode=("risk_on" if positive>=3 and r168[0]>0 else
              "risk_off" if negative>=3 and r168[0]<0 else "mixed")
        raw=np.zeros((4,4),float)
        if mode=="risk_on":
            ranked=sorted((j for j in range(4) if score[j]>0),key=lambda j:(-score[j],j))
            for j,w in zip(ranked[:2],(.50,.18)):raw[0,j]=w
        elif mode=="risk_off":
            ranked=sorted((j for j in range(4) if score[j]<0),key=lambda j:(score[j],j))
            for j,w in zip(ranked[:2],(-.42,-.20)):raw[0,j]=w
        else:
            best=min(range(4),key=lambda j:(-score[j],j))
            worst=min(range(4),key=lambda j:(score[j],j))
            if score[best]>0 and r168[best]>0:raw[0,best]=.35
            elif score[worst]<0 and r168[worst]<0:raw[0,worst]=-.30
        ups=[j for j in (1,2,3) if mean_funding[j]<-.00005 and r24[j]>.04 and r168[j]>0]
        downs=[j for j in (1,2,3) if mean_funding[j]>.00015 and r24[j]<-.05 and r168[j]<0]
        if ups:raw[1,min(ups,key=lambda j:(-r24[j],j))]=.20
        elif downs:raw[1,min(downs,key=lambda j:(r24[j],j))]=-.20
        low=min((1,2,3),key=lambda j:(mean_funding[j],j))
        high=min((1,2,3),key=lambda j:(-mean_funding[j],j))
        if low!=high and mean_funding[high]-mean_funding[low]>.00015 and r168[low]-r168[high]>.04 and r168[low]>0:
            raw[2,low]=.12;raw[2,high]=-.12
        if r168[0]<-.10 and negative>=3:
            raw[3,0]=-.18
        elif r168[0]<-.10 and r24[0]>.035 and int(np.sum(r24>0))>=3:
            raw[3,0]=.18
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("PB_WEEKLY_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PB_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    room=min(.30,max(0.,.88-float(np.abs(held).sum())))
    for slot in PRIORITY[mode]:
        if slot not in active:continue
        wanted=float(np.abs(raw[slot]).sum())
        if wanted>0 and room>0:
            use=min(wanted,room)
            held[slot]=raw[slot]*(use/wanted)
            room-=use
    if float(np.abs(held).sum())>.88+1e-10 or float(np.abs(held[1:]).sum())>.30+1e-10:
        raise ValueError("PB_GROSS_BREACH")
    return held

def target_books(decisions):
    return {name:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for name,active in BOOKS.items()}

def synthetic_test():
    tt=np.arange(HOURS)[:,None];jj=np.arange(4)[None,:]
    c=100*np.exp(.00007*tt*(1+jj/8)+.04*np.sin(tt/79+jj)+.02*np.cos(tt/43+jj))
    rate=np.zeros_like(c)
    a=signals({"c":c,"rate":rate})
    modified=c.copy();modified[15000:]*=np.array([.7,1.5,.8,1.8])
    b=signals({"c":modified,"rate":rate})
    for t in CLOCK:
        if t<15000 and (a[t][1]!=b[t][1] or not np.array_equal(a[t][0],b[t][0])):
            raise ValueError("PB_FUTURE_LEAK")
    altered_rate=rate.copy();altered_rate[15000:]=.0003
    d=signals({"c":c,"rate":altered_rate})
    for t in CLOCK:
        if t<15000 and (a[t][1]!=d[t][1] or not np.array_equal(a[t][0],d[t][0])):
            raise ValueError("PB_FUTURE_FUNDING_LEAK")
    books=target_books(a)
    if len(books)!=5 or any(len(v)!=157 for v in books.values()):
        raise ValueError("PB_BOOK_CLOCK")
    return {"decision":"PASS_PB_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "previous_settled_funding_only":True}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from pb_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("PB_INDEPENDENT_DECISION_MISMATCH")
    print("PB_INDEPENDENT_DECISION_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=(tier=="base" and order=="carried_before_fill" and book=="PB_full")
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PB_CELL",tier,order,book,"PHYSICAL",row["passed"],
                      "CAGR",round(100*row.get("cagr",-1),3),"FAIL",row.get("failure",""),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill_oracle=independent_fills(d,ledger) if audit is not None else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            if not all(x["passed"] for x in group.values()):
                failures.append(tier+"/"+order+":physical")
                continue
            full=group["PB_full"];key=tier+"/"+order
            marginals[key]={slot:full["log_growth"]-group[book]["log_growth"]
                for slot,book in (("Opportunity","PB_minus_opportunity"),
                                  ("Relative_Value","PB_minus_RV"),
                                  ("Stress_Recovery","PB_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","PB_minus_opportunity"),
                              ("Relative_Value","PB_minus_RV"),
                              ("Stress_Recovery","PB_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    diff=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if diff<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill_oracle is None or fill_oracle["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills")
    out={"architecture":"PB","preregistration":"pb_funding_dislocation_prereg_20261031.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"audit":audit,"independent_decision_oracle":oracle,
         "independent_fill_oracle":fill_oracle,"gate_failures":failures,
         "decision":"REJECT_PB_TRAINING" if failures else "PASS_PROVISIONAL_PB_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PB_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
