#!/usr/bin/env python3
"""PJ seven-slot channel propagation, preregistered EXPOSED Clean-4 training only."""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate, physical, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP
from ot_independent_oracle import independent_fills

CLOCK=tuple(range(WARMUP,HOURS,STEP))
BOOKS={"PJ_full":(0,1,2,3),"PJ_core_only":(0,),
       "PJ_minus_opportunity":(0,2,3),"PJ_minus_RV":(0,1,3),
       "PJ_minus_stress":(0,1,2)}
PRIORITY={"breakout":(1,2,3),"shock":(3,2,1),"range":(2,1,3)}

def signals(d):
    c=np.asarray(d["c"],float); h=np.asarray(d["h"],float)
    l=np.asarray(d["l"],float); q=np.asarray(d["q"],float)
    rate=np.asarray(d["rate"],float); event=np.asarray(d["event"],bool)
    if (any(a.shape!=(HOURS,4) for a in (c,h,l,q,rate,event))
        or not all(np.isfinite(a).all() for a in (c,h,l,q,rate))
        or np.any(c<=0) or np.any(l<=0) or np.any(q<0)
        or np.any(h<np.maximum(c,l)) or np.any(rate[~event]!=0)):
        raise ValueError("PJ_SOURCE_GEOMETRY")
    p=np.log(c); out={}
    for t in CLOCK:
        r24=p[t]-p[t-24]; r72=p[t]-p[t-72]
        r168=p[t]-p[t-168]; r336=p[t]-p[t-336]
        vol24=np.sum(q[t-23:t+1],axis=0)
        volprev=np.sum(q[t-167:t-23],axis=0)/6.
        valid=volprev>0
        up=(c[t]>np.max(h[t-168:t],axis=0)) & (r336>0) & valid & (vol24>1.15*volprev)
        down=(c[t]<np.min(l[t-168:t],axis=0)) & (r336<0) & valid & (vol24>1.15*volprev)
        sigma=np.std(np.diff(p[t-336:t+1],axis=0),axis=0)*math.sqrt(336)
        quality=np.abs(r336)/np.maximum(sigma,.04)
        raw=np.zeros((4,4),float)
        eligible=sorted((j for j in range(4) if up[j] or down[j]),key=lambda j:(-quality[j],j))
        for j,w in zip(eligible[:2],(.42,.24)):
            raw[0,j]=w if up[j] else -w
        if valid[0] and vol24[0]>1.4*volprev[0]:
            if r24[0]>.045:
                opts=[j for j in (1,2,3) if r72[j]>0 and r24[j]>0]
                if opts:raw[1,min(opts,key=lambda j:(-r24[j],j))]=.22
            elif r24[0]<-.045:
                opts=[j for j in (1,2,3) if r72[j]<0 and r24[j]<0]
                if opts:raw[1,min(opts,key=lambda j:(r24[j],j))]=-.22
        hr=np.diff(p[t-336:t+1],axis=0)
        btc=hr[:,0]; variance=float(np.var(btc))
        beta=np.array([float(np.mean((hr[:,j]-np.mean(hr[:,j]))*(btc-np.mean(btc))))/max(variance,1e-8) for j in range(4)])
        beta=np.clip(beta,0.,2.)
        residual=r168-beta*r168[0]
        hi=min((1,2,3),key=lambda j:(-residual[j],j))
        lo=min((1,2,3),key=lambda j:(residual[j],j))
        if (hi!=lo and residual[hi]-residual[lo]>.12 and residual[hi]>.04
            and residual[lo]<-.04 and r24[hi]>r24[lo]):
            raw[2,hi]=.13;raw[2,lo]=-.13
        if valid[0] and vol24[0]>1.3*volprev[0]:
            if r72[0]<-.09 and c[t,0]<np.min(l[t-336:t,0]):
                raw[3,0]=-.20
            elif r336[0]<-.18 and r24[0]>.065:
                raw[3,0]=.20
        mode=("breakout" if len(eligible)>=2 else
              "shock" if r72[0]<-.09 else "range")
        out[t]=(raw,mode,(up,down,residual))
    if len(out)!=157:raise ValueError("PJ_CLOCK")
    return out

