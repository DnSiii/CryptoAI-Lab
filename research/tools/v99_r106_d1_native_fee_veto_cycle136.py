"""C136 additive, ex-ante D1 native-fee veto. Model-only; NO economic certification.

Original preregistered D1 decision remains immutable. This stricter overlay can
only reduce exposure, never create a new trade, and must be frozen before any
historical economic TRAIN. Do not compare/choose overlays by PnL.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
from research.tools.v99_r106_d1_basis_carry_preregistered import (
    ASSETS, COST_SHOCKS, ENTRY_FUNDING_TO_STRESS_COST,
    FUNDING_LOOKBACK, FeeEvidence, Decision, decide,
)

UTC = timezone.utc


@dataclass(frozen=True)
class CausalFeeTier:
    evidence: FeeEvidence
    observed_at: datetime

    def __post_init__(self):
        if (type(self.observed_at) is not datetime or
                self.observed_at.tzinfo is not UTC):
            raise ValueError('C136_FEE_OBSERVATION_EXPLICIT_UTC')


def fee_bound_intent(*, time, bars, funding, scenario, fee_tiers):
    """Apply a fixed 2x full native+stress roundtrip hurdle to D1 intent.

    Two spot and two perp taker fills per pair. Both entry and hypothetical
    exit use the *known at decision* fee tier; exit fees are not authenticated.
    Stress is additive per fill. This is a conservative entry veto, not a
    substitute for actual exchange account/fill/funding evidence.
    """
    if scenario not in COST_SHOCKS or not isinstance(fee_tiers, dict) or set(fee_tiers) != set(ASSETS):
        raise ValueError('C136_COST_OR_FEE_SCHEMA')
    stress = Decimal(str(COST_SHOCKS[scenario]))
    original = decide(time, bars, funding, float(stress))
    cutoff = time - timedelta(hours=1)
    new_weights = {}
    details = {}
    for asset in ASSETS:
        row = fee_tiers[asset]
        if not isinstance(row, CausalFeeTier) or not isinstance(row.evidence, FeeEvidence):
            raise ValueError('C136_NATIVE_FEE_TIER_REQUIRED')
        tier = row.evidence
        if (tier.exchange != 'OKX' or row.observed_at > cutoff or
                tier.valid_from > cutoff or tier.valid_until <= cutoff):
            raise ValueError('C136_FEE_TIER_NOT_CAUSALLY_KNOWN')
        if tier.spot_taker < 0 or tier.perp_taker < 0:
            raise ValueError('C136_INVALID_NATIVE_FEE')
        fixes = sorted((f for f in funding[asset]
                        if f.announced_at <= cutoff and f.settled_at <= cutoff),
                       key=lambda f: f.settled_at)[-FUNDING_LOOKBACK:]
        if len(fixes) != FUNDING_LOOKBACK:
            raise ValueError('C136_MISSING_CAUSAL_FIXES')
        # FundingFix stores binary floats; tiny conversion drift at an exact
        # strict-inequality boundary must NEVER manufacture an entry. Floor
        # to 1e-12 of rate (more conservative than an exchange tick).
        forecast_raw = Decimal('3') * sum(Decimal(str(f.rate)) for f in fixes) / Decimal(FUNDING_LOOKBACK)
        forecast = forecast_raw.quantize(Decimal('0.000000000001'), rounding=ROUND_FLOOR)
        native_roundtrip = Decimal('2') * (
            Decimal(str(tier.spot_taker)) + Decimal(str(tier.perp_taker)))
        full_roundtrip = native_roundtrip + Decimal('4') * stress
        threshold = Decimal(str(ENTRY_FUNDING_TO_STRESS_COST)) * full_roundtrip
        # The original threshold is <= this one for nonnegative native fees.
        old_threshold = Decimal(str(ENTRY_FUNDING_TO_STRESS_COST)) * Decimal('4') * stress
        if threshold < old_threshold:
            raise AssertionError('C136_NONMONOTONE_COST_HURDLE')
        prior = getattr(original, asset.lower() + '_pair_weight')
        approved = prior if forecast > threshold else 0.0
        if approved > prior:
            raise AssertionError('C136_NEW_TRADE_FORBIDDEN')
        new_weights[asset] = approved
        details[asset] = {
            'projected_24h_funding_model_only': str(forecast),
            'full_native_plus_stress_roundtrip_fraction': str(full_roundtrip),
            'required_2x_roundtrip_fraction': str(threshold),
            'original_pair_weight': prior,
            'fee_veto_applied': prior > 0 and approved == 0,
            'exit_fee_assumed_not_authenticated': True,
        }
    result = Decision(original.time, new_weights['BTC'], new_weights['ETH'],
                      original.regime, original.feature_max_time,
                      original.funding_asof, 'C136_FEE_VETO_MODEL_ONLY_NO_ROI')
    return {
        'decision': result, 'assets': details, 'scenario': scenario,
        'status': 'C136_CONSERVATIVE_FEE_VETO_ONLY_HOLD',
        'changed_original_preregistration': False,
        'new_entries_possible': False,
        'native_fee_receipts_authenticated': False,
        'future_exit_fee_authenticated': False,
        'settled_account_funding_authenticated': False,
        'historical_economics_authorized': False,
        'validation_opened': False, 'holdout_opened': False,
        'promotion_authorized': False, 'orders_enabled': False,
    }
