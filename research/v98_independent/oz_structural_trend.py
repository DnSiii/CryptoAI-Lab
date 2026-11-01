#!/usr/bin/env python3
"""V98 OZ preregistered structural trend / crisis convexity seven-slot complete engine.
Only exposed Clean-4 2022-25 training; no V99/benchmarks/2026+/paper/holdout.
"""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate, physical, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP
from ot_independent_oracle import independent_fills

BOOKS={"OZ_full":(0,1,2,3),"OZ_core_only":(0,),
       "OZ_minus_opportunity":(0,2,3),"OZ_minus_RV":(0,1,3),
       "OZ_minus_stress":(0,1,2)}
PRIORITY={"trend":(1,2,3),"stress":(3,2,1),"transition":(3,1,2)}
MULT={"trend":(1.,1.,.50),"stress":(.50,.50,1.),"transition":(.50,.75,.75)}
CLOCK=tuple(range(WARMUP,HOURS,STEP))

def signals(d):
    c=np.asarray(d["c"],float)
    if c.shape!=(HOURS,4) or not np.isfinite(c).all() or np.any(c<=0):
        raise ValueError("OZ_BAD_CLOSE_SOURCE")
    p=np.log(c);out={}
    for t in CLOCK:
        raw=np.zeros((4,4),float)
        if t<1344:
            out[t]=(raw,"transition")
            continue
        r1344=p[t]-p[t-1344]
        r672=p[t]-p[t-672]
        r168=p[t]-p[t-168]
        r24=p[t]-p[t-24]
        hourly=np.diff(p[t-672:t+1],axis=0)
        volatility=np.std(hourly,axis=0)*math.sqrt(24*365.25)
        score=.60*r1344+.40*r672
        mode=("trend" if r672[0]>0 and int(np.sum(score>0))>=2 else
              "stress" if r672[0]<0 and int(np.sum(r672<0))>=3 else "transition")
        if mode=="trend":
            eligible=[j for j in range(4) if score[j]>0]
            ranked=sorted(eligible,key=lambda j:(-score[j]/max(float(volatility[j]),.04),j))
            for j,w in zip(ranked[:2],(.42,.25)):raw[0,j]=w
        elif mode=="stress":
            raw[0,0]=-.35
            worst=min((1,2,3),key=lambda j:(r672[j],j))
            raw[0,worst]=-.18
        elif r168[0]>0 and r672[0]>0:
            raw[0,0]=.20
        candidates=[]
        for j in (1,2,3):
            prior_high=float(np.max(p[t-168:t,j]))
            recent_range=float(np.max(p[t-167:t+1,j])-np.min(p[t-167:t+1,j]))
            if recent_range<.20 and p[t,j]>prior_high and score[j]>0 and r24[j]>0:
                candidates.append(j)
        if candidates:
            j=min(candidates,key=lambda j:(-score[j],j))
            raw[1,j]=.16
        top=min((1,2,3),key=lambda j:(-r672[j],j))
        bottom=min((1,2,3),key=lambda j:(r672[j],j))
        if top!=bottom and r672[top]-r672[bottom]>.30 and r168[top]>0 and r168[bottom]<0 and r672[0]>0:
            raw[2,top]=.10;raw[2,bottom]=-.10
        btc_drawdown=float(p[t,0]-np.max(p[t-672:t+1,0]))
        if btc_drawdown<math.log(.80) and int(np.sum(r168<0))>=3:
            raw[3,0]=-.16
        elif r168[0]<-.12 and r24[0]>0 and int(np.sum(r24>0))>=3:
            raw[3,0]=.16
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("OZ_WEEKLY_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("OZ_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    room=min(.28,max(0.,.84-float(np.abs(held).sum())))
    for slot in PRIORITY[mode]:
        if slot not in active:continue
        wanted=float(np.abs(raw[slot]).sum())
        if wanted>0 and room>0:
            use=min(wanted,room)
            held[slot]=raw[slot]*(use/wanted)
            room-=use
    if float(np.abs(held).sum())>.84+1e-10 or float(np.abs(held[1:]).sum())>.28+1e-10:
        raise ValueError("OZ_GROSS_BREACH")
    return held

def target_books(decisions):
    return {name:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for name,active in BOOKS.items()}

def synthetic_test():
    tt=np.arange(HOURS)[:,None];jj=np.arange(4)[None,:]
    c=100*np.exp(.00007*tt*(1+jj/8)+.04*np.sin(tt/79+jj)+.02*np.cos(tt/43+jj))
    a=signals({"c":c})
    modified=c.copy();modified[15000:]*=np.array([.7,1.5,.8,1.8])
    b=signals({"c":modified})
    for t in CLOCK:
        if t<15000 and (a[t][1]!=b[t][1] or not np.array_equal(a[t][0],b[t][0])):
            raise ValueError("OZ_FUTURE_LEAK")
    if any(np.any(a[t][0]) for t in CLOCK[:4]):
        raise ValueError("OZ_COLD_START_LEAK")
    books=target_books(a)
    if len(books)!=5 or any(len(v)!=157 for v in books.values()):
        raise ValueError("OZ_BOOK_CLOCK")
    return {"decision":"PASS_OZ_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "cold_start_cash_decisions":4}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from oz_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("OZ_INDEPENDENT_DECISION_MISMATCH")
    print("OZ_INDEPENDENT_DECISION_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=(tier=="base" and order=="carried_before_fill" and book=="OZ_full")
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("OZ_CELL",tier,order,book,"PHYSICAL",row["passed"],
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
            full=group["OZ_full"];key=tier+"/"+order
            marginals[key]={slot:full["log_growth"]-group[book]["log_growth"]
                for slot,book in (("Opportunity","OZ_minus_opportunity"),
                                  ("Relative_Value","OZ_minus_RV"),
                                  ("Stress_Recovery","OZ_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","OZ_minus_opportunity"),
                              ("Relative_Value","OZ_minus_RV"),
                              ("Stress_Recovery","OZ_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    diff=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if diff<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill_oracle is None or fill_oracle["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills")
    out={"architecture":"OZ","preregistration":"oz_structural_trend_prereg_20261031.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"audit":audit,"independent_decision_oracle":oracle,
         "independent_fill_oracle":fill_oracle,"gate_failures":failures,
         "decision":"REJECT_OZ_TRAINING" if failures else "PASS_PROVISIONAL_OZ_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("OZ_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
