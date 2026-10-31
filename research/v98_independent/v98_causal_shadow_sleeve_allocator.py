#!/usr/bin/env python3
"""V98 future-only causal module-specific shadow-return growth allocator; NOT a validated engine."""
import itertools, math
import numpy as np
HISTORY_INTERVALS=4
INTERVAL_HOURS=336
FUNDING_OBSERVATIONS=21
FUNDING_EVENTS_PER_HORIZON=42
ACTIVATIONS=(0.,.5,1.)
CAP=.84
WEIGHTS=np.array([.1,.2,.3,.4])
def shadow_history(raw,o,c,t,first_decision=744):
    """Four COMPLETED non-overlapping price-only shadow intervals; each signal from its start close."""
    raw=np.asarray(raw,dtype=float);o=np.asarray(o,dtype=float);c=np.asarray(c,dtype=float)
    if raw.ndim!=3 or raw.shape[1:]!=(4,4) or o.shape!=(len(raw),4) or c.shape!=o.shape:
        raise ValueError("V98_SHADOW_HISTORY_SHAPE")
    if not np.isfinite(raw).all() or not np.isfinite(o).all() or not np.isfinite(c).all():
        raise ValueError("V98_SHADOW_HISTORY_NONFINITE")
    if np.any(o<=0) or np.any(c<=0):
        raise ValueError("V98_SHADOW_HISTORY_NONPOSITIVE_PRICE")
    if t<first_decision or t>=len(raw) or (t-first_decision)%INTERVAL_HOURS:
        raise ValueError("V98_SHADOW_HISTORY_DECISION_TIME")
    if t-first_decision<HISTORY_INTERVALS*INTERVAL_HOURS:
        return np.zeros((4,4)),False
    history=np.zeros((4,4))
    for k in range(HISTORY_INTERVALS):
        start=t-(HISTORY_INTERVALS-k)*INTERVAL_HOURS
        end=start+INTERVAL_HOURS
        if start<first_decision or end>t:
            raise ValueError("V98_SHADOW_HISTORY_FUTURE_INTERVAL")
        target=raw[start]
        for module in range(4):
            gross=float(np.abs(target[module]).sum())
            if gross>CAP+1e-10:
                raise ValueError("V98_SHADOW_HISTORY_GROSS")
            if gross==0:continue
            price_change=c[end]/o[start+1]-1.
            gross_return=float(np.dot(target[module],price_change))
            if gross_return<=-1 or not math.isfinite(gross_return):
                raise ValueError("V98_SHADOW_HISTORY_INSOLVENT")
            history[module,k]=math.log1p(gross_return)/gross
    return history,True
def allocate(core,sleeves,current_net,shadow,funding,ready=True,
             fee=.0004,slippage=.0002,cap=CAP):
    core=np.asarray(core,dtype=float);sleeves=np.asarray(sleeves,dtype=float)
    old=np.asarray(current_net,dtype=float);sh=np.asarray(shadow,dtype=float)
    f=np.asarray(funding,dtype=float)
    if core.shape!=(4,) or sleeves.shape!=(3,4) or old.shape!=(4,) or sh.shape!=(4,4) or f.shape!=(21,4):
        raise ValueError("V98_SHADOW_ALLOCATOR_SHAPE")
    if not all(np.isfinite(x).all() for x in (core,sleeves,old,sh,f)):
        raise ValueError("V98_SHADOW_ALLOCATOR_NONFINITE")
    if not isinstance(ready,(bool,np.bool_)):
        raise ValueError("V98_SHADOW_ALLOCATOR_READY_FLAG")
    if not np.isfinite([fee,slippage,cap]).all() or min(fee,slippage)<0 or not 0<cap<1:
        raise ValueError("V98_SHADOW_ALLOCATOR_INVALID_COST_OR_CAP")
    if np.abs(core).sum()>cap+1e-10:
        raise ValueError("V98_SHADOW_ALLOCATOR_CORE_GROSS")
    if np.any(np.abs(sleeves).sum(axis=1)>cap+1e-10):
        raise ValueError("V98_SHADOW_ALLOCATOR_SLEEVE_GROSS")
    mu=np.clip(sh@WEIGHTS,-.50,.50)
    residual=sh-mu[:,None]
    empirical=(residual*WEIGHTS[None,:])@residual.T
    cov=.5*empirical+.5*np.diag(np.diag(empirical))
    cov=(cov+cov.T)*.5
    native_mean_rate=f.mean(axis=0)
    intents=np.concatenate((core[None,:],sleeves),axis=0)
    gross=np.abs(intents).sum(axis=1)
    candidates=[]
    for factors in itertools.product(ACTIVATIONS,repeat=4):
        if not ready and any(factors[1:]):continue
        fac=np.asarray(factors,dtype=float)
        virt=float(np.dot(gross,fac))
        if virt>cap+1e-10:continue
        weights=intents*fac[:,None]
        net=weights.sum(axis=0)
        net_gross=float(np.abs(net).sum())
        if net_gross>virt+1e-10:raise ValueError("V98_SHADOW_ALLOCATOR_HIDDEN_LEVERAGE")
        turn=float(np.abs(net-old).sum())
        predicted_gross=gross*fac
        expected_price=float(np.dot(predicted_gross,mu))
        variance=float(predicted_gross@cov@predicted_gross)
        if variance < -1e-12:raise ValueError("V98_SHADOW_ALLOCATOR_COVARIANCE")
        carry=float(FUNDING_EVENTS_PER_HORIZON*np.dot(net,native_mean_rate))
        utility=expected_price-.5*max(0.,variance)-turn*(fee+slippage)-carry
        candidates.append((utility,turn,virt,tuple(factors),weights,net,expected_price,variance,carry))
    if not candidates:raise ValueError("V98_SHADOW_ALLOCATOR_NO_ACTION")
    best=min(candidates,key=lambda x:(-x[0],x[1],x[2],x[3]))
    baseline=max((x for x in candidates if x[3][1:]==(0.,0.,0.)),key=lambda x:(x[0],-x[1],-x[2],tuple(-v for v in x[3])))
    return {"core_weights":best[4][0],"optional_weights":best[4][1:],
            "net_weights":best[5],"factors":best[3],
            "expected_net_log_utility":float(best[0]),
            "core_or_cash_expected_net_log_utility":float(baseline[0]),
            "expected_marginal_log_utility":float(best[0]-baseline[0]),
            "expected_price_log_growth":float(best[6]),
            "expected_shadow_variance":float(best[7]),
            "expected_funding_cost":float(best[8]),
            "expected_net_turnover_fraction":float(best[1]),
            "virtual_gross":float(best[2]),"net_gross":float(np.abs(best[5]).sum()),
            "eligible_actions":len(candidates),"shadow_history_complete":bool(ready),
            "uses_realized_future_pnl":False,"training_or_holdout_read":False,
            "not_a_validated_engine":True}
