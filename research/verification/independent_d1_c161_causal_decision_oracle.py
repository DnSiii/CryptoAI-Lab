"""C161 independent causal-feature / signal-ceiling check for D1 TRAIN journals.

Consumes the same full-hour journals as C160, plus independently supplied
per-decision PairedBar/FundingFix evidence. Recomputes 168h regime and the
necessary (not sufficient) funding/basis eligibility of any positive weight.
Native fee veto can only remove exposure, so zero weights are not interpreted
as a positive edge. No first-party authentication, orders, ROI or promotion.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal, InvalidOperation
from math import log, sqrt

from research.tools.v99_r106_d1_basis_carry_preregistered import (
    PairedBar, FundingFix, Decision, COST_SHOCKS, MAX_ASSET_SPOT,
)
from research.tools.v99_r106_d1_full_train_guard import START, HOURS
from research.verification.independent_d1_c148_risk_fold_scorecard import SCENARIOS
from research.verification.independent_d1_c160_integrated_structural_chain import (
    verify_integrated_train_structural_only,
)

ASSETS = ('BTC', 'ETH')


def amount(value):
    try:
        n = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError('C161_INVALID_NUMBER') from exc
    if not n.is_finite():
        raise ValueError('C161_NONFINITE_NUMBER')
    return n


def check_causal_decision_evidence(journals, decisions_by_scenario, evidence_by_decision):
    """Check all 219,744 asset-hour feature pairs and 3,924 last-three fixes.

    Independent evidence must match the journal, but even matching labels and
    timestamps are not exchange receipts. Historical funding announcement
    availability remains externally unauthenticated.
    """
    if (type(journals) is not dict or set(journals) != set(SCENARIOS) or
            type(decisions_by_scenario) is not dict or
            set(decisions_by_scenario) != set(SCENARIOS) or
            type(evidence_by_decision) is not dict):
        raise ValueError('C161_TWO_SCENARIOS_AND_EVIDENCE_REQUIRED')
    frames = journals[SCENARIOS[0]].get('frames')
    if not isinstance(frames, list) or len(frames) != HOURS:
        raise ValueError('C161_FULL_TRAIN_REQUIRED')
    times = tuple(START + timedelta(hours=i) for i in range(168, HOURS, 24))
    if len(times) != 654 or set(evidence_by_decision) != set(times):
        raise ValueError('C161_EXACT_654_DECISION_EVIDENCE_REQUIRED')
    if any(set(decisions_by_scenario[s]) != set(times) for s in SCENARIOS):
        raise ValueError('C161_DECISION_GRID_MISMATCH')
    funding_seen = {a: [] for a in ASSETS}
    bars_checked = fixes_checked = 0
    for i, frame in enumerate(frames):
        t = START + timedelta(hours=i)
        if frame.get('time') != t:
            raise ValueError('C161_HOURLY_GRID_MISMATCH')
        if t in evidence_by_decision:
            ev = evidence_by_decision[t]
            if (type(ev) is not dict or not {'bars', 'funding'} <= set(ev) or
                    type(ev['bars']) is not dict or set(ev['bars']) != set(ASSETS) or
                    type(ev['funding']) is not dict or set(ev['funding']) != set(ASSETS)):
                raise ValueError('C161_INCOMPLETE_FEATURE_EVIDENCE')
            eligibility = {}
            btc_prices = None
            for asset in ASSETS:
                history = ev['bars'][asset]
                if type(history) not in (list, tuple) or len(history) != 168:
                    raise ValueError('C161_EXACT_168H_LOOKBACK_REQUIRED')
                spot_prices = []
                for j, bar in enumerate(history):
                    source = frames[i - 168 + j]
                    at = t - timedelta(hours=168-j)
                    if (type(bar) is not PairedBar or bar.time != at or
                            bar.observed_at != at or bar.asset != asset or
                            bar.source_spot != 'OKX' or bar.source_perp != 'OKX' or
                            source['time'] != at or
                            amount(bar.spot_open) != amount(source['marks'][asset]['spot']) or
                            amount(bar.perp_open) != amount(source['marks'][asset]['perp'])):
                        raise ValueError('C161_EARLY_FEATURE_BAR_MISMATCH')
                    spot_prices.append(float(bar.spot_open))
                    bars_checked += 1
                if asset == 'BTC':
                    btc_prices = spot_prices
                declared = ev['funding'][asset]
                if type(declared) not in (tuple, list):
                    raise ValueError('C161_FUNDING_EVIDENCE_REQUIRED')
                known = sorted((f for f in declared if type(f) is FundingFix and
                                f.asset == asset and f.source == 'OKX' and
                                f.instrument == asset + '-USDT-SWAP' and
                                f.announced_at <= t-timedelta(hours=1) and
                                f.settled_at <= t-timedelta(hours=1)),
                               key=lambda f: f.settled_at)[-3:]
                actual = funding_seen[asset][-3:]
                if len(known) != 3 or len(actual) != 3:
                    raise ValueError('C161_THREE_KNOWN_SETTLEMENTS_REQUIRED')
                for f, raw in zip(known, actual):
                    if f.settled_at != raw['time'] or amount(f.rate) != amount(raw['rate']):
                        raise ValueError('C161_SETTLED_FUNDING_MISMATCH')
                    fixes_checked += 1
                if (any(b.settled_at-a.settled_at != timedelta(hours=8)
                        for a,b in zip(known, known[1:])) or
                        t-known[-1].settled_at > timedelta(hours=9)):
                    raise ValueError('C161_STALE_OR_WRONG_FUNDING_INTERVAL')
                projected = sum((amount(f.rate) for f in known), Decimal('0'))
                basis = amount(history[-1].perp_open)/amount(history[-1].spot_open)-1
                eligibility[asset] = (all(amount(f.rate)>0 for f in known) and
                                      abs(basis) < Decimal('.01'))
                eligibility[asset] = (eligibility[asset], projected)
            log_returns = [log(b/a) for a,b in zip(btc_prices, btc_prices[1:])]
            mean = sum(log_returns)/len(log_returns)
            vol = sqrt(sum((x-mean)**2 for x in log_returns)/(len(log_returns)-1))*sqrt(8760)
            move = btc_prices[-1]/btc_prices[0]-1
            regime = ('BULL' if move > .04 else 'BEAR' if move < -.04 else 'SIDEWAYS')
            regime += '__'+('HIGH_VOLATILITY' if vol > .85 else 'LOW_VOLATILITY')
            for scenario in SCENARIOS:
                d = decisions_by_scenario[scenario][t]
                if (type(d) is not Decision or d.time != t or d.regime != regime or
                        d.feature_max_time != t-timedelta(hours=1) or
                        d.funding_asof != t-timedelta(hours=1)):
                    raise ValueError('C161_REGIME_OR_CAUSAL_DECISION_MISMATCH')
                for asset, weight in (('BTC',d.btc_pair_weight),('ETH',d.eth_pair_weight)):
                    allowed, projected = eligibility[asset]
                    threshold = Decimal('8')*amount(COST_SHOCKS[scenario])
                    if (weight not in (0, MAX_ASSET_SPOT) or
                            (weight > 0 and not (allowed and projected > threshold))):
                        raise ValueError('C161_UNSUPPORTED_POSITIVE_EXPOSURE')
        for f in frame['funding']:
            if (f['asset'] not in ASSETS or f['time'] != t or
                    f['source'] != 'OKX' or f['instrument'] != f['asset']+'-USDT-SWAP'):
                raise ValueError('C161_FUNDING_ROW_INVALID')
            funding_seen[f['asset']].append(f)
    if bars_checked != 219744 or fixes_checked != 3924:
        raise ValueError('C161_INCOMPLETE_INDEPENDENT_REEXECUTION')
    return {'status':'C161_CAUSAL_FEATURE_AND_ELIGIBILITY_STRUCTURAL_ONLY',
            'decision_hours_checked':654,'asset_hour_pairs_checked':bars_checked,
            'last_three_funding_fixes_checked':fixes_checked,
            'regimes_recomputed':True,'positive_exposure_eligibility_checked':True,
            'fee_veto_exactly_reexecuted':False,
            'funding_announcement_first_party_authenticated':False,
            'historical_economics_authorized':False,'promotion_authorized':False,
            'validation_opened':False,'holdout_opened':False,'orders_enabled':False}


def verify_c161_integrated_structural_only(journals, decisions_by_scenario,
                                          funding_schedule, initial_marks,
                                          initial_marks_time, evidence_by_decision):
    account = verify_integrated_train_structural_only(
        journals, decisions_by_scenario, funding_schedule,
        initial_marks, initial_marks_time)
    feature = check_causal_decision_evidence(journals, decisions_by_scenario,
                                             evidence_by_decision)
    return {'status':'C161_INTEGRATED_DATA_ONLY_HOLD',
            'c160_account_funding_risk':account,
            'c161_causal_feature_check':feature,
            'first_party_okx_receipts_authenticated':False,
            'historical_roi_authorized':False,'promotion_authorized':False,
            'validation_opened':False,'holdout_opened':False,'orders_enabled':False}
