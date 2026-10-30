#!/usr/bin/env python3
"""V98 future DISTINCT candidates only: causal mixed-sleeve open projection.
Never rerun or rescue frozen ND with this code. No future funding/mark/PnL.
"""
import numpy as np

def project(q,source_w,updated,px,equity,funding_event=False,cap=.84,event_cap=.82):
    q=np.asarray(q,dtype=float)
    source_w=np.asarray(source_w,dtype=float)
    updated=np.asarray(updated,dtype=bool)
    px=np.asarray(px,dtype=float)
    if q.shape!=(4,4) or source_w.shape!=(4,4) or updated.shape!=(4,) or px.shape!=(4,):
        raise ValueError('V98_PROJECT_SHAPE')
    if not all(np.isfinite(x).all() for x in (q,source_w,px)) or not np.isfinite([equity,cap,event_cap]).all():
        raise ValueError('V98_PROJECT_NONFINITE')
    if equity<=0 or np.any(px<=0) or not 0<event_cap<cap<1:
        raise ValueError('V98_PROJECT_INVALID')
    if np.abs(source_w).sum()>cap+1e-10:
        raise ValueError('V98_PROJECT_SOURCE_HIDDEN_LEVERAGE')
    pre_virtual=float(np.sum(np.abs(q)*px))
    pre_net=float(np.sum(np.abs(q.sum(axis=0))*px))
    if max(pre_virtual,pre_net)>equity*(1+1e-9):
        raise ValueError('V98_PROJECT_PREEXISTING_LEVERAGE')
    raw=q*px/equity
    raw[updated]=source_w[updated]
    raw_gross=float(np.abs(raw).sum())
    active_cap=(event_cap if pre_virtual>cap*equity or
                (bool(funding_event) and pre_virtual>event_cap*equity) else cap)
    result=raw.copy()
    core_gross=float(np.abs(result[0]).sum())
    if core_gross>active_cap:
        result[0]*=active_cap/core_gross
    room=max(0.,active_cap-float(np.abs(result[0]).sum()))
    optional=float(np.abs(result[1:]).sum())
    if optional>room and optional>0:
        result[1:]*=room/optional
    if np.abs(result).sum()>active_cap+1e-10:
        raise ValueError('V98_PROJECT_GROSS')
    if np.any((raw!=0)&(np.sign(result)!=np.sign(raw))):
        raise ValueError('V98_PROJECT_SIGN_CHANGED')
    return {'weights':result,'raw_virtual_gross':raw_gross,
            'projected_virtual_gross':float(np.abs(result).sum()),
            'pre_virtual_gross':pre_virtual,'pre_net_gross':pre_net,
            'effective_cap':active_cap,
            'core_scaled':bool(core_gross>active_cap),
            'optional_scaled':bool(optional>room),
            'uses_future_funding_or_pnl':False}

def synthetic_tests():
    from v98_oneway_net_atomic_planner import plan_virtual
    px=np.array([100.,200.,30.,50.])
    q=np.zeros((4,4))
    q[0,0]=35.;q[1,1]=8.;q[2,2]=-15.
    source=np.zeros((4,4))
    source[0,0]=.44;source[0,1]=.18;source[1,3]=.14;source[2,0]=-.08
    a=project(q,source,np.array([True,False,True,False]),px,10000.,False)
    assert np.abs(a['weights']).sum()<=.84+1e-10
    assert a['raw_virtual_gross']>.84
    b=project(q,source,np.array([True,False,True,False]),px,10000.,True)
    assert b['effective_cap']==.84 # existing pretrade gross is below .82
    result=plan_virtual(q,a['weights'],px,10000.,.0004,.0002)
    assert result['post_virtual_gross']<=.84*10000.+1e-6
    q2=q.copy();q2[1,1]=16.
    e=project(q2,source,np.array([True,False,True,False]),px,10000.,True)
    assert e['effective_cap']==.82
    assert np.abs(e['weights']).sum()<=.82+1e-10
    rng=np.random.default_rng(98003)
    for _ in range(400):
        equity=10000.
        prices=rng.uniform(20,200,4)
        q0=rng.uniform(-1,1,(4,4))
        q0*=equity*.78/max(float(np.sum(np.abs(q0)*prices)),1e-12)
        w=rng.uniform(-.15,.15,(4,4))
        w*=.84/max(float(np.abs(w).sum()),1e-12)
        update=rng.integers(0,2,4).astype(bool)
        out=project(q0,w,update,prices,equity,bool(rng.integers(0,2)))
        assert out['projected_virtual_gross']<=out['effective_cap']+1e-10
        assert np.isfinite(out['weights']).all()
        assert not out['uses_future_funding_or_pnl']
        # independent gross, source/hold reconciliation, sign invariance
        raw=np.where(update[:,None],w,q0*prices/equity)
        assert out['raw_virtual_gross']>=out['projected_virtual_gross']-1e-9
        assert np.all((out['weights']*raw)>=-1e-12)
        assert abs(float(np.abs(out['weights']).sum())-out['projected_virtual_gross'])<1e-10
    for bad in (np.nan,np.inf,0.,-1.):
        try:project(q,source,np.ones(4,bool),px,bad)
        except ValueError:pass
        else:raise AssertionError('V98_PROJECT_INVALID_EQUITY_UNDETECTED')
    return True
if __name__=='__main__':
    assert synthetic_tests()
    print('V98_FUTURE_ONLY_PRETRADE_PROJECTION_400_RANDOMIZED_SYNTHETIC_PASS_NOT_PNL')
