#!/usr/bin/env python3
"""Independent scalar PF decision, net-contribution and allocator oracle.
No import of PF signals/allocator; checks source -> decisions -> five books.
No PnL, 2026+, external benchmarks, holdout, paper or live.
"""
import math,statistics
import numpy as np

CLOCK=tuple(range(744,27048,168))
BOOKS={"PF_full":(0,1,2,3),"PF_core_only":(0,),
       "PF_minus_opportunity":(0,2,3),"PF_minus_RV":(0,1,3),
       "PF_minus_stress":(0,1,2)}

def logratio(a,b):return math.log(float(a)/float(b))
def mean(values):return sum(values)/len(values)
def var(values):
    m=mean(values)
    return sum((x-m)**2 for x in values)/len(values)

def independent_decisions(d,decisions,books):
    c=d["c"];h=d["h"];l=d["l"];rate=d["rate"];event=d["event"]
    history={1:[],2:[],3:[]};previous_raw={}
    mismatches=0;max_error=0.;score_errors=0
    if set(decisions)!=set(CLOCK) or set(books)!=set(BOOKS):
        raise ValueError("PF_ORACLE_DECISION_CLOCK_OR_BOOKS")
    for t in CLOCK:
        r672=[logratio(c[t,j],c[t-672,j]) for j in range(4)]
        r168=[logratio(c[t,j],c[t-168,j]) for j in range(4)]
        r48=[logratio(c[t,j],c[t-48,j]) for j in range(4)]
        vol=[]
        for j in range(4):
            returns=[logratio(c[i,j],c[i-1,j]) for i in range(t-335,t+1)]
            vol.append(math.sqrt(var(returns)))
        quality=[r672[j]/max(vol[j],1e-5) for j in range(4)]
        raw=[[0.]*4 for _ in range(4)]
        if r672[0]>0:
            rank=sorted((j for j in range(4) if r672[j]>0),key=lambda j:(-quality[j],j))
            for j,w in zip(rank[:2],(.30,.20)):raw[0][j]=w
        elif r672[0]<0:
            rank=sorted((j for j in range(4) if r672[j]<0),key=lambda j:(quality[j],j))
            for j,w in zip(rank[:2],(-.30,-.20)):raw[0][j]=w
        eligible=[]
        for j in range(4):
            recent=mean([(float(h[i,j])-float(l[i,j]))/float(c[i,j])
                         for i in range(t-167,t+1)])
            prior=mean([(float(h[i,j])-float(l[i,j]))/float(c[i,j])
                        for i in range(t-671,t-167)])
            if prior>0 and recent<.70*prior and abs(r48[j])>.03:eligible.append(j)
        if eligible:
            j=min(eligible,key=lambda j:(-abs(r48[j]),j))
            raw[1][j]=math.copysign(.20,r48[j])
        btc=[logratio(c[i,0],c[i-1,0]) for i in range(t-671,t+1)]
        bmean=mean(btc);bcenter=[v-bmean for v in btc]
        bvar=sum(v*v for v in bcenter)
        residuals=[]
        if bvar>1e-12:
            for j in (1,2,3):
                alt=[logratio(c[i,j],c[i-1,j]) for i in range(t-671,t+1)]
                amean=mean(alt)
                beta=sum(x*(y-amean) for x,y in zip(bcenter,alt))/bvar
                beta=max(0.,min(1.5,beta))
                residual=r168[j]-beta*r168[0]
                if abs(residual)>=.04:residuals.append((abs(residual),j,residual,beta))
        if residuals:
            _,j,residual,beta=min(residuals,key=lambda x:(-x[0],x[1]))
            raw[2][j]=-math.copysign(.16,residual)
            raw[2][0]=-raw[2][j]*beta
        if sum(v<-.07 for v in r168)>=3:
            if sum(v>0 for v in r48)>=3:raw[3][0]=.20
            else:
                j=min(range(4),key=lambda j:(r48[j],j))
                raw[3][j]=-.20
        prev=t-168
        if prev in previous_raw:
            for k in (1,2,3):
                w=previous_raw[prev][k]
                weekly=sum(w[j]*(float(c[t,j])/float(c[prev,j])-1.) for j in range(4))
                fr=sum(w[j]*sum(float(rate[i,j]) for i in range(prev+1,t+1)
                                if bool(event[i,j])) for j in range(4))
                estimated=weekly-fr-.004*sum(abs(x) for x in w)
                history[k].append(estimated)
                if len(history[k])>8:history[k].pop(0)
        scores={k:(mean(history[k]) if len(history[k])>=4 else float("-inf")) for k in (1,2,3)}
        recent_btc=[logratio(c[i,0],c[i-1,0]) for i in range(t-167,t+1)]
        prior_btc=[logratio(c[i,0],c[i-1,0]) for i in range(t-670,t-167)]
        mode="stress" if var(prior_btc)>0 and var(recent_btc)>1.5*var(prior_btc) else "normal"
        original,reported_mode,reported_scores=decisions[t]
        err=float(np.max(np.abs(np.asarray(raw)-original)))
        max_error=max(max_error,err)
        if err>1e-9 or reported_mode!=mode:mismatches+=1
        for k in (1,2,3):
            if math.isinf(scores[k]) and math.isinf(reported_scores[k]):continue
            if abs(scores[k]-reported_scores[k])>1e-9:score_errors+=1
        ties=(3,1,2) if mode=="stress" else (1,2,3)
        priority=sorted((1,2,3),key=lambda k:(-scores[k],ties.index(k)))
        for name,active in BOOKS.items():
            held=[[0.]*4 for _ in range(4)]
            if 0 in active:held[0]=raw[0][:]
            room=min(.34,max(0.,.84-sum(abs(v) for v in held[0])))
            for k in priority:
                if k not in active or not scores[k]>0:continue
                gross=sum(abs(v) for v in raw[k])
                if gross>0 and room>0:
                    fraction=min(room,gross)/gross
                    held[k]=[v*fraction for v in raw[k]]
                    room-=min(room,gross)
            error=float(np.max(np.abs(np.asarray(held)-books[name][t])))
            max_error=max(max_error,error)
            if error>1e-9:mismatches+=1
        previous_raw[t]=raw
    return {"weekly_decisions":len(CLOCK),"books":len(BOOKS),
            "signal_and_allocation_mismatches":mismatches+score_errors,
            "source_signal_mismatches":mismatches,
            "causal_net_score_mismatches":score_errors,
            "max_weight_error":max_error,
            "independent_scalar_source_reconstruction":True,
            "training_only":True}
