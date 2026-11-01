#!/usr/bin/env python3
"""V98 PF: preregistered causal counterfactual capital competition.
Only exposed Clean-4 2022-25 training; never V14/V15/V99, 2026+, holdout or paper.
"""
import json,math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

BOOKS={"PF_full":(0,1,2,3),"PF_core_only":(0,),
       "PF_minus_opportunity":(0,2,3),"PF_minus_RV":(0,1,3),
       "PF_minus_stress":(0,1,2)}
CLOCK=tuple(range(WARMUP,HOURS,STEP))
SLEEVES=(1,2,3)
ESTIMATED_ROUNDTRIP_COST=2*(.001+.001)

def signals(d):
    c=np.asarray(d["c"],float);h=np.asarray(d["h"],float)
    l=np.asarray(d["l"],float);rate=np.asarray(d["rate"],float)
    event=np.asarray(d["event"],bool)
    if any(x.shape!=(HOURS,4) for x in (c,h,l,rate,event)):
        raise ValueError("PF_SOURCE_SHAPE")
    if not all(np.isfinite(x).all() for x in (c,h,l,rate)) or np.any(c<=0) or np.any(l<=0) or np.any(h<l):
        raise ValueError("PF_SOURCE_GEOMETRY")
    p=np.log(c)
    ranges=(h-l)/c
    out={};raw_history={};score_history={k:[] for k in SLEEVES}
    for t in CLOCK:
        r672=p[t]-p[t-672]
        r168=p[t]-p[t-168]
        r48=p[t]-p[t-48]
        r14=np.diff(p[t-336:t+1],axis=0)
        vol=np.std(r14,axis=0)
        quality=r672/np.maximum(vol,1e-5)
        raw=np.zeros((4,4),float)
        if r672[0]>0:
            eligible=sorted((j for j in range(4) if r672[j]>0),
                            key=lambda j:(-quality[j],j))
            for j,w in zip(eligible[:2],(.30,.20)):raw[0,j]=w
        elif r672[0]<0:
            eligible=sorted((j for j in range(4) if r672[j]<0),
                            key=lambda j:(quality[j],j))
            for j,w in zip(eligible[:2],(-.30,-.20)):raw[0,j]=w
        recent_range=np.mean(ranges[t-167:t+1],axis=0)
        prior_range=np.mean(ranges[t-671:t-167],axis=0)
        compressed=[j for j in range(4) if prior_range[j]>0
                    and recent_range[j]<.70*prior_range[j] and abs(r48[j])>.03]
        if compressed:
            j=min(compressed,key=lambda j:(-abs(r48[j]),j))
            raw[1,j]=math.copysign(.20,float(r48[j]))
        btc_ret=np.diff(p[t-672:t+1,0])
        btc_center=btc_ret-btc_ret.mean()
        btc_var=float(np.dot(btc_center,btc_center))
        residuals=[]
        if btc_var>1e-12:
            for j in (1,2,3):
                alt=np.diff(p[t-672:t+1,j])
                beta=float(np.dot(btc_center,alt-alt.mean())/btc_var)
                beta=float(np.clip(beta,0.,1.5))
                residual=float(r168[j]-beta*r168[0])
                if abs(residual)>=.04:
                    residuals.append((abs(residual),j,residual,beta))
        if residuals:
            _,j,residual,beta=min(residuals,key=lambda x:(-x[0],x[1]))
            raw[2,j]=-math.copysign(.16,residual)
            raw[2,0]=-raw[2,j]*beta
        if int(np.sum(r168<-.07))>=3:
            if int(np.sum(r48>0))>=3:
                raw[3,0]=.20
            else:
                j=min(range(4),key=lambda j:(r48[j],j))
                raw[3,j]=-.20
        prev=t-STEP
        if prev in raw_history:
            ret=c[t]/c[prev]-1.
            funding_rates=np.sum(np.where(event[prev+1:t+1],rate[prev+1:t+1],0.),axis=0)
            for k in SLEEVES:
                w=raw_history[prev][k]
                estimate=float(np.dot(w,ret)-np.dot(w,funding_rates)
                               -ESTIMATED_ROUNDTRIP_COST*np.abs(w).sum())
                score_history[k].append(estimate)
                if len(score_history[k])>8:score_history[k].pop(0)
        score={k:(float(np.mean(score_history[k])) if len(score_history[k])>=4
                  else float("-inf")) for k in SLEEVES}
        var_recent=float(np.var(np.diff(p[t-168:t+1,0])))
        var_prior=float(np.var(np.diff(p[t-671:t-167,0])))
        mode="stress" if var_prior>0 and var_recent>1.5*var_prior else "normal"
        out[t]=(raw,mode,score)
        raw_history[t]=raw.copy()
    if len(out)!=157:raise ValueError("PF_DECISION_CLOCK")
    return out