def allocate(raw,mode,active,history):
    if (raw.shape!=(4,4) or history.shape!=(168,4) or mode not in PRIORITY
        or not np.isfinite(raw).all() or not np.isfinite(history).all()):
        raise ValueError("PJ_ALLOCATOR_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    core=float(np.abs(held[0]).sum())
    if core>.66+1e-10:raise ValueError("PJ_CORE_GROSS")
    room=min(.30,max(0.,.84-core))
    for slot in PRIORITY[mode]:
        if slot not in active or room<=1e-12:continue
        gross=float(np.abs(raw[slot]).sum())
        if gross<=1e-12:continue
        candidate=history@raw[slot]
        current=history@held.sum(axis=0)
        if np.std(candidate)>1e-12 and np.std(current)>1e-12:
            corr=float(np.corrcoef(candidate,current)[0,1])
        else:corr=0.
        if not math.isfinite(corr):raise ValueError("PJ_NONFINITE_CORRELATION")
        take=min(room,gross*(.5 if corr>.45 else 1.))
        held[slot]=raw[slot]*(take/gross)
        room-=take
    if np.abs(held).sum()>.84+1e-10 or np.abs(held[1:]).sum()>.30+1e-10:
        raise ValueError("PJ_GROSS")
    return held

def target_books(d,decisions):
    p=np.log(np.asarray(d["c"],float))
    return {name:{t:allocate(raw,mode,active,np.diff(p[t-168:t+1],axis=0))
                  for t,(raw,mode,_) in decisions.items()}
            for name,active in BOOKS.items()}

def synthetic_test():
    time=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00003*time*(1+j/5)+.09*np.sin(time/53+j))
    q=np.broadcast_to(10000*(1+.4*np.sin(time/17+j)),(HOURS,4)).copy()
    d={"c":c,"h":c*1.012,"l":c*.988,"q":q,
       "rate":np.zeros((HOURS,4)),"event":np.zeros((HOURS,4),bool)}
    first=signals(d)
    other={k:v.copy() for k,v in d.items()}
    for k in ("c","h","l"):other[k][15000:]*=np.array([1.3,.8,1.5,.7])
    other["q"][15000:]*=2.
    other["event"][15000::8]=True
    other["rate"][15000::8]=.03
    second=signals(other)
    for t in CLOCK:
        if t>=15000:continue
        a,b=first[t],second[t]
        if a[1]!=b[1] or not np.array_equal(a[0],b[0]) or any(not np.array_equal(x,y) for x,y in zip(a[2],b[2])):
            raise ValueError("PJ_FUTURE_LEAK")
    books=target_books(d,first)
    if len(books)!=5 or any(len(b)!=157 for b in books.values()) or any(np.abs(w).sum()>.84+1e-10 for b in books.values() for w in b.values()):
        raise ValueError("PJ_BOOK_GROSS")
    return {"decision":"PASS_PJ_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "books":5,"future_mutation_safe":True,"pnl_computed":False}

def run(d):
    source=source_gate(d)
    decisions=signals(d)
    books=target_books(d,decisions)
    from pj_channel_propagation_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["mismatches"]:raise ValueError("PJ_INDEPENDENT_ORACLE")
    print("PJ_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PJ_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PJ_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    accounting=independent_accounting(d,ledger) if ledger is not None and len(ledger)==HOURS-WARMUP-1 else None
    fills=independent_fills(d,ledger) if accounting is not None else None
    failures=[];marginals={}
    slots=(("Opportunity","PJ_minus_opportunity"),("Relative_Value","PJ_minus_RV"),("Stress_Recovery","PJ_minus_stress"))
    for tier in COSTS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["PJ_full"]
            marginals[label]={slot:full["log_growth"]-group[book]["log_growth"] for slot,book in slots}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(label+":CAGR")
            if full["turnover"]>1000000:failures.append(label+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(label+":drawdown")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(label+":annual")
            for slot,book in slots:
                if marginals[label][slot]<=.02:failures.append(label+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    delta=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if delta<-.03:failures.append(label+":"+slot+":"+year+":annual_marginal")
    if accounting is None or accounting["cash_identity_mismatches"]:failures.append("independent_hourly_accounting")
    if fills is None or fills["independent_fee_slippage_funding_mismatches"]:failures.append("independent_fills_and_funding")
    out={"architecture":"PJ","preregistration":"pj_channel_propagation_prereg_20261101.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"independent_decision_oracle":oracle,
         "independent_accounting":accounting,"independent_fills":fills,
         "gate_failures":failures,
         "decision":"REJECT_PJ_TRAINING" if failures else "PASS_PROVISIONAL_PJ_TRAINING_NOT_VALIDATED",
         "2025_exposed_training_only":True,"exact_event_mark_attested":False,
         "2026_plus_accessed":False,"holdout_accessed":False,
         "external_benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PJ_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