def synthetic_tests():
    funding=np.zeros((21,4))
    core=np.array([.3,0.,0.,0.])
    sleeves=np.zeros((3,4));sleeves[1,1]=.2;sleeves[1,2]=-.2
    sh=np.zeros((4,4));sh[0]=.01;sh[2]=.08
    a=allocate(core,sleeves,np.zeros(4),sh,funding)
    assert a["factors"][2]==1. and a["expected_marginal_log_utility"]>0
    bad=sh.copy();bad[2]=-.08
    b=allocate(core,sleeves,np.zeros(4),bad,funding)
    assert b["factors"][2]==0.
    c=allocate(core,sleeves,np.zeros(4),sh,funding,ready=False)
    assert c["factors"][1:]==(0.,0.,0.)
    negative=np.full((4,4),-.2)
    d=allocate(core,sleeves,np.zeros(4),negative,funding)
    assert d["factors"]==(0.,0.,0.,0.)
    long=np.zeros((3,4));long[0,1]=.2
    positive=np.zeros((4,4));positive[1]=.01
    e=allocate(core,long,np.zeros(4),positive,funding)
    f=funding.copy();f[:,1]=.03
    g=allocate(core,long,np.zeros(4),positive,f)
    assert e["factors"][1]==1. and g["factors"][1]==0.
    n=2500
    raw=np.zeros((n,4,4));o=np.full((n,4),100.);close=o.copy()
    for k in range(744,n,336):raw[k,0,0]=.3
    close[2088,0]=110.
    hist,ready=shadow_history(raw,o,close,2088)
    assert ready and hist.shape==(4,4)
    changed=close.copy();changed[2089:]*=1.8
    future,ready2=shadow_history(raw,o,changed,2088)
    assert ready2 and np.array_equal(hist,future)
    early,ready3=shadow_history(raw,o,close,744)
    assert not ready3 and np.count_nonzero(early)==0
    rng=np.random.default_rng(98031)
    for _ in range(500):
        co=rng.uniform(-.15,.15,4)
        sl=rng.uniform(-.07,.07,(3,4))
        old=rng.uniform(-.2,.2,4)
        sh=rng.normal(0,.1,(4,4))
        fr=rng.normal(0,.0002,(21,4))
        out=allocate(co,sl,old,sh,fr)
        assert out["virtual_gross"]<=CAP+1e-9
        assert out["net_gross"]<=out["virtual_gross"]+1e-9
        assert out["expected_marginal_log_utility"]>=-1e-10
        assert out["eligible_actions"]>=1 and not out["uses_realized_future_pnl"]
        assert np.isfinite(out["expected_net_log_utility"])
    for v in (float("nan"),float("inf"),-1.):
        try:allocate(core,sleeves,np.zeros(4),sh,funding,fee=v)
        except ValueError:pass
        else:raise AssertionError("V98_SHADOW_INVALID_COST_ACCEPTED")
    return True
if __name__=="__main__":
    assert synthetic_tests()
    print("V98_CAUSAL_SHADOW_SLEEVE_ALLOCATOR_500_ADVERSARIAL_PASS_NOT_PNL")
