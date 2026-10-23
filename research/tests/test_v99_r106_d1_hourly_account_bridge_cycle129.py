"""C129 synthetic adversarial checks: combined mark/funding/fill hourly bridge."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest

from research.tools.v99_r106_d1_hourly_account_bridge_cycle129 import reconcile_hourly_account
from research.tests.test_v99_r106_d1_cash_inventory_oracle_cycle128 import case, snap

T = datetime(2022, 5, 1, tzinfo=timezone.utc)

def example(scenario='severe_model_only'):
    fills, tiers = case(scenario)
    fee = Decimal('.0007' if scenario == 'severe_model_only' else '.0014')*100
    initial = snap('1000', '0', '0')
    # At first mark, there are no positions; a paired buy/short opens.
    f1 = {'time':T, 'marks':{'BTC':{'spot':'100','perp':'100'},
                             'ETH':{'spot':'50','perp':'50'}},
          'before':deepcopy(initial), 'after_mark':deepcopy(initial),
          'funding':[], 'after_funding':deepcopy(initial),
          'fills':fills, 'after':deepcopy(fills[-1]['after'])}
    # At the second mark, short perp loses 1 quote; long spot gains 1.
    # A positive .001 settled fix pays the existing -1 BTC short +.101.
    old = deepcopy(f1['after'])
    marked = deepcopy(old)
    marked['cash_quote'] = str(Decimal(old['cash_quote'])-1)
    funded = deepcopy(marked)
    funded['cash_quote'] = str(Decimal(marked['cash_quote'])+Decimal('.101'))
    f2 = {'time':T+timedelta(hours=1),
          'marks':{'BTC':{'spot':'101','perp':'101'},
                   'ETH':{'spot':'50','perp':'50'}},
          'before':old, 'after_mark':marked,
          'funding':[{'asset':'BTC','time':T+timedelta(hours=1),
                      'rate':'.001','source':'OKX','instrument':'BTC-USDT-SWAP'}],
          'after_funding':funded,'fills':[], 'after':deepcopy(funded)}
    return [f1,f2], tiers

def replay(frames,tiers,scenario='severe_model_only'):
    return reconcile_hourly_account(
        scenario=scenario, frames=frames,
        initial_marks={'BTC':{'spot':'100','perp':'100'},
                       'ETH':{'spot':'50','perp':'50'}},
        initial_marks_time=T-timedelta(hours=1),
        native_fee_schedule=tiers)

@pytest.mark.parametrize('scenario,fee', [('severe_model_only','.2900'),
                                         ('supersevere_model_only','.4300')])
def test_full_hourly_bridge(scenario,fee):
    frames,tiers=example(scenario)
    out=replay(frames,tiers,scenario)
    assert out['hours_replayed']==2
    assert out['fills_replayed']==2
    assert out['funding_events_modeled']==1
    assert Decimal(out['perp_variation_margin_quote'])==Decimal('-1')
    assert Decimal(out['modeled_funding_quote'])==Decimal('.101')
    assert Decimal(out['modeled_native_plus_stress_fees_quote'])==Decimal(fee)
    assert Decimal(out['modeled_net_nav_delta_quote'])==Decimal('.100')-Decimal(fee)
    assert out['actual_settled_funding_authenticated'] is False
    assert out['promotion_authorized'] is False

def reject(change,match):
    frames,tiers=example();change(frames)
    with pytest.raises(ValueError,match=match): replay(frames,tiers)

def test_perp_mark_pnl_must_reconcile():
    reject(lambda f:f[1]['after_mark'].update(cash_quote='899.81'), 'VARIATION_MARGIN')

def test_no_lookahead_hour():
    reject(lambda f:f[1].update(time=datetime(2024,1,18,tzinfo=timezone.utc)), 'SEALED')

def test_funding_cannot_be_silent_cash_credit():
    reject(lambda f:f[1]['after_funding'].update(cash_quote='999'), 'FUNDING_CASH')

def test_funding_cannot_use_unrelated_instrument():
    reject(lambda f:f[1]['funding'][0].update(instrument='ETH-USDT-SWAP'), 'UNBOUND_FUNDING')

def test_cross_hour_state_discontinuity():
    reject(lambda f:f[1]['before'].update(cash_quote='1000'), 'DISCONTINUITY')

def test_fill_must_start_after_mark_and_funding():
    reject(lambda f:f[0]['fills'][0]['before'].update(cash_quote='2000'), 'ANCHORED')

def test_no_fill_cannot_change_inventory():
    reject(lambda f:f[1]['after']['spot_base'].update(BTC='2'), 'UNEXPLAINED')

def test_no_fill_cannot_create_cash():
    reject(lambda f:f[1]['after'].update(cash_quote='1000'), 'UNEXPLAINED')

def test_wrong_hour_fill_rejected():
    reject(lambda f:f[0]['fills'][1].update(time=T+timedelta(hours=1)), 'WRONG_HOUR')

def test_spot_mark_is_not_perp_variation_margin():
    reject(lambda f:f[1]['after_mark'].update(cash_quote='899.81'), 'VARIATION_MARGIN')


def test_perp_execution_slippage_not_silently_ignored():
    reject(lambda f:f[0]['fills'][1].update(execution_price_quote_per_base='101'),
           'OFF_MARK_FILL_REQUIRES_SLIPPAGE')

def test_spot_execution_slippage_not_silently_ignored():
    reject(lambda f:f[0]['fills'][0].update(execution_price_quote_per_base='99'),
           'OFF_MARK_FILL_REQUIRES_SLIPPAGE')

def test_funding_cannot_be_charged_twice():
    reject(lambda f:f[1]['funding'].append(deepcopy(f[1]['funding'][0])),
           'DUPLICATE_OR_UNBOUND_FUNDING')

def test_funding_requires_same_timestamp():
    reject(lambda f:f[1]['funding'][0].update(time=T), 'DUPLICATE_OR_UNBOUND_FUNDING')

def test_cannot_relabel_market_without_account_effect():
    reject(lambda f:f[1]['marks']['BTC'].update(perp='102'), 'VARIATION_MARGIN')


def dual(frames_s,frames_x,tiers):
    from research.tools.v99_r106_d1_hourly_account_bridge_cycle129 import reconcile_dual_cost_scenarios
    return reconcile_dual_cost_scenarios(
        frames_by_scenario={'severe_model_only':frames_s,
                            'supersevere_model_only':frames_x},
        initial_marks={'BTC':{'spot':'100','perp':'100'},
                       'ETH':{'spot':'50','perp':'50'}},
        initial_marks_time=T-timedelta(hours=1), native_fee_schedule=tiers)


def test_two_cost_scenarios_share_market_and_funding():
    s,tiers=example();x,_=example('supersevere_model_only')
    out=dual(s,x,tiers)
    assert out['same_exogenous_market_and_funding_path']
    assert out['scenario_ordering_is_not_alpha_proof']
    assert out['promotion_authorized'] is False


def test_scenario_market_path_tampering_rejected():
    s,tiers=example();x,_=example('supersevere_model_only')
    x[1]['marks']['BTC']['spot']='105'
    with pytest.raises(ValueError,match='EXOGENOUS_PATH_MISMATCH'):
        dual(s,x,tiers)


def test_scenario_funding_path_tampering_rejected():
    s,tiers=example();x,_=example('supersevere_model_only')
    x[1]['funding'][0]['rate']='.002'
    with pytest.raises(ValueError,match='EXOGENOUS_PATH_MISMATCH'):
        dual(s,x,tiers)
