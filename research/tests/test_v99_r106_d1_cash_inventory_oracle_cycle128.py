"""C128 adversarial, synthetic-only account transition replay."""
import copy
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from research.tools.v99_r106_d1_cash_inventory_oracle_cycle128 import reconcile_cash_inventory

T = datetime(2022, 5, 1, tzinfo=timezone.utc)
START = datetime(2021, 12, 9, tzinfo=timezone.utc)
END = datetime(2023, 10, 1, tzinfo=timezone.utc)


def snap(cash, btc_spot='0', btc_perp='0'):
    return {'cash_quote': str(cash), 'spot_base': {'BTC': str(btc_spot), 'ETH': '0'},
            'perp_base': {'BTC': str(btc_perp), 'ETH': '0'}}


def case(scenario='severe_model_only', spot_currency='BASE'):
    rate = Decimal('.0007' if scenario == 'severe_model_only' else '.0014')
    schedule = {'BTC': [{'start': START, 'end': END, 'spot_taker': '.001',
                         'perp_taker': '.0005', 'spot_fee_currency': spot_currency,
                         'account_tier': 'SYNTHETIC_NOT_AUTHENTICATED'}],
                'ETH': [{'start': START, 'end': END, 'spot_taker': '.001',
                         'perp_taker': '.0005', 'spot_fee_currency': spot_currency,
                         'account_tier': 'SYNTHETIC_NOT_AUTHENTICATED'}]}
    stress = 100 * rate
    base_fee = Decimal('.001') if spot_currency == 'BASE' else Decimal('0')
    quote_fee = Decimal('.1') if spot_currency == 'QUOTE' else Decimal('0')
    after_spot_cash = Decimal('1000') - Decimal('100') - stress - quote_fee
    after_spot_units = Decimal('1') - base_fee
    spot = {'trade_id': 's1', 'time': T, 'asset': 'BTC', 'leg': 'spot',
            'side': 'buy', 'base_quantity': '1', 'execution_price_quote_per_base': '100',
            'quote_notional': '100', 'native_fee_quote': '.100',
            'stress_fee_quote': str(stress), 'booked_total_fee_quote': str(Decimal('.1')+stress),
            'before': snap('1000'), 'after': snap(after_spot_cash, after_spot_units)}
    if spot_currency == 'BASE':
        spot.update({'base_fee_units': '.001', 'inventory_base_fee_debit_units': '.001'})
    perp_cash = after_spot_cash - Decimal('.05') - stress
    perp = {'trade_id': 'p1', 'time': T, 'asset': 'BTC', 'leg': 'perp',
            'side': 'sell', 'base_quantity': '1', 'execution_price_quote_per_base': '100',
            'quote_notional': '100', 'native_fee_quote': '.050',
            'stress_fee_quote': str(stress), 'booked_total_fee_quote': str(Decimal('.05')+stress),
            'before': copy.deepcopy(spot['after']),
            'after': snap(perp_cash, after_spot_units, '-1')}
    return [spot, perp], schedule


@pytest.mark.parametrize('scenario,expected', [
    ('severe_model_only', '.2900'), ('supersevere_model_only', '.4300')])
def test_replay_two_frozen_costs(scenario, expected):
    fills, schedule = case(scenario)
    x = reconcile_cash_inventory(scenario=scenario, fills=fills, native_fee_schedule=schedule)
    assert Decimal(x['total_economic_fee_quote']) == Decimal(expected)
    assert x['fills_replayed'] == 2
    assert x['exchange_receipts_authenticated'] is False
    assert x['promotion_authorized'] is False


def test_quote_denominated_spot_fee_is_cash_not_base():
    fills, schedule = case(spot_currency='QUOTE')
    x = reconcile_cash_inventory(scenario='severe_model_only', fills=fills, native_fee_schedule=schedule)
    assert Decimal(x['native_base_inventory_fee_quote']) == 0
    assert Decimal(x['native_quote_cash_fee_quote']) == Decimal('.150')


def reject(changer, match):
    fills, schedule = case()
    changer(fills, schedule)
    with pytest.raises(ValueError, match=match):
        reconcile_cash_inventory(scenario='severe_model_only', fills=fills, native_fee_schedule=schedule)


def test_double_charge_base_fee_as_quote_cash():
    reject(lambda f,s: f[0]['after'].update(cash_quote='899.83'), 'DOUBLE_CHARGE_OR_OMISSION')


def test_omit_base_fee_inventory():
    reject(lambda f,s: f[0]['after']['spot_base'].update(BTC='1'), 'SPOT_BASE_INVENTORY_MISMATCH')


def test_missing_perp_fee_cash():
    reject(lambda f,s: f[1]['after'].update(cash_quote='899.86'), 'PERP_FEE_CASH_MISMATCH')


def test_missing_spot_trade_cash():
    reject(lambda f,s: f[0]['after'].update(cash_quote='999.93'), 'DOUBLE_CHARGE_OR_OMISSION')


def test_other_asset_inventory_tamper():
    reject(lambda f,s: f[0]['after']['spot_base'].update(ETH='1'), 'OTHER_ASSET_BALANCE_CHANGED')


def test_cross_fill_state_discontinuity():
    reject(lambda f,s: f[1]['before'].update(cash_quote='900'), 'DISCONTINUOUS_ACCOUNT_JOURNAL')


def test_perp_notional_must_not_debit_cash():
    reject(lambda f,s: f[1]['after'].update(cash_quote='799.81'), 'PERP_FEE_CASH_MISMATCH')


def test_price_quantity_notional_tamper():
    reject(lambda f,s: f[1].update(base_quantity='2'), 'FILL_NOTIONAL_QUANTITY_PRICE_MISMATCH')


def test_duplicate_trade_ids_rejected_by_c127():
    reject(lambda f,s: f[1].update(trade_id='s1'), 'DUPLICATE')


def test_nonchronological_fill():
    reject(lambda f,s: f[1].update(time=datetime(2022,4,30,tzinfo=timezone.utc)), 'NONCHRONOLOGICAL')


def test_sealed_fill():
    reject(lambda f,s: f[0].update(time=END), 'OUTSIDE_TRAIN')


def test_missing_full_state():
    reject(lambda f,s: f[0]['before']['spot_base'].pop('ETH'), 'COMPLETE_SPOT_BALANCE_REQUIRED')


def test_sell_inventory_base_fee():
    fills, schedule = case()
    # Start with 2 BTC, sell 1 BTC and debit 0.001 BTC native fee.
    fills[0]['side'] = 'sell'
    fills[0]['before'] = snap('1000', '2')
    fills[0]['after'] = snap('1099.93', '.999')
    fills[1]['before'] = copy.deepcopy(fills[0]['after'])
    fills[1]['after'] = snap('1099.81', '.999', '-1')
    x = reconcile_cash_inventory(scenario='severe_model_only', fills=fills, native_fee_schedule=schedule)
    assert x['fills_replayed'] == 2


def test_negative_spot_inventory():
    reject(lambda f,s: f[0]['after']['spot_base'].update(BTC='-1'), 'NEGATIVE_CASH_OR_SPOT_BALANCE')
