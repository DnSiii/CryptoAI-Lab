#!/usr/bin/env python3
"""V98 future DISTINCT architectures only: causal expected net-log-growth allocator.
Not an NQ/NP/NO rescue; never use realized future PnL or exact-tick claims.
"""
import itertools,math
import numpy as np
LOOKBACK=336
FUNDING_OBSERVATIONS=21
HALF_LIFE=84.
HORIZON_HOURS=168
ACTIVATIONS=(0.,.5,1.)
CAP=.84
def forecast(returns,funding):
    r=np.asarray(returns,dtype=float)
    f=np.asarray(funding,dtype=float)
    if r.shape!=(LOOKBACK,4) or f.shape!=(FUNDING_OBSERVATIONS,4):
        raise ValueError('V98_GROWTH_FORECAST_HISTORY_SHAPE')
    if not np.isfinite(r).all() or not np.isfinite(f).all():
        raise ValueError('V98_GROWTH_FORECAST_NONFINITE')
    age=np.arange(LOOKBACK-1,-1,-1,dtype=float)
    weights=np.exp2(-age/HALF_LIFE);weights/=weights.sum()
    mu=weights@r
    residual=r-mu
    empirical=(residual*weights[:,None]).T@residual
    cov=.5*empirical+.5*np.diag(np.diag(empirical))
    cov=(cov+cov.T)*.5
    rate=f.mean(axis=0)/8.
    return mu,cov,rate

def allocate(core,sleeves,current_net,returns,funding,
             fee=.0004,slippage=.0002,cap=CAP):
    core=np.asarray(core,dtype=float)
    sleeves=np.asarray(sleeves,dtype=float)
    old=np.asarray(current_net,dtype=float)
    if core.shape!=(4,) or sleeves.shape!=(3,4) or old.shape!=(4,):
        raise ValueError('V98_GROWTH_ALLOCATOR_SHAPE')
    if not all(np.isfinite(x).all() for x in (core,sleeves,old)):
        raise ValueError('V98_GROWTH_ALLOCATOR_NONFINITE')
    if not np.isfinite([fee,slippage,cap]).all() or min(fee,slippage)<0 or not 0<cap<1:
        raise ValueError('V98_GROWTH_ALLOCATOR_INVALID')
    if np.abs(core).sum()>cap+1e-10:
        raise ValueError('V98_GROWTH_ALLOCATOR_CORE_LEVERAGE')
    mu,cov,rate=forecast(returns,funding)
    candidates=[]
    for factors in itertools.product(ACTIVATIONS,repeat=3):
        opt=sleeves*np.asarray(factors)[:,None]
        optional_gross=float(np.abs(opt).sum())
        if optional_gross>cap+1e-10:continue
        room=cap-optional_gross
        core_gross=float(np.abs(core).sum())
        core_scale=min(1.,room/core_gross) if core_gross>0 else 1.
        actual_core=core*core_scale
        net=actual_core+opt.sum(axis=0)
        virtual=float(np.abs(actual_core).sum()+np.abs(opt).sum())
        if virtual>cap+1e-9:raise ValueError('V98_GROWTH_ALLOCATOR_VIRTUAL_GROSS')
        if float(np.abs(net).sum())>virtual+1e-9:
            raise ValueError('V98_GROWTH_ALLOCATOR_HIDDEN_LEVERAGE')
        turn=float(np.abs(net-old).sum())
        directional=float(np.dot(net,mu))
        funding_hourly=float(np.dot(net,rate))
        variance=float(net@cov@net)
        if variance < -1e-12:raise ValueError('V98_GROWTH_ALLOCATOR_BAD_COVARIANCE')
        utility=HORIZON_HOURS*(directional-funding_hourly-.5*max(variance,0.))-turn*(fee+slippage)
        candidates.append((utility,turn,virtual,tuple(factors),actual_core,opt,net))
    if not candidates:raise ValueError('V98_GROWTH_ALLOCATOR_NO_FEASIBLE_CANDIDATE')
    # Deterministic fixed 27-action choice; exact ties prefer less turnover,
    # less virtual gross and then the smallest activation tuple (core/cash).
    best=sorted(candidates,key=lambda z:(-z[0],z[1],z[2],z[3]))[0]
    baseline=next(z for z in candidates if z[3]==(0.,0.,0.))
    return {'core_weights':best[4],'optional_weights':best[5],
        'net_weights':best[6],'factors':best[3],
        'expected_net_log_utility':float(best[0]),
        'core_only_expected_net_log_utility':float(baseline[0]),
        'expected_marginal_log_utility':float(best[0]-baseline[0]),
        'expected_net_turnover_fraction':float(best[1]),
        'virtual_gross':float(best[2]),
        'net_gross':float(np.abs(best[6]).sum()),
        'cost_rate':float(fee+slippage),'eligible_actions':len(candidates),
        'forecast_lookback_hours':LOOKBACK,
        'funding_observations':FUNDING_OBSERVATIONS,
        'uses_realized_future_pnl':False,'training_or_holdout_read':False,
        'not_a_validated_engine':True}

