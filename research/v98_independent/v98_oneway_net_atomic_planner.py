#!/usr/bin/env python3
"""V98 Independent one-way netted virtual-sleeve atomic planner, preregistered.
Infrastructure only. Never applies retrospectively to rejected candidate PnL.
Account one-way position-mode evidence required for exchange-native claim.
"""
import numpy as np

def plan_virtual(q,w,px,equity,fee,slip,funding_event=False,
                 target_virtual_cap=.84,post_cap=.90,fixed_event_loss_fraction=.03):
    q=np.asarray(q,dtype=float);w=np.asarray(w,dtype=float);px=np.asarray(px,dtype=float)
    if q.shape!=(4,4) or w.shape!=(4,4) or px.shape!=(4,):
        raise ValueError('V98_NET_SHAPE')
    if not all(np.isfinite(x).all() for x in (q,w,px)) or not np.isfinite(
            [equity,fee,slip,target_virtual_cap,post_cap,fixed_event_loss_fraction]).all():
        raise ValueError('V98_NET_NONFINITE')
    if np.any(px<=0) or equity<=0 or min(fee,slip,fixed_event_loss_fraction)<0:
        raise ValueError('V98_NET_INVALID_INPUT')
    if not 0<target_virtual_cap<post_cap<1:
        raise ValueError('V98_NET_CAPS')
    if float(np.abs(w).sum())>target_virtual_cap+1e-10:
        raise ValueError('V98_NET_HIDDEN_VIRTUAL_LEVERAGE')
    pre_virtual=float(np.sum(np.abs(q)*px))
    old_net=q.sum(axis=0)
    pre_net=float(np.sum(np.abs(old_net)*px))
    if pre_virtual>equity*(1+1e-9) or pre_net>equity*(1+1e-9):
        raise ValueError('V98_NET_PREEXISTING_LEVERAGE')
    desired=w*equity/px
    def assess(scale):
        target=desired*scale
        new_net=target.sum(axis=0)
        delta=new_net-old_net
        turnover=float(np.sum(np.abs(delta)*px))
        cost=turnover*(fee+slip)
        virt=float(np.sum(np.abs(target)*px))
        net=float(np.sum(np.abs(new_net)*px))
        reserve=(fixed_event_loss_fraction*max(pre_net,net)) if funding_event else 0.
        after=equity-cost-reserve
        ok=bool(after>0 and virt<=post_cap*after+1e-8 and
                net<=post_cap*after+1e-8 and virt<=target_virtual_cap*equity+1e-8)
        return ok,target,new_net,delta,turnover,cost,virt,net,reserve,after
    if not assess(0.)[0]:raise ValueError('V98_NET_CANNOT_CLOSE')
    if assess(1.)[0]:scale=1.
    else:
        low,high=0.,1.
        for _ in range(72):
            mid=(low+high)/2
            if assess(mid)[0]:low=mid
            else:high=mid
        scale=low
    feasible,target,new_net,delta,turn,cost,virt,net,reserve,after=assess(scale)
    if not feasible:raise ValueError('V98_NET_INFEASIBLE_SCALE')
    closing=np.zeros(4);opening=np.zeros(4)
    for j in range(4):
        old=float(old_net[j]);new=float(new_net[j])
        if old*new<=0:
            closing[j]=-old;opening[j]=new
        elif abs(new)<=abs(old):
            closing[j]=new-old
        else:
            opening[j]=new-old
    mid_net=old_net+closing
    if not np.allclose(mid_net+opening,new_net,rtol=0,atol=1e-10):
        raise ValueError('V98_NET_ATOMIC_ORDER')
    close_turn=float(np.sum(np.abs(closing)*px))
    open_turn=float(np.sum(np.abs(opening)*px))
    if abs(close_turn+open_turn-turn)>1e-7:
        raise ValueError('V98_NET_TURNOVER_IDENTITY')
    mid_equity=equity-close_turn*(fee+slip)
    post_equity=mid_equity-open_turn*(fee+slip)
    mid_gross=float(np.sum(np.abs(mid_net)*px))
    if mid_equity<=0 or post_equity<=0 or max(
            pre_net/equity,mid_gross/mid_equity,net/post_equity)>1+1e-9:
        raise ValueError('V98_NET_INTERMEDIATE_LEVERAGE')
    return {'virtual_quantity':target,'net_quantity':new_net,
            'net_delta':delta,'net_close_first':closing,'net_open_second':opening,
            'scale':scale,'turnover':turn,'fees':turn*fee,'slippage':turn*slip,
            'pre_virtual_gross':pre_virtual,'pre_net_gross':pre_net,
            'post_virtual_gross':virt,'post_net_gross':net,
            'reserved_funding_loss':reserve,'equity_after_cost':post_equity,
            'max_intermediate_net_gross_fraction':max(
                pre_net/equity,mid_gross/mid_equity,net/post_equity),
            'one_way_position_mode_required':True,
            'uses_actual_future_funding_to_size':False}

