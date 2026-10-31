#!/usr/bin/env python3
"""V98 OU preregistered complete seven-slot 2022-25 TRAINING-only system.
Reuses V98 OT *physical execution/accounting mechanics*, never OT signals/parameters.
2025 exposed; no future/holdout, benchmarks, exact-mark, paper or live claims.
"""
import json,math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
BOOKS={
 "OU_full":(0,1,2,3),
 "OU_core_only":(0,),
 "OU_minus_opportunity":(0,2,3),
 "OU_minus_RV":(0,1,3),
 "OU_minus_stress":(0,1,2),
}
PRIORITY={"shock":(3,2,1),"trend":(1,2,3),"range":(2,1,3)}
MULT={"shock":(.5,1.,1.),"trend":(1.,.75,.5),"range":(.75,1.,.75)}

def signals(d):
    c=np.asarray(d["c"]);p=np.log(c);h=np.asarray(d["h"]);l=np.asarray(d["l"])
    q=np.asarray(d["q"]);rate=np.asarray(d["rate"]);event=np.asarray(d["event"])
    result={}
    for t in range(WARMUP,HOURS,STEP):
        r336=p[t]-p[t-336];r72=p[t]-p[t-72]
        r24=p[t]-p[t-24];r12=p[t]-p[t-12]
        sigma336=np.std(np.diff(p[t-336:t+1],axis=0),axis=0)
        sigma72=np.std(np.diff(p[t-72:t+1],axis=0),axis=0)
        ratio=float(np.median(sigma72)/max(float(np.median(sigma336)),1e-9))
        med=float(np.median(r336))
        agreement=int(np.sum((r336>0) if med>0 else (r336<0))) if med!=0 else 0
        mode="shock" if ratio>=1.25 else ("trend" if agreement>=3 else "range")
        raw=np.zeros((4,4),float)
        eligible=[j for j in range(4) if r336[j]*r72[j]>0]
        if eligible:
            score=np.abs(r336)/np.maximum(sigma336*np.sqrt(336),.03)
            j=min(eligible,key=lambda k:(-score[k],k))
            raw[0,j]=.62 if r336[j]>0 else -.62
        recent_q=np.sum(q[t-23:t+1],axis=0)
        avg_q=np.sum(q[t-168:t],axis=0)/7.
        ups=c[t]>np.max(h[t-72:t],axis=0)
        downs=c[t]<np.min(l[t-72:t],axis=0)
        eligible=[j for j in range(4) if recent_q[j]>1.4*avg_q[j] and (ups[j] or downs[j])]
        if eligible:
            j=min(eligible,key=lambda k:(-abs(r24[k]),k))
            raw[1,j]=.16 if ups[j] else -.16
        # Only settled historical 8h funding events through the decision hour.
        past=rate[t-160:t+1:8]
        if past.shape!=(21,4) or not np.all(event[t-160:t+1:8]):
            raise ValueError("OU_CAUSAL_FUNDING_HISTORY")
        avg=np.mean(past,axis=0)
        hi=min(range(4),key=lambda k:(-avg[k],k))
        lo=min(range(4),key=lambda k:(avg[k],k))
        if avg[hi]-avg[lo]>.00005:
            raw[2,hi]=-.12;raw[2,lo]=+.12
        if int(np.sum(r24<-.05))>=3 and int(np.sum(r12>0))>=3:
            j=min(range(4),key=lambda k:(r72[k],k));raw[3,j]=+.16
        elif int(np.sum(r24<-.07))>=3 and int(np.sum(r12<0))>=3:
            j=min(range(4),key=lambda k:(r72[k],k));raw[3,j]=-.16
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        result[t]=(raw,mode)
    if len(result)!=157:raise ValueError("OU_DECISION_CLOCK")
    return result

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("OU_ALLOC_INPUT")
    held=np.zeros((4,4))
    if 0 in active:held[0]=raw[0]
    room=min(.22,max(0.,.84-float(np.abs(held).sum())))
    for k in PRIORITY[mode]:
        if k not in active:continue
        gross=float(np.abs(raw[k]).sum())
        if gross>0 and room>0:
            use=min(room,gross);held[k]=raw[k]*(use/gross);room-=use
    if float(np.abs(held).sum())>.84+1e-10 or float(np.abs(held[1:]).sum())>.22+1e-10:
        raise ValueError("OU_ALLOC_GROSS")
    return held

