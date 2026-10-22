import numpy as np
import pytest
from phase935_hourly_drawdown_integrity import drawdown,compare_hourly_daily

def test_intraday_trough_not_hidden_by_daily_recovery():
    h=np.full(48,100.,dtype=float);h[12]=20.;h[24:]=110.
    r=compare_hourly_daily(h,100.,np.arange(48)%24)
    assert r['hourly_close_max_drawdown']==pytest.approx(-.8)
    assert r['daily_close_max_drawdown']==0.
    assert r['additional_hourly_drawdown']==pytest.approx(.8)

def test_scale_invariance_and_monotonicity():
    h=np.linspace(100,200,48)
    a=compare_hourly_daily(h,100.,np.arange(48)%24)
    b=compare_hourly_daily(h*17,1700.,np.arange(48)%24)
    assert a==b and a['hourly_close_max_drawdown']==0.

def test_randomized_hourly_always_no_less_severe():
    rng=np.random.default_rng(935)
    for _ in range(1000):
        h=100*np.exp(np.cumsum(rng.normal(0,.03,24*4)))
        r=compare_hourly_daily(h,100.,np.arange(len(h))%24)
        assert r['hourly_close_max_drawdown']<=r['daily_close_max_drawdown']+1e-12

def test_incomplete_calendar_and_missing_nav_fail_closed():
    with pytest.raises(ValueError):compare_hourly_daily(np.ones(47),1,np.arange(47)%24)
    with pytest.raises(ValueError):compare_hourly_daily(np.ones(48),1,np.ones(48,dtype=int))
    with pytest.raises(ValueError):drawdown([1,float('nan')],1)
