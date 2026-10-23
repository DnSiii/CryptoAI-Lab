"""C162 exact C136 native-fee-veto replay over both full TRAIN cost paths.

Model-only and unauthenticated: this does not establish actual OKX historical
fees, fills, funding, ROI, orders, or permission to open sealed partitions.
"""
from datetime import timedelta
from decimal import Decimal, ROUND_FLOOR
from research.tools.v99_r106_d1_basis_carry_preregistered import (
    ASSETS, COST_SHOCKS, Decision, decide,
)
from research.tools.v99_r106_d1_native_fee_veto_cycle136 import (
    CausalFeeTier, fee_bound_intent,
)
from research.tools.v99_r106_d1_full_train_guard import START, HOURS

SCENARIOS = tuple(COST_SHOCKS)


def verify_exact_fee_veto(decisions_by_scenario, evidence_by_decision,
                          fee_tiers_by_decision):
    times = tuple(START + timedelta(hours=i) for i in range(168, HOURS, 24))
    if (type(decisions_by_scenario) is not dict or
            set(decisions_by_scenario) != set(SCENARIOS) or
            type(evidence_by_decision) is not dict or
            set(evidence_by_decision) != set(times) or
            type(fee_tiers_by_decision) is not dict or
            set(fee_tiers_by_decision) != set(times) or
            any(type(decisions_by_scenario[s]) is not dict or
                set(decisions_by_scenario[s]) != set(times) for s in SCENARIOS)):
        raise ValueError('C162_EXACT_FULL_TRAIN_TWO_SCENARIOS_REQUIRED')
    checked = 0
    vetoed = 0
    for t in times:
        ev = evidence_by_decision[t]
        tiers = fee_tiers_by_decision[t]
        if (type(ev) is not dict or set(ev) != {'bars','funding'} or
                type(tiers) is not dict or set(tiers) != set(ASSETS)):
            raise ValueError('C162_MISSING_MARKET_OR_FEE_EVIDENCE')
        for a in ASSETS:
            tier = tiers[a]
            if (type(tier) is not CausalFeeTier or
                    tier.observed_at > t-timedelta(hours=1) or
                    tier.evidence.valid_from > t-timedelta(hours=1) or
                    tier.evidence.valid_until <= t-timedelta(hours=1)):
                raise ValueError('C162_FUTURE_OR_MISSING_NATIVE_TIER')
        for scenario in SCENARIOS:
            original = decide(t, ev['bars'], ev['funding'], COST_SHOCKS[scenario])
            replay = fee_bound_intent(time=t, bars=ev['bars'],
                                      funding=ev['funding'], scenario=scenario,
                                      fee_tiers=tiers)
            actual = decisions_by_scenario[scenario][t]
            expected = replay['decision']
            if (type(actual) is not Decision or actual != expected or
                    actual.status != 'C136_FEE_VETO_MODEL_ONLY_NO_ROI'):
                raise ValueError('C162_EXACT_C136_DECISION_MISMATCH')
            for a in ASSETS:
                fixes = sorted((f for f in ev['funding'][a]
                                if f.announced_at <= t-timedelta(hours=1) and
                                f.settled_at <= t-timedelta(hours=1)),
                               key=lambda f:f.settled_at)[-3:]
                if len(fixes) != 3:
                    raise ValueError('C162_MISSING_CAUSAL_FUNDING')
                forecast = (sum((Decimal(str(f.rate)) for f in fixes),Decimal('0'))
                            .quantize(Decimal('.000000000001'),rounding=ROUND_FLOOR))
                tier = tiers[a].evidence
                hurdle = Decimal('2') * (
                    Decimal('2')*(Decimal(str(tier.spot_taker))+
                                  Decimal(str(tier.perp_taker))) +
                    Decimal('4')*Decimal(str(COST_SHOCKS[scenario])))
                prior = getattr(original, a.lower()+'_pair_weight')
                independent = prior if forecast > hurdle else 0.0
                if getattr(actual,a.lower()+'_pair_weight') != independent:
                    raise ValueError('C162_INDEPENDENT_HURDLE_DISAGREES')
                vetoed += int(prior > 0 and independent == 0)
            checked += 1
    return {'status':'C162_EXACT_NATIVE_VETO_STRUCTURAL_ONLY',
            'decision_scenarios_checked':checked,
            'asset_scenario_decisions_checked':checked*len(ASSETS),
            'vetoed_asset_scenario_decisions':vetoed,
            'native_fee_first_party_authenticated':False,
            'historical_economics_authorized':False,
            'promotion_authorized':False,
            'validation_opened':False,'holdout_opened':False,
            'orders_enabled':False}