def target_books(decisions):
    return {name:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for name,active in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS)[:,None];j=np.arange(4)[None,:]
    c=100*np.exp(.00007*t*(1+j/10)+.08*np.sin(t/67+j))
    d={"c":c,"h":c*1.01,"l":c*.99,"q":np.ones_like(c)*1e6,
       "rate":np.zeros_like(c),"event":np.tile((np.arange(HOURS)%8==0)[:,None],(1,4))}
    before=signals(d)
    altered={k:v.copy() for k,v in d.items()}
    for k in ("c","h","l"):altered[k][15000:]*=1.5
    altered["q"][15000:]*=2.
    altered["rate"][15000:]=.001
    after=signals(altered)
    for t in before:
        if t<15000 and (not np.array_equal(before[t][0],after[t][0]) or before[t][1]!=after[t][1]):
            raise ValueError("OU_FUTURE_LEAK")
    for name,targets in target_books(before).items():
        if len(targets)!=157 or any(float(np.abs(w).sum())>.84+1e-10 for w in targets.values()):
            raise ValueError("OU_SYNTHETIC_ALLOC_"+name)
    return {"decision":"PASS_OU_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157}

def run(d):
    source=source_gate(d)
    decision=signals(d);targets=target_books(decision)
    from ou_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decision,targets)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("OU_INDEPENDENT_SIGNAL_ALLOC_MISMATCH")
    print("OU_INDEPENDENT_DECISION_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=book=="OU_full" and tier=="base" and order=="carried_before_fill"
                row,detail=physical(d,targets[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("OU_CELL",tier,order,book,"PHYSICAL",row["passed"],
                      "CAGR",round(100*row.get("cagr",-1),3),
                      "FAIL",row.get("failure",""),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill_oracle=independent_fills(d,ledger) if audit is not None else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            if not all(x["passed"] for x in group.values()):
                failures.append(tier+"/"+order+":physical");continue
            full=group["OU_full"]
            marginals[tier+"/"+order]={s:full["log_growth"]-group[book]["log_growth"]
                for s,book in (("Opportunity","OU_minus_opportunity"),
                               ("Relative_Value","OU_minus_RV"),("Stress_Recovery","OU_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(tier+"/"+order+":CAGR")
            if full["turnover"]>1_000_000:failures.append(tier+"/"+order+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(tier+"/"+order+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(tier+"/"+order+":annual")
            for sleeve,book in (("Opportunity","OU_minus_opportunity"),
                                ("Relative_Value","OU_minus_RV"),("Stress_Recovery","OU_minus_stress")):
                if marginals[tier+"/"+order][sleeve]<=.02:
                    failures.append(tier+"/"+order+":"+sleeve+":marginal")
                for y in ("2023","2024","2025"):
                    diff=math.log1p(full["year_returns"][y])-math.log1p(group[book]["year_returns"][y])
                    if diff<-.03:failures.append(tier+"/"+order+":"+sleeve+":"+y+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill_oracle is None or fill_oracle["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills")
    out={"architecture":"OU","preregistration":"ou_volatility_expansion_prereg_20261031.md",
         "source":source,"weekly_decisions":len(decision),"cells":cells,
         "marginals":marginals,"audit":audit,"independent_decision_oracle":oracle,
         "independent_fill_oracle":fill_oracle,"gate_failures":failures,
         "decision":"REJECT_OU_TRAINING" if failures else "PASS_PROVISIONAL_OU_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("OU_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