def allocate(raw,mode,score,active):
    if raw.shape!=(4,4) or mode not in ("normal","stress") or not np.isfinite(raw).all():
        raise ValueError("PF_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    core=float(np.abs(held[0]).sum())
    if core>.50+1e-10:raise ValueError("PF_CORE_CAP")
    room=min(.34,max(0.,.84-core))
    ties=(3,1,2) if mode=="stress" else (1,2,3)
    priority=sorted(SLEEVES,key=lambda k:(-score[k],ties.index(k)))
    for k in priority:
        if k not in active or not score[k]>0:continue
        gross=float(np.abs(raw[k]).sum())
        if gross>0 and room>0:
            take=min(room,gross)
            held[k]=raw[k]*(take/gross)
            room-=take
    if np.abs(held).sum()>.84+1e-10 or np.abs(held[1:]).sum()>.34+1e-10:
        raise ValueError("PF_GROSS")
    return held

def target_books(decisions):
    return {book:{t:allocate(raw,mode,score,active)
                  for t,(raw,mode,score) in decisions.items()}
            for book,active in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS)[:,None];j=np.arange(4)[None,:]
    c=100*np.exp(.00004*t*(1+j/7)+.07*np.sin(t/91+j))
    h=c*(1.012+.003*np.sin(t/19+j)**2)
    l=c*(.988-.003*np.cos(t/17+j)**2)
    event=np.broadcast_to((np.arange(HOURS)%8==0)[:,None],(HOURS,4)).copy()
    rate=np.broadcast_to((.00005*np.sin(np.arange(HOURS)/113)[:,None]+.00002*j),(HOURS,4)).copy()
    d={"c":c,"h":h,"l":l,"rate":rate,"event":event}
    a=signals(d)
    changed={k:v.copy() for k,v in d.items()}
    for k in ("c","h","l"):
        changed[k][15000:]*=np.array([1.4,.8,1.5,.6])
    changed["rate"][15000:]*=-4
    b=signals(changed)
    for t in CLOCK:
        if t<15000:
            x,y=a[t],b[t]
            if x[1]!=y[1] or not np.array_equal(x[0],y[0]) or x[2]!=y[2]:
                raise ValueError("PF_FUTURE_LEAK")
    books=target_books(a)
    if len(books)!=5 or any(len(v)!=157 for v in books.values()):
        raise ValueError("PF_BOOKS")
    if not all(np.isfinite(w).all() and np.abs(w).sum()<=.84+1e-10
               for book in books.values() for w in book.values()):
        raise ValueError("PF_SYNTHETIC_GROSS")
    return {"decision":"PASS_PF_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "future_price_and_funding_mutation_safe":True}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from pf_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("PF_INDEPENDENT_ORACLE_MISMATCH")
    print("PF_INDEPENDENT_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PF_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PF_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill=independent_fills(d,ledger) if audit else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            key=tier+"/"+order
            if not all(x["passed"] for x in group.values()):
                failures.append(key+":physical");continue
            full=group["PF_full"]
            marginals[key]={slot:full["log_growth"]-group[book]["log_growth"] for slot,book in (
                ("Opportunity","PF_minus_opportunity"),("Relative_Value","PF_minus_RV"),("Stress_Recovery","PF_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","PF_minus_opportunity"),("Relative_Value","PF_minus_RV"),("Stress_Recovery","PF_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    delta=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if delta<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill is None or fill["independent_fee_slippage_funding_mismatches"]:failures.append("independent_fills")
    out={"architecture":"PF","preregistration":"pf_causal_counterfactual_allocator_prereg_20261101.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,"marginals":marginals,
         "audit":audit,"independent_decision_oracle":oracle,"independent_fill_oracle":fill,
         "gate_failures":failures,"decision":"REJECT_PF_TRAINING" if failures else "PASS_PROVISIONAL_PF_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PF_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