def settle_virtual(plan,funding_cash,order,equity,old_virtual,px,post_cap=.90):
    if order not in ('carried_before_fill','new_after_fill'):
        raise ValueError('V98_NET_FUNDING_ORDER')
    if not np.isfinite(funding_cash) or equity<=0:
        raise ValueError('V98_NET_FUNDING_INVALID')
    if funding_cash < -plan['reserved_funding_loss']-1e-7:
        raise ValueError('V98_NET_FUNDING_RESERVE_EXCEEDED')
    after=plan['equity_after_cost']+funding_cash
    if after<=0 or max(plan['post_virtual_gross'],plan['post_net_gross'])>post_cap*after+1e-7:
        raise ValueError('V98_NET_POST_FUNDING_GROSS')
    if order=='carried_before_fill':
        old_net=np.asarray(old_virtual,dtype=float).sum(axis=0)
        pre_net=float(np.sum(np.abs(old_net)*np.asarray(px,dtype=float)))
        if equity+funding_cash<=0 or pre_net>(equity+funding_cash)*(1+1e-9):
            raise ValueError('V98_NET_CARRIED_PRE_FILL_LEVERAGE')
    return float(after)

def synthetic_tests():
    px=np.full(4,100.)
    q=np.zeros((4,4))
    w=q.copy();w[0,0]=.30;w[3,0]=-.30
    a=plan_virtual(q,w,px,10000.,.001,.001)
    assert a['turnover']==0. and a['fees']==0. and a['slippage']==0.
    assert abs(a['post_virtual_gross']-6000.)<1e-8
    assert np.max(np.abs(a['net_quantity']))==0.
    b=plan_virtual(a['virtual_quantity'],w,px,10000.,.001,.001)
    assert b['turnover']==0.
    w2=q.copy();w2[0,0]=.35;w2[3,0]=-.25
    c=plan_virtual(a['virtual_quantity'],w2,px,10000.,.001,.001)
    assert abs(c['turnover']-1000.)<1e-8
    assert abs(c['fees']-1.)<1e-8 and abs(c['slippage']-1.)<1e-8
    assert np.allclose(c['net_close_first']+c['net_open_second'],c['net_delta'])
    wbad=q.copy();wbad[0,0]=.5;wbad[3,0]=-.5
    try:plan_virtual(q,wbad,px,10000.,.001,.001)
    except ValueError as exc:assert 'HIDDEN_VIRTUAL' in str(exc)
    else:raise AssertionError('V98_NET_HIDDEN_LEVERAGE_NOT_BLOCKED')
    wflip=q.copy();wflip[2,0]=-.40
    old=q.copy();old[0,0]=50.
    f=plan_virtual(old,wflip,px,10000.,.001,.001,True)
    assert abs(f['turnover']-9000.)<1e-7
    assert f['net_close_first'][0]==-50. and f['net_open_second'][0]<0
    assert f['reserved_funding_loss']>0 and not f['uses_actual_future_funding_to_size']
    assert settle_virtual(f,-100.,'carried_before_fill',10000.,old,px)>0
    assert settle_virtual(f,-100.,'new_after_fill',10000.,old,px)>0
    try:settle_virtual(f,-1000.,'carried_before_fill',10000.,old,px)
    except ValueError as exc:assert 'RESERVE' in str(exc)
    else:raise AssertionError('V98_NET_RESERVE_NOT_ENFORCED')
    rng=np.random.default_rng(980)
    for _ in range(300):
        v=rng.uniform(-.07,.07,size=(4,4))
        v*=.60/max(float(np.abs(v).sum()),1e-12)
        result=plan_virtual(q,v,px,10000.,.001,.002,bool(rng.integers(0,2)))
        assert result['turnover']>=0 and result['fees']>=0
        assert result['post_virtual_gross']<=.84*10000.+1e-6
        assert np.allclose(result['net_quantity'],result['virtual_quantity'].sum(axis=0))
        assert np.allclose(result['net_delta'],
                           result['net_close_first']+result['net_open_second'])
    return True

if __name__=='__main__':
    assert synthetic_tests()
    print('V98_ONEWAY_NETTED_ATOMIC_300_RANDOMIZED_SYNTHETIC_TESTS_PASS_NOT_PNL')
