#!/usr/bin/env python3
"""V98 Independent causal pre-fill atomic planner for NEW candidates only.

Only known-at-fill equity, open prices, scheduled funding calendar and FIXED
ex-ante worst-loss reserve enter sizing. Actual event rate / mark OHLC never do.
No mutation of frozen historical candidate receipts.
"""
import numpy as np
def plan_causal(q,w,px,equity,fee,slip,funding_event=False,gross_cap=.90,
                fixed_event_loss_fraction=.03):
    q=np.asarray(q,float);w=np.asarray(w,float);px=np.asarray(px,float)
    if q.shape!=(4,4) or w.shape!=(4,4) or px.shape!=(4,):
        raise ValueError('V98_CAUSAL_SHAPE')
    if not all(np.isfinite(x).all() for x in (q,w,px)) or not np.isfinite(
            [equity,fee,slip,gross_cap,fixed_event_loss_fraction]).all():
        raise ValueError('V98_CAUSAL_NONFINITE')
    if np.any(px<=0) or equity<=0 or min(fee,slip,fixed_event_loss_fraction)<0 or not 0<gross_cap<1:
        raise ValueError('V98_CAUSAL_INPUT')
    if np.sum(np.abs(w))>1+1e-10:raise ValueError('V98_CAUSAL_TARGET_LEVERAGE')
    pre=float(np.sum(np.abs(q)*px))
    if pre>equity*(1+1e-10):raise ValueError('V98_CAUSAL_PREEXISTING_LEVERAGE')
    desired=w*equity/px
    def assess(scale):
        target=desired*scale
        turnover=float(np.sum(np.abs(target-q)*px))
        cost=turnover*(fee+slip)
        gross=float(np.sum(np.abs(target)*px))
        reserve=(fixed_event_loss_fraction*max(pre,gross)) if funding_event else 0.
        remain=equity-cost-reserve
        return remain>0 and gross<=gross_cap*remain+1e-9,target,turnover,cost,gross,reserve
    if not assess(0.)[0]:raise ValueError('V98_CAUSAL_CANNOT_CLOSE')
    if assess(1.)[0]:scale=1.
    else:
        lo,hi=0.,1.
        for _ in range(72):
            mid=(lo+hi)/2
            if assess(mid)[0]:lo=mid
            else:hi=mid
        scale=lo
    feasible,target,turnover,cost,gross,reserve=assess(scale)
    if not feasible:raise ValueError('V98_CAUSAL_SCALE')
    close=np.zeros_like(q);opening=np.zeros_like(q)
    for k in range(4):
        for j in range(4):
            old=float(q[k,j]);new=float(target[k,j])
            if old*new<=0:close[k,j]=-old;opening[k,j]=new
            elif abs(new)<=abs(old):close[k,j]=new-old
            else:opening[k,j]=new-old
    mid=q+close
    if not np.allclose(mid+opening,target,rtol=0,atol=1e-10):
        raise ValueError('V98_CAUSAL_ORDER')
    close_turn=float(np.sum(np.abs(close)*px))
    open_turn=float(np.sum(np.abs(opening)*px))
    if abs(close_turn+open_turn-turnover)>1e-7:
        raise ValueError('V98_CAUSAL_TURNOVER')
    after_close=equity-close_turn*(fee+slip)
    after_open=after_close-open_turn*(fee+slip)
    mid_gross=float(np.sum(np.abs(mid)*px))
    if after_open<=reserve or max(pre/equity,mid_gross/after_close,gross/after_open)>1+1e-9:
        raise ValueError('V98_CAUSAL_INTERMEDIATE')
    return {'quantity':target,'scale':scale,'turnover':turnover,'fees':turnover*fee,
            'slippage':turnover*slip,'close_turnover':close_turn,
            'open_turnover':open_turn,'reserved_funding_loss':reserve,
            'pre_gross':pre,'mid_gross':mid_gross,'post_gross':gross,
            'equity_after_cost':after_open,'close_first':True,
            'max_intermediate_gross_fraction':max(pre/equity,mid_gross/after_close,gross/after_open),
            'uses_actual_future_funding_to_size':False}
def settle_checked(planned,actual_funding_cash,order,starting_equity,px,old_qty):
    """Ex-post accounting only; must not feed result back to plan_causal."""
    if order not in ('carried_before_fill','new_after_fill'):
        raise ValueError('V98_CAUSAL_ORDER_INVALID')
    if not np.isfinite(actual_funding_cash):raise ValueError('V98_CAUSAL_FUNDING_NONFINITE')
    reserve=planned['reserved_funding_loss']
    if actual_funding_cash < -reserve-1e-7:
        raise ValueError('V98_CAUSAL_FUNDING_EXCEEDS_PRECOMMITTED_RESERVE')
    gross=planned['post_gross']
    after=planned['equity_after_cost']+actual_funding_cash
    if after<=0 or gross>after*.93+1e-7:
        raise ValueError('V98_CAUSAL_POSTFUNDING_GROSS')
    pre=float(np.sum(np.abs(old_qty)*px))
    if order=='carried_before_fill':
        before_fill=starting_equity+actual_funding_cash
        if before_fill<=0 or pre>before_fill*(1+1e-9):
            raise ValueError('V98_CAUSAL_CARRIED_PRE_FILL_LEVERAGE')
    return after
def synthetic_tests():
    px=np.full(4,100.)
    z=np.zeros((4,4));w=z.copy();w[0,0]=.90
    a=plan_causal(z,w,px,10000.,.001,.001,True)
    assert 0<a['scale']<1 and a['reserved_funding_loss']>0
    assert not a['uses_actual_future_funding_to_size']
    old=z.copy();old[0,0]=90.
    flip=z.copy();flip[0,0]=-.90
    b=plan_causal(old,flip,px,10000.,.001,.001,True)
    assert b['max_intermediate_gross_fraction']<=1
    assert settle_checked(b,-100.,'new_after_fill',10000.,px,old)>0
    assert settle_checked(b,-100.,'carried_before_fill',10000.,px,old)>0
    try:settle_checked(b,-1000.,'new_after_fill',10000.,px,old)
    except ValueError as e:assert 'RESERVE' in str(e)
    else:raise AssertionError('V98_CAUSAL_RESERVE_FAIL')
    try:plan_causal(old*1.2,w,px,10000.,.001,.001)
    except ValueError as e:assert 'PREEXISTING' in str(e)
    else:raise AssertionError('V98_CAUSAL_LEVERAGE_FAIL')
    return True
if __name__=='__main__':
    assert synthetic_tests()
    print('V98_CAUSAL_PREFILL_ATOMIC_FUNDING_RESERVE_TESTS_PASS')
