"""C93: bind the *reported hourly modeled NAV* to an independent native ledger.

This bridges C82 mark-only and C83 active-fill oracles to the C74/C78 hourly
modeled-NAV output, including open-vs-fill perp anchor unrealized variation.
Never a source of historical market provenance, fills, funding or realized ROI.
No orders, validation, holdout, or promotion.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from collections.abc import Mapping

from research.oracles.v99_r106_d1_cycle82_independent_mark_ledger import independently_verify_mark
from research.oracles.v99_r106_d1_cycle83_independent_active_ledger import verify_active_hour

ASSETS = ('BTC', 'ETH')
SCENARIOS = ('severe_model_only', 'supersevere_model_only')


def exact(x):
    if type(x) not in (str, int, Decimal):
        raise ValueError('C93_EXACT_DECIMAL_REQUIRED')
    try:
        y = Decimal(x)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError('C93_BAD_DECIMAL') from exc
    if not y.is_finite():
        raise ValueError('C93_NONFINITE_DECIMAL')
    return y


def _native_nav(*, state, spot_open, perp_open, contract_specs, at):
    """Independent quote-cash + spot + short-perp unrealized at the OPEN."""
    if any(not isinstance(m, Mapping) or set(m) != set(ASSETS)
           for m in (spot_open, perp_open, contract_specs)):
        raise ValueError('C93_COMPLETE_TWO_ASSET_NATIVE_MARKS_REQUIRED')
    cash = exact(state.quote.cash_quote)
    nav = cash
    components = {'cash': str(cash)}
    for a in ASSETS:
        spec = contract_specs[a]
        if spec.asset != a or not (spec.valid_from <= at < spec.valid_until):
            raise ValueError('C93_NATIVE_SPEC_ERA_MISMATCH')
        sp, pp = exact(spot_open[a]), exact(perp_open[a])
        units = exact(dict(state.quote.spot_base)[a])
        contracts = exact(dict(state.quote.perp_contracts)[a])
        anchor = exact(dict(state.quote.perp_mark_anchor)[a])
        lot = exact(spec.lot_size_contracts)
        if (sp <= 0 or pp <= 0 or anchor <= 0 or lot <= 0 or units < 0 or contracts > 0
                or contracts / lot != (contracts / lot).to_integral_value()):
            raise ValueError('C93_NATIVE_MARK_LOT_OR_POSITION_INVALID')
        base = contracts * exact(spec.contract_value_base) * exact(spec.multiplier)
        spot_value = units * sp
        perp_unrealized = base * (pp - anchor)
        nav += spot_value + perp_unrealized
        components[a + '_spot_value'] = str(spot_value)
        components[a + '_perp_unrealized'] = str(perp_unrealized)
    if nav <= 0:
        raise ValueError('C93_NONPOSITIVE_NATIVE_NAV')
    return nav, components


def verify_hourly_nav_binding(*, before, after, at, scenario, spot_open,
                              perp_open, completed_ranges, contract_specs,
                              reported_modeled_nav, transitions=None,
                              funding_fixes=None, funding_marks=None,
                              tolerance='0.00000001'):
    """Re-execute one hour independently, then bind the hourly NAV report.

    C82 is used when there are no fills; C83 when a daily active fill exists.
    C83 validates cash/funding/fills but its `nav_at_open` deliberately does
    not include the short-perp fill-anchor variation. This bridge does.
    """
    if (type(at) is not datetime or at.tzinfo is not timezone.utc or
            at.minute or at.second or at.microsecond or scenario not in SCENARIOS):
        raise ValueError('C93_NONCANONICAL_HOUR_OR_SCENARIO')
    if transitions is None:
        transitions = {}
    if not isinstance(transitions, Mapping):
        raise ValueError('C93_TRANSITION_MAPPING_REQUIRED')
    common = dict(before=before, after=after, at=at, spot_open=spot_open,
                  perp_open=perp_open, completed_ranges=completed_ranges,
                  contract_specs=contract_specs,
                  funding_fixes=funding_fixes or {}, funding_marks=funding_marks or {})
    if transitions:
        proof = verify_active_hour(scenario=scenario, transitions=dict(transitions), **common)
        kind = 'C83_ACTIVE_FILL_ORACLE'
    else:
        proof = independently_verify_mark(**common)
        kind = 'C82_MARK_ONLY_ORACLE'
    nav, components = _native_nav(state=after, spot_open=spot_open,
                                  perp_open=perp_open, contract_specs=contract_specs, at=at)
    if not transitions and abs(nav - exact(proof['nav'])) > exact(tolerance):
        raise ValueError('C93_MARK_ORACLE_NAV_DIVERGENCE')
    claimed = exact(reported_modeled_nav)
    if abs(nav - claimed) > exact(tolerance):
        raise ValueError('C93_REPORTED_HOURLY_NAV_UNBOUND')
    return {'status':'SYNTHETIC_INDEPENDENT_NATIVE_HOURLY_NAV_BOUND_ONLY',
            'at':at.isoformat(), 'scenario':scenario, 'oracle':kind,
            'independent_modeled_nav_quote':str(nav), 'components':components,
            'native_fill_and_mark_accounting_oracle_passed':True,
            'historical_economics_authorized':False,
            'real_fills_authenticated':False,
            'account_settled_funding_authenticated':False,
            'historical_roi_calculated':False,
            'validation_opened':False, 'final_holdout_opened':False,
            'promotion_authorized':False, 'orders_enabled':False}


def bind_two_scenario_hourly_journals(*, severe, supersevere,
                                      evidence_by_scenario, start, end,
                                      fixture_only=False):
    """Fail-closed two-cost hourly scorer-NAV preflight (no economic approval).

    One independent C82/C83 verification per scenario per journal hour.
    All exogenous market inputs are identical across cost paths; account
    states are separate. `fixture_only` permits shortened *synthetic* tests.
    """
    from datetime import timedelta
    from research.tools.v99_r106_d1_train_scoring_gate import TRAIN_START, TRAIN_END
    if (type(start) is not datetime or type(end) is not datetime or
            start.tzinfo is not timezone.utc or end.tzinfo is not timezone.utc or
            not TRAIN_START <= start < end <= TRAIN_END or
            any((x.minute,x.second,x.microsecond)!=(0,0,0) for x in (start,end)) or
            ((start,end)!=(TRAIN_START,TRAIN_END) and not fixture_only)):
        raise ValueError('C93_SEALED_OR_NONFROZEN_SCORING_PARTITION')
    if (severe.scenario, supersevere.scenario) != SCENARIOS:
        raise ValueError('C93_COST_PATH_ORDER_MISMATCH')
    if not isinstance(evidence_by_scenario, Mapping) or set(evidence_by_scenario) != set(SCENARIOS):
        raise ValueError('C93_BOTH_COST_PATH_EVIDENCE_REQUIRED')
    n=int((end-start).total_seconds()//3600)
    if any(len(j.hours)!=n or len(evidence_by_scenario[j.scenario])!=n
           for j in (severe,supersevere)):
        raise ValueError('C93_FULL_HOURLY_EVIDENCE_COVERAGE_REQUIRED')
    exogenous=('at','spot_open','perp_open','completed_ranges','contract_specs',
               'funding_fixes','funding_marks')
    prev={s:None for s in SCENARIOS}
    for i in range(n):
        at=start+timedelta(hours=i)
        frame_by_scenario={s:evidence_by_scenario[s][i] for s in SCENARIOS}
        a,b=(frame_by_scenario[s] for s in SCENARIOS)
        if not isinstance(a,Mapping) or not isinstance(b,Mapping):
            raise ValueError('C93_INVALID_HOURLY_FRAME')
        if any(a.get(k)!=b.get(k) for k in exogenous):
            raise ValueError('C93_COST_SCENARIO_EXOGENOUS_DIVERGENCE')
        for journal in (severe,supersevere):
            s=journal.scenario
            f=frame_by_scenario[s]
            if f.get('at')!=at or journal.hours[i].time!=at:
                raise ValueError('C93_HOURLY_TIME_GAP_OR_LEAK')
            if prev[s] is not None and f.get('before')!=prev[s]:
                raise ValueError('C93_ACCOUNT_RESET_OR_STATE_CHAIN_BREAK')
            kw={k:f[k] for k in ('before','after','at','spot_open','perp_open',
                                 'completed_ranges','contract_specs')}
            kw.update(scenario=s, reported_modeled_nav=str(journal.hours[i].nav),
                      transitions=f.get('transitions'),
                      funding_fixes=f.get('funding_fixes'),
                      funding_marks=f.get('funding_marks'), tolerance='0.000001')
            verify_hourly_nav_binding(**kw)
            prev[s]=f['after']
    return {'status':'SYNTHETIC_TWO_COST_FULL_HOURLY_NAV_BOUND_NO_PROMOTION',
            'hours_per_scenario':n,'independent_native_hour_checks':2*n,
            'five_folds_verified':False, 'historical_roi_calculated':False,
            'exchange_provenance_authenticated':False,
            'historical_economics_authorized':False,
            'validation_opened':False,'final_holdout_opened':False,
            'promotion_authorized':False,'orders_enabled':False}
