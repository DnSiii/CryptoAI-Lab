#!/usr/bin/env python3
"""V98 Independent pre-trade cash/funding-aware atomic planner.
For NEW preregistered candidates only. Does not alter frozen MA/LZ decisions.
Signals and position targets must be computed at completed t, filled at t+1.
"""
import numpy as np

def plan_atomic(current_qty, target_weights, open_prices, equity, fee, slippage,
                funding_rate=None, funding_lower=None, funding_upper=None,
                funding_event=None, gross_cap=.93):
    q=np.asarray(current_qty,dtype=float)
    w=np.asarray(target_weights,dtype=float)
    px=np.asarray(open_prices,dtype=float)
    if q.shape!=(4,4) or w.shape!=(4,4) or px.shape!=(4,):
        raise ValueError('V98_ATOMIC_SHAPE')
    if not all(np.isfinite(z).all() for z in (q,w,px)) or not np.isfinite([equity,fee,slippage,gross_cap]).all():
        raise ValueError('V98_ATOMIC_NONFINITE')
    if np.any(px<=0) or equity<=0 or fee<0 or slippage<0 or not 0<gross_cap<1:
        raise ValueError('V98_ATOMIC_INVALID_INPUT')
    pre_gross=float(np.sum(np.abs(q)*px))
    if pre_gross>equity*(1+1e-10):
        raise ValueError('V98_PREEXISTING_GROSS_ABOVE_NAV')
    if any(z is not None for z in (funding_rate,funding_lower,funding_upper,funding_event)):
        if any(z is None for z in (funding_rate,funding_lower,funding_upper,funding_event)):
            raise ValueError('V98_ATOMIC_INCOMPLETE_FUNDING')
        rate,low,high,event=[np.asarray(z) for z in (funding_rate,funding_lower,funding_upper,funding_event)]
        if any(z.shape!=(4,) for z in (rate,low,high,event)) or not all(np.isfinite(z).all() for z in (rate,low,high)):
            raise ValueError('V98_ATOMIC_FUNDING_SHAPE')
        if np.any(low<=0) or np.any(low>high):
            raise ValueError('V98_ATOMIC_FUNDING_BOUNDS')
        event=event.astype(bool)
    else:
        rate=low=high=event=None
    desired=w*equity/px
    def assess(scale):
        target=desired*scale
        turnover=float(np.sum(np.abs(target-q)*px))
        cost=turnover*(fee+slippage)
        cash=0.
        if event is not None:
            obligation=np.sum(target,axis=0)*rate*event
            cash=-float(np.dot(obligation,np.where(obligation>=0,high,low)))
        # A positive projected funding receipt cannot be used to justify more gross.
        reserved_equity=equity-cost+min(0.,cash)
        gross=float(np.sum(np.abs(target)*px))
        feasible=reserved_equity>0 and gross<=gross_cap*reserved_equity+1e-8
        return feasible,target,turnover,cost,cash,gross,reserved_equity
    if not assess(0.)[0]:
        raise ValueError('V98_ATOMIC_CANNOT_CLOSE_WITHOUT_INSOLVENCY')
    if assess(1.)[0]:
        scale=1.
    else:
        left,right=0.,1.
        for _ in range(72):
            mid=(left+right)/2.
            if assess(mid)[0]:left=mid
            else:right=mid
        scale=left
    feasible,target,turnover,cost,cash,gross,reserved=assess(scale)
    if not feasible:raise ValueError('V98_ATOMIC_SCALE_FAILURE')
    # Deterministic close/reduce-first execution schedule. Opposite signs must
    # close the old side before opening the new side; no buy-first gross spikes.
    close=np.zeros_like(q)
    opened=np.zeros_like(q)
    for k in range(4):
        for j in range(4):
            old=float(q[k,j]);new=float(target[k,j])
            if old*new<=0:
                close[k,j]=-old
                opened[k,j]=new
            elif abs(new)<=abs(old):
                close[k,j]=new-old
            else:
                opened[k,j]=new-old
    after_close=q+close
    after_open=after_close+opened
    if not np.allclose(after_open,target,atol=1e-10,rtol=0):
        raise ValueError('V98_ATOMIC_ORDER_MISMATCH')
    reduction_turnover=float(np.sum(np.abs(close)*px))
    opening_turnover=float(np.sum(np.abs(opened)*px))
    if abs(reduction_turnover+opening_turnover-turnover)>1e-7:
        raise ValueError('V98_ATOMIC_TURNOVER_MISMATCH')
    eq_after_close=equity-reduction_turnover*(fee+slippage)
    eq_after_open=eq_after_close-opening_turnover*(fee+slippage)
    eq_after_funding=eq_after_open+cash
    close_gross=float(np.sum(np.abs(after_close)*px))
    if close_gross>pre_gross+1e-8 or eq_after_close<=0 or eq_after_funding<=0:
        raise ValueError('V98_ATOMIC_CLOSE_OR_SOLVENCY_FAILURE')
    # Track actual gross/equity after close, after open and after funding.
    ratios=(pre_gross/equity,close_gross/eq_after_close,
            gross/eq_after_open,gross/eq_after_funding)
    if max(ratios)>1+1e-9 or gross>gross_cap*eq_after_funding+1e-7:
        raise ValueError('V98_ATOMIC_HIDDEN_LEVERAGE_OR_FINAL_GROSS')
    return {'quantity':target,'equity_after':eq_after_funding,'funding_cash':cash,
            'fees':turnover*fee,'slippage_cash':turnover*slippage,'turnover':turnover,
            'scale':scale,'pretrade_gross_fraction':ratios[0],
            'max_intermediate_gross_fraction':max(ratios),
            'final_gross_fraction':ratios[-1],
            'close_first':True,'post_funding_reserved':event is not None}

def synthetic_tests():
    px=np.full(4,100.)
    zero=np.zeros((4,4))
    w=zero.copy();w[0,0]=.93
    a=plan_atomic(zero,w,px,10000.,.01,.01)
    assert 0<a['scale']<1 and a['final_gross_fraction']<=.93+1e-9
    old=zero.copy();old[0,0]=.9*10000/100
    reverse=zero.copy();reverse[0,0]=-.9
    b=plan_atomic(old,reverse,px,10000.,.001,.001)
    assert b['close_first'] and b['max_intermediate_gross_fraction']<=1
    c=plan_atomic(zero,w,px,10000.,.0004,.0002,
                  funding_rate=np.full(4,.01),funding_lower=np.full(4,99.),
                  funding_upper=np.full(4,101.),funding_event=np.ones(4,bool))
    assert c['funding_cash']<0 and c['final_gross_fraction']<=.93+1e-9
    d=plan_atomic(old,zero,px,10000.,.001,.001)
    assert np.all(d['quantity']==0) and d['final_gross_fraction']==0
    try:plan_atomic(old*1.2,w,px,10000.,.001,.001)
    except ValueError as e:assert 'PREEXISTING' in str(e)
    else:raise AssertionError('V98_LEVERAGE_TEST_FAILED')
    return True
if __name__=='__main__':
    assert synthetic_tests()
    print('V98_ATOMIC_PREFILL_CASH_FUNDING_GROSS_TESTS_PASS')