def synthetic_tests():
    zeros=np.zeros((LOOKBACK,4))
    funding=np.zeros((FUNDING_OBSERVATIONS,4))
    core=np.array([.3,0.,0.,0.])
    sleeves=np.array([[0.,.2,0.,0.],[0.,0.,.12,-.12],[.08,0.,0.,0.]])
    a=allocate(core,sleeves,core,zeros,funding)
    assert a['factors']==(0.,0.,0.) and a['expected_marginal_log_utility']==0.
    growth=zeros.copy();growth[:,1]=.001
    b=allocate(core,sleeves,core,growth,funding)
    assert b['factors'][0]==1. and b['expected_marginal_log_utility']>0
    negative_funding=funding.copy();negative_funding[:,1]=.02
    c=allocate(core,sleeves,core,zeros,negative_funding)
    assert c['factors'][0]==0.
    weak=zeros.copy();weak[:,1]=1e-7
    d=allocate(core,sleeves,core,weak,funding,fee=.01,slippage=.01)
    assert d['factors'][0]==0.
    # Funding on a short is credited only when signed net inventory is short.
    short=np.zeros((3,4));short[0,1]=-.2
    e=allocate(core,short,core,zeros,negative_funding)
    assert e['factors'][0]==1.
    # Same-asset offset cannot create hidden leverage or double-charge turnover.
    hedge=np.zeros((3,4));hedge[0,0]=-.1
    h=allocate(core,hedge,core,zeros,funding)
    assert h['net_gross']<=h['virtual_gross']+1e-10
    rng=np.random.default_rng(98030)
    for _ in range(300):
        r=rng.normal(0,.002,(LOOKBACK,4))
        f=rng.normal(0,.0002,(FUNDING_OBSERVATIONS,4))
        co=rng.uniform(0,.16,4)
        sl=rng.uniform(-.08,.08,(3,4))
        old=rng.uniform(-.2,.2,4)
        out=allocate(co,sl,old,r,f)
        assert out['virtual_gross']<=CAP+1e-9
        assert out['net_gross']<=out['virtual_gross']+1e-9
        assert out['expected_marginal_log_utility']>=-1e-12
        assert out['eligible_actions']>=1 and not out['uses_realized_future_pnl']
        assert np.isfinite(out['expected_net_log_utility'])
    for bad in (float('nan'),float('inf'),-1.):
        try:allocate(core,sleeves,core,zeros,funding,fee=bad)
        except ValueError:pass
        else:raise AssertionError('V98_GROWTH_ALLOCATOR_BAD_FEE_UNDETECTED')
    return True
if __name__=='__main__':
    assert synthetic_tests()
    print('V98_FUTURE_NET_LOG_GROWTH_CAPITAL_COMPETITION_300_SYNTHETIC_PASS_NOT_PNL')
