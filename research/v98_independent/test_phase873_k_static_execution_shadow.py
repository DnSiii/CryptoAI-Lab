"""V98 Independent Phase873 causal static-capacity shadow tests (no PnL)."""
import numpy as np
import pytest
from phase873_k_static_execution_shadow import simulate_static


def base():
    w = np.zeros((12,4));w[:,0]=.65;w[5:,1]=.4;w[5:,0]=.3
    q = np.full((12,4),1e6)
    return w,q


def test_fills_exact_target_when_capacity_abundant():
    w,q=base()
    r=simulate_static(w,q,1e6,participation=1)
    assert r['terminal_l1_tracking_gap_nav']==pytest.approx(0)
    assert r['max_static_asset_weight']<=.70


def test_low_liquidity_creates_unfilled_queue():
    w,q=base();q[:]=0
    r=simulate_static(w,q,1e6)
    assert r['filled_notional_usd']==0
    assert r['hours_unfilled_any']==11
    assert r['orders_with_zero_prior_closed_hour_liquidity']>0


def test_future_volume_cannot_change_earlier_fills():
    w,q=base()
    a,trace_a=simulate_static(w,q,1e6,return_trace=True)
    q[8:]=1e12
    b,trace_b=simulate_static(w,q,1e6,return_trace=True)
    np.testing.assert_array_equal(trace_a['tracking_l1_nav'][:8],trace_b['tracking_l1_nav'][:8])


def test_future_targets_cannot_change_earlier_fills():
    w,q=base()
    a,trace_a=simulate_static(w,q,1e6,return_trace=True)
    w[8:]=0
    b,trace_b=simulate_static(w,q,1e6,return_trace=True)
    np.testing.assert_array_equal(trace_a['tracking_l1_nav'][:8],trace_b['tracking_l1_nav'][:8])


def test_reversal_supersedes_pending_without_fabricated_fills():
    w,q=base();q[:]=10
    w[3:,0]=0;w[3:,1]=.6
    r=simulate_static(w,q,1e6)
    assert r['filled_notional_usd']<100
    assert r['max_static_asset_weight']<=.7


def test_reject_bad_data_and_caps():
    w,q=base()
    for a,b,c in [(w[:2],q[:2],1e6),(w,q,-1),(w,np.full_like(q,-1),1e6),
                  (w,np.full_like(q,np.nan),1e6)]:
        with pytest.raises(ValueError):simulate_static(a,b,c)
    w[0,0]=.9
    with pytest.raises(ValueError):simulate_static(w,q,1e6)


def test_monotone_fill_under_uniform_volume_increase_for_constant_targets():
    w=np.zeros((12,4));w[:,0]=.7;w[:,1]=.5
    q=np.full((12,4),1000.)
    small=simulate_static(w,q,1e6)
    big=simulate_static(w,q*10,1e6)
    assert big['terminal_l1_tracking_gap_nav'] <= small['terminal_l1_tracking_gap_nav']
    assert big['filled_notional_usd'] >= small['filled_notional_usd']


def test_uses_previous_closed_hour_volume():
    w=np.zeros((5,4));w[:,0]=.7
    q=np.zeros((5,4));q[0,0]=1e7
    report,trace=simulate_static(w,q,1e6,return_trace=True)
    assert trace['tracking_l1_nav'][0]==pytest.approx(.2)
    assert trace['tracking_l1_nav'][1]==pytest.approx(.2)
