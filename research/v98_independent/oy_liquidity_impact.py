#!/usr/bin/env python3
"""V98 OY: preregistered signed-liquidity price-impact seven-slot complete physical engine.
Exploratory exposed 2022-25 Clean-4 training ONLY. No benchmarks, 2026+, XRP or paper.
"""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
BOOKS={"OY_full":(0,1,2,3),"OY_core_only":(0,),
       "OY_minus_opportunity":(0,2,3),"OY_minus_RV":(0,1,3),
       "OY_minus_stress":(0,1,2)}
PRIORITY={"accumulation":(1,2,3),"distribution":(3,1,2),"mixed":(2,3,1)}
MULT={"accumulation":(1.,.75,.5),"distribution":(.75,1.,1.),
      "mixed":(.75,1.,.75)}

def signals(d):
    close=np.asarray(d["c"],float);volume=np.asarray(d["q"],float)
    if close.shape!=(HOURS,4) or volume.shape!=(HOURS,4) or not np.isfinite(close).all() or not np.isfinite(volume).all() or np.any(close<=0) or np.any(volume<0):
        raise ValueError("OY_SOURCE_CLOSE_VOLUME")
    logs=np.log(close);out={}
    for t in range(WARMUP,HOURS,STEP):
        r336=logs[t]-logs[t-336];r72=logs[t]-logs[t-72];r24=logs[t]-logs[t-24]
        returns336=np.diff(logs[t-336:t+1],axis=0)
        vol336=volume[t-335:t+1]
        pressure336=np.sum(np.sign(returns336)*vol336,axis=0)/np.maximum(np.sum(vol336,axis=0),1e-12)
        returns72=np.diff(logs[t-72:t+1],axis=0)
        vol72=volume[t-71:t+1]
        pressure72=np.sum(np.sign(returns72)*vol72,axis=0)/np.maximum(np.sum(vol72,axis=0),1e-12)
        recent=np.mean(volume[t-23:t+1],axis=0)
        prior=np.mean(volume[t-191:t-23],axis=0)
        volume_ratio=recent/np.maximum(prior,1e-12)
        positive=int(np.sum((pressure336>0)&(r336>0)))
        negative=int(np.sum((pressure336<0)&(r336<0)))
        mode=("accumulation" if positive>=3 else
              "distribution" if negative>=3 else "mixed")
        raw=np.zeros((4,4),float)
        score=pressure336*np.abs(r336)
        if mode=="accumulation":
            candidates=sorted((k for k in range(4) if pressure336[k]>0 and r336[k]>0),
                              key=lambda k:(-score[k],k))
            for k,w in zip(candidates[:2],(.42,.24)):raw[0,k]=w
        elif mode=="distribution":
            candidates=sorted((k for k in range(4) if pressure336[k]<0 and r336[k]<0),
                              key=lambda k:(score[k],k))
            for k,w in zip(candidates[:2],(-.34,-.20)):raw[0,k]=w
        else:
            long_eligible=[k for k in range(4) if pressure336[k]>.10 and r336[k]>0 and r72[k]>0]
            short_eligible=[k for k in range(4) if pressure336[k]<-.10 and r336[k]<0 and r72[k]<0]
            if long_eligible:
                k=min(long_eligible,key=lambda k:(-score[k],k));raw[0,k]=.30
            elif short_eligible:
                k=min(short_eligible,key=lambda k:(score[k],k));raw[0,k]=-.24
        ups=[k for k in range(4) if volume_ratio[k]>1.4 and r24[k]>.035 and r72[k]>0 and pressure336[k]>0]
        downs=[k for k in range(4) if volume_ratio[k]>1.4 and r24[k]<-.035 and r72[k]<0 and pressure336[k]<0]
        if ups:
            k=min(ups,key=lambda k:(-r24[k],k));raw[1,k]=.18
        elif downs:
            k=min(downs,key=lambda k:(r24[k],k));raw[1,k]=-.18
        residual=r72[1:]-r72[0]
        longs=[k for k in range(1,4) if residual[k-1]>.07 and pressure72[k]>0]
        shorts=[k for k in range(1,4) if residual[k-1]<-.07 and pressure72[k]<0]
        if longs and shorts:
            hi=min(longs,key=lambda k:(-residual[k-1],k))
            lo=min(shorts,key=lambda k:(residual[k-1],k))
            raw[2,hi]=.12;raw[2,lo]=-.12
        if int(np.sum(r72<-.08))>=3 and int(np.sum(volume_ratio>1.25))>=3 and int(np.sum(r24>0))>=3:
            k=min(range(4),key=lambda k:(-r24[k],k));raw[3,k]=.16
        elif int(np.sum(r24<-.06))>=3 and r72[0]<-.07 and volume_ratio[0]>1.25:
            raw[3,0]=-.16
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("OY_WEEKLY_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("OY_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    room=min(.30,max(0.,.90-float(np.abs(held).sum())))
    for slot in PRIORITY[mode]:
        if slot not in active:continue
        wanted=float(np.abs(raw[slot]).sum())
        if wanted>0 and room>0:
            used=min(wanted,room)
            held[slot]=raw[slot]*(used/wanted)
            room-=used
    if float(np.abs(held).sum())>.90+1e-10 or float(np.abs(held[1:]).sum())>.30+1e-10:
        raise ValueError("OY_GROSS_BREACH")
    return held

def target_books(decisions):
    return {book:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for book,active in BOOKS.items()}

def synthetic_test():
    tt=np.arange(HOURS)[:,None];jj=np.arange(4)[None,:]
    close=100*np.exp(.000035*tt*(1+jj/10)+.06*np.sin(tt/67+jj)+.015*np.cos(tt/19+jj*2))
    volume=1e6*(1+.15*np.sin(tt/29+jj))
    a=signals({"c":close,"q":volume})
    future=close.copy();future[15000:]*=np.array([1.4,.7,1.2,.9])
    b=signals({"c":future,"q":volume})
    for t in a:
        if t<15000 and (a[t][1]!=b[t][1] or not np.allclose(a[t][0],b[t][0],atol=1e-12,rtol=0)):
            raise ValueError("OY_FUTURE_LEAK")
    books=target_books(a)
    if len(books)!=5 or any(len(book)!=157 for book in books.values()):
        raise ValueError("OY_SYNTHETIC_BOOK_CLOCK")
    return {"decision":"PASS_OY_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from oy_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("OY_INDEPENDENT_DECISION_MISMATCH")
    print("OY_INDEPENDENT_DECISION_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=(tier=="base" and order=="carried_before_fill" and book=="OY_full")
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("OY_CELL",tier,order,book,"PHYSICAL",row["passed"],
                      "CAGR",round(100*row.get("cagr",-1),3),"FAIL",row.get("failure",""),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill_oracle=independent_fills(d,ledger) if audit is not None else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            if not all(x["passed"] for x in group.values()):
                failures.append(tier+"/"+order+":physical");continue
            full=group["OY_full"];key=tier+"/"+order
            marginals[key]={slot:full["log_growth"]-group[book]["log_growth"]
                for slot,book in (("Opportunity","OY_minus_opportunity"),
                                  ("Relative_Value","OY_minus_RV"),
                                  ("Stress_Recovery","OY_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","OY_minus_opportunity"),
                              ("Relative_Value","OY_minus_RV"),
                              ("Stress_Recovery","OY_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    diff=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if diff<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill_oracle is None or fill_oracle["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills")
    out={"architecture":"OY","preregistration":"oy_liquidity_impact_prereg_20261031.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"audit":audit,"independent_decision_oracle":oracle,
         "independent_fill_oracle":fill_oracle,"gate_failures":failures,
         "decision":"REJECT_OY_TRAINING" if failures else "PASS_PROVISIONAL_OY_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("OY_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
