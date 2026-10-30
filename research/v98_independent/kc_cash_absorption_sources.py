#!/usr/bin/env python3
"""KC preregistered cash-market buyer absorption versus lagged USD-M OI, seven slots, training only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"NORMAL":.88,"STRESS":.70,"RECOVERY":.82}
PATHS=("KC_core_only","KC_full","KC_minus_opportunity","KC_minus_RV","KC_minus_stress")

def bundle(opening,high,low,close,rate,event,quote,oi,spot_buy,spot_quote,spot_valid):
    o,h,l,c,r,e,q,v,sb,sq=[np.asarray(x,dtype=float) for x in
                            (opening,high,low,close,rate,event,quote,oi,spot_buy,spot_quote)]
    sm=np.asarray(spot_valid,dtype=bool)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(z.shape!=c.shape for z in (o,h,l,r,e,q,v,sb,sq,sm)) or
        any(not np.isfinite(z).all() for z in (o,h,l,c,r,e,q)) or
        not np.isfinite(sb[sm]).all() or not np.isfinite(sq[sm]).all() or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1)) or
        np.any(v[np.isfinite(v)]<=0) or
        np.any(sq[sm]<=0) or np.any(sb[sm]<0) or
        np.any(sb[sm]>sq[sm]+1e-5*np.maximum(1.,sq[sm])) or
        not np.isnan(sb[~sm]).all() or not np.isnan(sq[~sm]).all()):
        raise ValueError("KC_INVALID_NATIVE_SPOT_OR_OI_SOURCE")
    n=len(c)
    ret=np.zeros_like(c)
    ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    market=np.mean(net,axis=1)
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    budgets=np.zeros((n,3),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        downside=np.maximum(np.sqrt(np.mean(np.minimum(net[t-335:t+1],0.)**2,axis=0)),.002)
        mom672=np.sum(net[t-671:t+1],axis=0)
        leaders=np.argsort(-(mom672/downside),kind="stable")[:2]
        core=np.zeros(4)
        inv=1./downside[leaders]
        core[leaders]=inv/inv.sum()
        experts=np.zeros((4,4))
        experts[0]=core
        m72=float(np.sum(market[t-71:t+1]))
        m24=float(np.sum(market[t-23:t+1]))
        mprev72=float(np.sum(market[t-95:t-23]))
        regime=("STRESS" if m72<-.03 else
                "RECOVERY" if m24>.012 and mprev72<0 else "NORMAL")
        good=bool(np.isfinite(v[t-337:t]).all() and
                  np.all(sm[t-167:t+1]))
        if good:
            den=np.sum(sq[t-167:t+1],axis=0)
            good=bool(np.all(den>0))
        valid[t]=good
        if good:
            share=np.sum(sb[t-167:t+1],axis=0)/den
            oi168=np.log(v[t-1]/v[t-169])
            oi72=np.log(v[t-1]/v[t-73])
            score=np.maximum(share-.5,0.)*np.maximum(-oi168,0.)
            if np.max(score)>0:
                experts[1,int(np.argmax(score))]=1.
                budgets[t,0]=.18
            spread_score=(share-.5)-.5*oi168
            if np.max(spread_score)-np.min(spread_score)>.02:
                long=int(np.argmax(spread_score));short=int(np.argmin(spread_score))
                if long!=short:
                    experts[2,long]=.5;experts[2,short]=-.5
                    budgets[t,1]=.12
            if regime=="STRESS":
                choose=int(np.argmax(share-.5*np.maximum(oi72,0.)))
            elif regime=="RECOVERY":
                choose=int(np.argmax(share))
            else:
                burden=np.sum((r*e)[t-167:t+1],axis=0)
                choose=int(np.argmax(share-burden))
            experts[3,choose]=1.
            budgets[t,2]=.10
        for path in range(5):
            b=budgets[t].copy()
            if path==0:b[:]=0.
            elif path>=2:b[path-2]=0.
            target=(1.-float(np.sum(b)))*core+b@experts[1:]
            if not np.isfinite(target).all() or np.abs(target).sum()>1.+1e-10 or np.sum(b)>.4+1e-12:
                raise ValueError("KC_GROSS_OR_FINITE")
            targets[t,path]=target
        if not good and not np.allclose(targets[t],targets[t,0]):
            raise ValueError("KC_SOURCE_QUARANTINE_LEAK")
        regimes[t]=regime
        updates[t]=True
    return targets,updates,regimes,valid,budgets

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    v=1e5*np.exp(t[:,None]*np.array([[.00001,.00002,.00003,.00004]])+
                 .1*np.sin(t[:,None]/79.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    sm=np.ones_like(c,dtype=bool);sm[2000:2002]=False
    sq=q.copy();sb=q*(.5+.12*np.sin(t[:,None]/101.+np.arange(4)))
    sq[~sm]=np.nan;sb[~sm]=np.nan
    a=bundle(o,h,l,c,r,e,q,v,sb,sq,sm)
    cc,oo,hh,ll,qq,rr,vv,ss,bb=[z.copy() for z in (c,o,h,l,q,r,v,sq,sb)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.;vv[3200:]*=2.;ss[3200:]*=4.;bb[3200:]*=4.
    b=bundle(oo,hh,ll,cc,rr,e,qq,vv,bb,ss,sm)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("KC_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.+1e-10):
        raise ValueError("KC_GROSS")
    mutation=v.copy();mutation[WARMUP]*=100.
    delayed=bundle(o,h,l,c,r,e,q,mutation,sb,sq,sm)
    if not np.array_equal(a[0][WARMUP],delayed[0][WARMUP]):
        raise ValueError("KC_OI_PUBLICATION_LAG")
    bad=v.copy();bad[700,2]=np.nan
    gap=bundle(o,h,l,c,r,e,q,bad,sb,sq,sm)
    if gap[3][WARMUP] or not np.allclose(gap[0][WARMUP],gap[0][WARMUP,0]):
        raise ValueError("KC_OI_QUARANTINE")
    if not np.any(~a[3][epochs]):
        raise ValueError("KC_SPOT_MASK_TEST")
    return True

if __name__=="__main__":
    assert static_check()
    print("KC_CROSS_VENUE_OI_LAG_AND_SPOT_MASK_PASS")
