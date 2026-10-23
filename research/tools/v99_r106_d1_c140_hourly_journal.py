"""C140 model-only D1 hourly journal constructor; no exchange auth, orders or ROI.

Builds strict t-1 decision -> paired modeled fills -> marked variation ->
settled-funding cash -> independently replayable C129 hourly frames.
All market/fee/funding inputs are caller-supplied, hence unauthenticated.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from research.tools.v99_r106_d1_basis_carry_preregistered import Decision
from research.tools.v99_r106_d1_target_rebalance_cycle139 import rebalance, dec, SCENARIOS, ASSETS, TRAIN_START, TRAIN_END
from research.tools.v99_r106_d1_hourly_account_bridge_cycle129 import reconcile_hourly_account
from research.verification.independent_d1_funding_schedule_cycle132 import audit_funding_schedule

REGIMES=frozenset(d+'__'+v for d in ('BULL','BEAR','SIDEWAYS') for v in ('HIGH_VOLATILITY','LOW_VOLATILITY'))


def _hour(t):
    return (type(t) is datetime and t.tzinfo is timezone.utc and
            t.minute == t.second == t.microsecond == 0)


def _state_copy(state):
    return {'cash_quote':str(state['cash_quote']),
            'spot_base':{a:str(state['spot_base'][a]) for a in ASSETS},
            'perp_base':{a:str(state['perp_base'][a]) for a in ASSETS}}


def _new_cash(state, cash):
    row = _state_copy(state)
    row['cash_quote'] = str(cash)
    if cash < 0:
        raise ValueError('C140_UNCOLLATERALIZED_NEGATIVE_CASH')
    return row


def build_journal(*, scenario, rows, initial_state, initial_marks,
                  initial_marks_time, native_fee_schedule, decisions,
                  expected_funding_schedule):
    """Build a contiguous TRAIN-only modeled journal; independently replay.

    rows: {time,marks,funding} where funding is a list of C129 schema rows.
    decisions: exact hour -> preregistered D1/C136 Decision, not a new signal.
    Fee tier must be known no later than t-1; modeled spot fee currency explicit.
    Original exchange receipts must be checked separately; this is not proof.
    """
    if scenario not in SCENARIOS or type(rows) not in (tuple,list) or not rows:
        raise ValueError('C140_BAD_SCENARIO_OR_EMPTY_INPUT')
    if not _hour(initial_marks_time) or not isinstance(decisions,dict):
        raise ValueError('C140_BAD_INITIAL_OR_DECISIONS')
    if (type(native_fee_schedule) is not dict or set(native_fee_schedule)!=set(ASSETS)
            or type(initial_marks) is not dict or set(initial_marks)!=set(ASSETS)):
        raise ValueError('C140_INCOMPLETE_NATIVE_SCHEDULE_OR_MARKS')
    prev_t = initial_marks_time
    prev_marks = initial_marks
    after = _state_copy(initial_state)
    frames = []
    decision_times = set()
    for row in rows:
        if type(row) is not dict or set(row)!={'time','marks','funding'}:
            raise ValueError('C140_BAD_INPUT_ROW_SCHEMA')
        t = row['time']
        if not _hour(t) or not TRAIN_START <= t < TRAIN_END or t != prev_t + timedelta(hours=1):
            raise ValueError('C140_NONCONTIGUOUS_OR_SEALED_TRAIN')
        marks = row['marks']
        if type(marks) is not dict or set(marks)!=set(ASSETS):
            raise ValueError('C140_INCOMPLETE_BTC_ETH_MARKS')
        for a in ASSETS:
            if type(marks[a]) is not dict or set(marks[a]) != {'spot','perp'}:
                raise ValueError('C140_INCOMPLETE_PAIRED_MARK')
            for leg in ('spot','perp'):
                dec(marks[a][leg],positive=True)
                dec(prev_marks[a][leg],positive=True)
        before = _state_copy(after)
        variation = sum(dec(before['perp_base'][a]) *
                        (dec(marks[a]['perp'])-dec(prev_marks[a]['perp'])) for a in ASSETS)
        after_mark = _new_cash(before,dec(before['cash_quote'])+variation)
        funding_rows = row['funding']
        if type(funding_rows) not in (list,tuple):
            raise ValueError('C140_BAD_FUNDING_ROWS')
        seen = set()
        funding_cash = Decimal('0')
        for f in funding_rows:
            if (type(f) is not dict or set(f)!={'asset','time','rate','source','instrument'}
                    or f['asset'] not in ASSETS or f['asset'] in seen or f['time'] != t
                    or f['source']!='OKX' or f['instrument']!=f["asset"]+'-USDT-SWAP'):
                raise ValueError('C140_INVALID_FUNDING_ROW')
            rate = dec(f['rate'])
            if abs(rate)>Decimal('.1'):
                raise ValueError('C140_INVALID_FUNDING_RATE')
            a=f['asset']
            funding_cash -= dec(before['perp_base'][a])*dec(marks[a]['perp'])*rate
            seen.add(a)
        after_funding = _new_cash(after_mark,dec(after_mark['cash_quote'])+funding_cash)
        fills=[]
        after = after_funding
        if t in decisions:
            decision = decisions[t]
            if (not isinstance(decision,Decision) or t.hour != 0 or decision.time != t or
                    decision.feature_max_time > t-timedelta(hours=1) or
                    decision.funding_asof > t-timedelta(hours=1) or
                    decision.status != 'C136_FEE_VETO_MODEL_ONLY_NO_ROI' or
                    decision.regime not in REGIMES):
                raise ValueError('C140_NONCAUSAL_OR_UNFROZEN_DECISION')
            tiers={}
            for a in ASSETS:
                schedule=native_fee_schedule[a]
                if type(schedule) not in (list,tuple):
                    raise ValueError('C140_MISSING_NATIVE_FEE_SCHEDULE')
                matching=[f for f in schedule if f['start'] <= t < f['end'] and
                          f.get('observed_at') is not None and
                          f['observed_at'] <= t-timedelta(hours=1)]
                if len(matching)!=1:
                    raise ValueError('C140_NATIVE_FEE_NOT_KNOWN_AT_DECISION')
                f=matching[0]
                tiers[a]={'spot':f['spot_taker'],'perp':f['perp_taker'],
                          'spot_currency':f['spot_fee_currency']}
            proof=rebalance(time=t,decision_feature_max_time=decision.feature_max_time,
                            scenario=scenario,before=after_funding,
                            target_weights={'BTC':str(decision.btc_pair_weight),
                                            'ETH':str(decision.eth_pair_weight)},
                            marks=marks,native_fees=tiers)
            fills=proof['fills']
            after=proof['after']
            decision_times.add(t)
        frames.append({'time':t,'marks':marks,'before':before,
                       'after_mark':after_mark,'funding':funding_rows,
                       'after_funding':after_funding,'fills':fills,'after':after})
        prev_t,prev_marks=t,marks
    if set(decisions)!=decision_times:
        raise ValueError('C140_UNUSED_OR_OUTSIDE_TRAIN_DECISIONS')
    funding_proof=audit_funding_schedule(frames,expected_funding_schedule,
                                       start=rows[0]['time'],end=rows[-1]['time']+timedelta(hours=1))
    oracle_fee_schedule={a:[{k:v for k,v in tier.items() if k!='observed_at'}
                            for tier in native_fee_schedule[a]] for a in ASSETS}
    account_proof=reconcile_hourly_account(scenario=scenario,frames=frames,
                    initial_marks=initial_marks,initial_marks_time=initial_marks_time,
                    native_fee_schedule=oracle_fee_schedule)
    return {'status':'C140_MODEL_ONLY_ACCOUNTING_NOT_ECONOMICS',
            'frames':frames,'funding_proof':funding_proof,
            'account_proof':account_proof,
            'economic_roi_authorized':False,'first_party_receipts_authenticated':False,
            'validation_opened':False,'holdout_opened':False,
            'promotion_authorized':False,'orders_enabled':False}
