"""C139: causal target -> paired spot/perp modeled fills, no orders or ROI.

Pre-economic mechanical execution adapter for distinct preregistered D1.
It does NOT authenticate OKX receipts or enable historical scoring.
The supplied prices are *execution marks* at time t; decisions must have
been finalized with information no later than t-1 hour.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from decimal import Decimal, getcontext, ROUND_DOWN

getcontext().prec = 40
ASSETS = ('BTC', 'ETH')
MAX_GROSS = Decimal('1')
MAX_PAIR = Decimal('0.25')
MODEL_SPOT_QTY_STEP = Decimal('0.000000000001')  # modeled, NOT OKX lot-size proof
SCENARIOS = {'severe_model_only': Decimal('0.0007'),
             'supersevere_model_only': Decimal('0.0014')}
TRAIN_START = datetime(2021, 12, 9, tzinfo=timezone.utc)
TRAIN_END = datetime(2023, 10, 1, tzinfo=timezone.utc)


def dec(value, *, positive=False, nonnegative=False):
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError('C139_CANONICAL_DECIMAL_STRING_REQUIRED')
    try:
        x = Decimal(value)
    except Exception as e:
        raise ValueError('C139_INVALID_DECIMAL') from e
    if not x.is_finite() or (positive and x <= 0) or (nonnegative and x < 0):
        raise ValueError('C139_INVALID_FINITE_VALUE')
    return x


def rebalance(*, time, decision_feature_max_time, scenario, before,
              target_weights, marks, native_fees):
    """Produce paired fills with exact net-base hedge and NAV fee identity.

    All financial inputs are modeled/declared; no exchange authentication.
    `before` includes cash, spot_base and perp_base dictionaries of strings.
    `native_fees` per asset contains spot, perp, spot_currency BASE/QUOTE.
    This adapter never makes a decision or changes a signal; it only executes
    the already preregistered D1 target and the fixed 1.0x gross constraint.
    """
    if (type(time) is not datetime or time.tzinfo is not timezone.utc or
        time.minute or time.second or time.microsecond or
        not TRAIN_START <= time < TRAIN_END or
        type(decision_feature_max_time) is not datetime or
        decision_feature_max_time.tzinfo is not timezone.utc or
        decision_feature_max_time > time - timedelta(hours=1)):
        raise ValueError('C139_SEALED_OR_LOOKAHEAD_DECISION')
    if scenario not in SCENARIOS:
        raise ValueError('C139_UNPREREGISTERED_SCENARIO')
    if (type(before) is not dict or set(before) != {'cash_quote','spot_base','perp_base'} or
        any(type(x) is not dict or set(x) != set(ASSETS) for x in
            (before['spot_base'],before['perp_base'])) or
        any(type(x) is not dict or set(x) != set(ASSETS) for x in
            (target_weights, marks, native_fees))):
        raise ValueError('C139_INCOMPLETE_BTC_ETH_ACCOUNT')
    cash = dec(before['cash_quote'], nonnegative=True)
    spot = {a: dec(before['spot_base'][a], nonnegative=True) for a in ASSETS}
    perp = {a: dec(before['perp_base'][a]) for a in ASSETS}
    prices = {}
    fees = {}
    weights = {}
    for a in ASSETS:
        if type(marks[a]) is not dict or set(marks[a]) != {'spot','perp'}:
            raise ValueError('C139_MISSING_PAIRED_MARKS')
        prices[a] = {leg: dec(marks[a][leg],positive=True) for leg in ('spot','perp')}
        if type(native_fees[a]) is not dict or set(native_fees[a]) != {'spot','perp','spot_currency'}:
            raise ValueError('C139_NATIVE_FEE_SCHEMA')
        fees[a] = {leg: dec(native_fees[a][leg],nonnegative=True) for leg in ('spot','perp')}
        if any(fees[a][leg] > Decimal('.01') for leg in ('spot','perp')):
            raise ValueError('C139_NATIVE_FEE_OUT_OF_RANGE')
        if native_fees[a]['spot_currency'] not in ('BASE','QUOTE'):
            raise ValueError('C139_FEE_CURRENCY')
        weights[a] = dec(target_weights[a],nonnegative=True)
        if weights[a] > MAX_PAIR:
            raise ValueError('C139_PAIR_WEIGHT_CAP')
    nav_before = cash + sum(spot[a]*prices[a]['spot'] for a in ASSETS)
    if nav_before <= 0:
        raise ValueError('C139_NONPOSITIVE_NAV')
    # Fixed gross cap; scale both preregistered target opportunities uniformly.
    target_gross = sum(weights[a] * (Decimal('1') +
                        prices[a]['perp']/prices[a]['spot']) for a in ASSETS)
    # Budget for native+worst-scenario stress *before* sizing. Two-sided
    # turnover can approach 2x gross when replacing holdings; a fixed
    # worst-case fee reserve prevents apparent 1.0x gross from exceeding
    # actual post-fee NAV. No scenario-specific risk appetite or tuning.
    max_native = max(fees[a][leg] for a in ASSETS for leg in ('spot','perp'))
    max_cost = max_native + max(SCENARIOS.values())
    safe_gross_fraction = MAX_GROSS / (Decimal('1') + Decimal('2')*max_cost)
    gross_scale = min(Decimal('1'), safe_gross_fraction / target_gross) if target_gross else Decimal('1')
    target_spot = {a: nav_before*weights[a]*gross_scale/prices[a]['spot'] for a in ASSETS}
    stress = SCENARIOS[scenario]
    fills = []
    def snapshot():
        return {'cash_quote':str(cash),
                'spot_base':{asset:str(spot[asset]) for asset in ASSETS},
                'perp_base':{asset:str(perp[asset]) for asset in ASSETS}}
    native_total = Decimal('0')
    stress_total = Decimal('0')
    for a in ASSETS:
        # Spot BASE-fee trades need extra bought units, or fewer sold units,
        # to leave exactly the intended *net* spot inventory.
        delta = target_spot[a] - spot[a]
        rate = fees[a]['spot']
        base_fee = native_fees[a]['spot_currency'] == 'BASE'
        if abs(delta) >= MODEL_SPOT_QTY_STEP:
            before_fill = snapshot()
            side = 'buy' if delta > 0 else 'sell'
            q = (abs(delta)/(Decimal('1')-rate if delta > 0 else Decimal('1')+rate)
                 if base_fee else abs(delta)).quantize(MODEL_SPOT_QTY_STEP, rounding=ROUND_DOWN)
            if q == 0:
                raise ValueError('C139_ZERO_MODELED_LOT')
            notional = q * prices[a]['spot']
            native = notional * rate
            extra = notional * stress
            cash += (notional if side == 'sell' else -notional) - extra - (Decimal('0') if base_fee else native)
            spot[a] += (q if side == 'buy' else -q) - (q*rate if base_fee else Decimal('0'))
            native_total += native
            stress_total += extra
            fills.append({'trade_id':f'C139-{time.isoformat()}-{a}-spot',
                          'time':time,'before':before_fill,'after':snapshot(),
                          'quote_notional':str(notional),
                          'booked_total_fee_quote':str(native+extra),
                          'inventory_base_fee_debit_units':str(q*rate if base_fee else Decimal('0')),
                          'asset':a,'leg':'spot','side':side,'base_quantity':str(q),
                          'execution_price_quote_per_base':str(prices[a]['spot']),
                          'native_fee_quote':str(native),'stress_fee_quote':str(extra),
                          'base_fee_units':str(q*rate if base_fee else Decimal('0'))})
        # Perp short is BASE-matched to the *net* post-fee spot inventory.
        perp_delta = -spot[a] - perp[a]
        if perp_delta:
            before_fill = snapshot()
            side = 'buy' if perp_delta > 0 else 'sell'
            q = abs(perp_delta)
            notional = q*prices[a]['perp']
            native = notional*fees[a]['perp']
            extra = notional*stress
            cash -= native + extra
            perp[a] += perp_delta
            native_total += native
            stress_total += extra
            fills.append({'trade_id':f'C139-{time.isoformat()}-{a}-perp',
                          'time':time,'before':before_fill,'after':snapshot(),
                          'quote_notional':str(notional),
                          'booked_total_fee_quote':str(native+extra),
                          'asset':a,'leg':'perp','side':side,'base_quantity':str(q),
                          'execution_price_quote_per_base':str(prices[a]['perp']),
                          'native_fee_quote':str(native),'stress_fee_quote':str(extra),
                          'base_fee_units':'0'})
    if cash < 0:
        raise ValueError('C139_INSUFFICIENT_CASH_NO_MARGIN_BORROW_ALLOWED')
    if any(spot[a] != -perp[a] for a in ASSETS):
        raise ValueError('C139_BROKEN_PAIRED_HEDGE')
    gross = sum(spot[a]*prices[a]['spot']+abs(perp[a])*prices[a]['perp'] for a in ASSETS)
    nav_after = cash + sum(spot[a]*prices[a]['spot'] for a in ASSETS)
    if gross - nav_after*MAX_GROSS > Decimal('1e-18'):
        raise ValueError('C139_POST_FEE_GROSS_EXCEEDED')
    if abs((nav_after - nav_before) + native_total + stress_total) > Decimal('1e-18'):
        raise ValueError('C139_NAV_FEE_IDENTITY')
    return {'status':'C139_MODEL_ONLY_PRE_ECONOMIC_HOLD',
            'after':{'cash_quote':str(cash),
                     'spot_base':{a:str(spot[a]) for a in ASSETS},
                     'perp_base':{a:str(perp[a]) for a in ASSETS}},
            'fills':fills, 'native_fee_quote':str(native_total),
            'stress_fee_quote':str(stress_total), 'gross_scale':str(gross_scale),
            'gross_quote':str(gross), 'nav_before':str(nav_before),
            'nav_after':str(nav_after),
            'native_receipts_authenticated':False,
            'execution_fills_authenticated':False,
            'funding_settlements_authenticated':False,
            'historical_roi_authorized':False,
            'validation_opened':False,'holdout_opened':False,
            'promotion_authorized':False,'orders_enabled':False}
