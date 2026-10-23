"""V99 D1: single distinct, PRE-ECONOMIC spot/perpetual basis-carry architecture.

NO NETWORK, NO ORDERS, NO exchange-certified results. Inputs are external
provenance-bearing data, not assumed Binance/OKX fee or funding receipts.
Historical economic trial is deliberately locked until source gate passes.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite, log, sqrt
from typing import Sequence

UTC = timezone.utc
ASSETS = ('BTC', 'ETH')
OKX_SWAP_INSTRUMENTS = {'BTC': 'BTC-USDT-SWAP', 'ETH': 'ETH-USDT-SWAP'}
TRAIN_END = datetime(2023, 10, 1, tzinfo=UTC)
VALIDATION_END = datetime(2024, 1, 18, tzinfo=UTC)
MAX_TOTAL_GROSS = 1.0  # 2 legs per asset, <=0.25 NAV on each leg
MAX_ASSET_SPOT = 0.25
LOOKBACK_HOURS = 168
FUNDING_LOOKBACK = 3
REBALANCE_HOURS = 24
ENTRY_FUNDING_TO_STRESS_COST = 2.0
BASIS_ENTRY_ABS = 0.01
BASIS_EXIT_ABS = 0.015
COST_SHOCKS = {'severe_model_only': .0007, 'supersevere_model_only': .0014}


def utc(t: datetime) -> datetime:
    if not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError('UTC required')
    return t


def finite_positive(x: float) -> float:
    if not isfinite(x) or x <= 0:
        raise ValueError('invalid price')
    return x


@dataclass(frozen=True)
class PairedBar:
    time: datetime
    asset: str
    spot_open: float
    perp_open: float
    source_spot: str
    source_perp: str
    observed_at: datetime

    def __post_init__(self):
        utc(self.time); utc(self.observed_at)
        if self.asset not in ASSETS or not self.source_spot or not self.source_perp:
            raise ValueError('missing instrument provenance')
        finite_positive(self.spot_open); finite_positive(self.perp_open)
        # The hourly OPEN cannot be observed before its exchange event hour.
        # Here observed_at denotes the event-time availability of the OPEN,
        # NOT the (usually much later) archive download/capture timestamp.
        # A timestamp in the past would permit impossible foreknowledge.
        if self.observed_at != self.time:
            raise ValueError('D1_OPEN_EVENT_AVAILABILITY_MISMATCH')

    @property
    def basis(self):
        return self.perp_open / self.spot_open - 1


@dataclass(frozen=True)
class FundingFix:
    asset: str
    announced_at: datetime
    settled_at: datetime
    rate: float
    source: str
    instrument: str

    def __post_init__(self):
        utc(self.announced_at); utc(self.settled_at)
        if self.asset not in ASSETS or not self.source or not self.instrument:
            raise ValueError('funding source missing')
        if self.source == 'OKX' and self.instrument != OKX_SWAP_INSTRUMENTS[self.asset]:
            raise ValueError('OKX_FUNDING_INSTRUMENT_MISMATCH')
        if not isfinite(self.rate) or abs(self.rate) > .1 or self.announced_at > self.settled_at:
            raise ValueError('funding timestamp/rate invalid')


@dataclass(frozen=True)
class FeeEvidence:
    exchange: str
    spot_taker: float
    perp_taker: float
    valid_from: datetime
    valid_until: datetime
    tier_reference: str

    def __post_init__(self):
        utc(self.valid_from); utc(self.valid_until)
        if self.exchange != 'OKX' or not self.tier_reference or self.valid_until <= self.valid_from:
            raise ValueError('native fee provenance unavailable')
        if not all(isfinite(x) and 0 <= x <= .01 for x in (self.spot_taker, self.perp_taker)):
            raise ValueError('invalid fee tier')


@dataclass(frozen=True)
class Decision:
    time: datetime
    btc_pair_weight: float
    eth_pair_weight: float
    regime: str
    feature_max_time: datetime
    funding_asof: datetime
    status: str

    def __post_init__(self):
        utc(self.time); utc(self.feature_max_time); utc(self.funding_asof)
        if self.feature_max_time > self.time - timedelta(hours=1):
            raise ValueError('price lookahead')
        if self.funding_asof > self.time - timedelta(hours=1):
            raise ValueError('funding lookahead')
        if not all(isfinite(x) and 0 <= x <= MAX_ASSET_SPOT for x in
                   (self.btc_pair_weight, self.eth_pair_weight)):
            raise ValueError('position limit')
        if 2 * (self.btc_pair_weight + self.eth_pair_weight) > MAX_TOTAL_GROSS + 1e-12:
            raise ValueError('gross limit')


def _fee_schedule_covers_train_window(fee_evidence, start: datetime, end_exclusive: datetime):
    """Require an ordered, gap-free historical tier schedule; no tier extrapolation.

    Still only structural: strings and FeeEvidence objects are NOT first-party
    receipts. The economic gate remains closed regardless of this check.
    """
    if isinstance(fee_evidence, FeeEvidence):
        schedule = (fee_evidence,)
    elif isinstance(fee_evidence, (tuple, list)) and fee_evidence:
        schedule = tuple(fee_evidence)
    else:
        raise ValueError('NO_AUTHENTICATED_OKX_FEE_TIER')
    if any(not isinstance(tier, FeeEvidence) for tier in schedule):
        raise ValueError('INVALID_HISTORICAL_FEE_SCHEDULE')
    if schedule[0].valid_from > start or schedule[-1].valid_until < end_exclusive:
        raise ValueError('FEE_TIER_NOT_HISTORICALLY_VALID')
    for before, after in zip(schedule, schedule[1:]):
        if before.valid_until != after.valid_from:
            raise ValueError('FEE_TIER_SCHEDULE_GAP_OR_OVERLAP')
    return len(schedule)


def historical_source_gate(spot_perp_bars: dict, funding: dict,
                           fee_evidence: FeeEvidence | Sequence[FeeEvidence] | None):
    """Fail closed: do not silently turn Binance OHLCV into OKX spot/perp/funding."""
    if fee_evidence is None:
        raise ValueError('NO_AUTHENTICATED_OKX_FEE_TIER')
    for asset in ASSETS:
        bars = spot_perp_bars.get(asset, ())
        rates = funding.get(asset, ())
        if len(bars) < LOOKBACK_HOURS + 25 or len(rates) < FUNDING_LOOKBACK:
            raise ValueError('NO_PAIRED_MARKET_AND_FUNDING_HISTORY')
        if any(b.asset != asset or b.source_spot != 'OKX' or b.source_perp != 'OKX'
               for b in bars):
            raise ValueError('CROSS_VENUE_PRICE_MIXING')
        if any(f.asset != asset or f.source != 'OKX' or
               f.instrument != OKX_SWAP_INSTRUMENTS[asset] for f in rates):
            raise ValueError('CROSS_VENUE_FUNDING_MIXING')
        if any(f.settled_at >= TRAIN_END or f.announced_at >= TRAIN_END for f in rates):
            raise ValueError('SEALED_FUNDING_PARTITION')
        for before, after in zip(bars, bars[1:]):
            if after.time - before.time != timedelta(hours=1):
                raise ValueError('MISSING_PAIRED_HOURS')
        if bars[-1].time >= TRAIN_END:
            raise ValueError('SEALED_VALIDATION_OR_HOLDOUT')
        _fee_schedule_covers_train_window(fee_evidence, bars[0].time,
                                          bars[-1].time + timedelta(hours=1))
    # All four paired legs must share the exact same hourly TRAIN grid.
    # Per-asset continuity alone is insufficient: a shifted BTC/ETH feed
    # would silently mix prices from different instants in a portfolio NAV.
    grids = [tuple(b.time for b in spot_perp_bars[a]) for a in ASSETS]
    if grids[0] != grids[1]:
        raise ValueError('CROSS_ASSET_HOURLY_GRID_MISMATCH')
    if any(t.minute or t.second or t.microsecond or t.tzinfo is not UTC
           for t in grids[0]):
        raise ValueError('NONCANONICAL_EXPLICIT_UTC_HOURLY_GRID')
    # Structural labels and strings are not exchange authentication.
    # No economic permission may be derived from self-reported source fields.
    return {'structural_consistency': True, 'exchange_authenticated': False,
            'historical_economics_authorized': False,
            'validation_opened': False, 'holdout_opened': False}


def _regime(btc_spot: Sequence[PairedBar]):
    values = [log(b.spot_open / a.spot_open) for a, b in zip(btc_spot, btc_spot[1:])]
    mu = sum(values) / len(values)
    vol = sqrt(sum((x - mu) ** 2 for x in values) / max(1, len(values) - 1)) * sqrt(8760)
    move = btc_spot[-1].spot_open / btc_spot[0].spot_open - 1
    direction = 'BULL' if move > .04 else 'BEAR' if move < -.04 else 'SIDEWAYS'
    return direction + '__' + ('HIGH_VOLATILITY' if vol > .85 else 'LOW_VOLATILITY')


def decide(time: datetime, bars: dict[str, Sequence[PairedBar]],
           funding: dict[str, Sequence[FundingFix]], stress_fee_per_leg: float) -> Decision:
    """Daily causal decision; all features/announcements <= t-1.

    Economic hypothesis: positive, persistent perp funding paid to shorts
    compensates TWO entry/exit legs and basis divergence under stress.
    This is NOT a directional BTC/ETH trend, Donchian, or C1/C2 retune.
    """
    utc(time)
    if time >= TRAIN_END:
        raise ValueError('TRAIN_ONLY_NO_VALIDATION')
    if time.hour != 0:
        raise ValueError('DAILY_DECISION_ONLY')
    if stress_fee_per_leg not in COST_SHOCKS.values():
        raise ValueError('UNPREREGISTERED_COST_SCENARIO')
    eligible = {}
    for asset in ASSETS:
        history = bars[asset]
        if any(f.settled_at >= TRAIN_END or f.announced_at >= TRAIN_END for f in funding[asset]):
            raise ValueError('SEALED_FUNDING_PARTITION')
        if len(history) < LOOKBACK_HOURS or history[-1].time != time - timedelta(hours=1):
            raise ValueError('MISSING_CAUSAL_WARMUP')
        recent = history[-LOOKBACK_HOURS:]
        if any(x.asset != asset or x.source_spot != 'OKX' or x.source_perp != 'OKX'
               for x in recent):
            raise ValueError('NOT_OKX_PAIRED_HISTORY')
        for x, y in zip(recent, recent[1:]):
            if y.time - x.time != timedelta(hours=1):
                raise ValueError('NONCONTIGUOUS_HISTORY')
        known = sorted((f for f in funding[asset]
                        if f.announced_at <= time - timedelta(hours=1)
                        and f.settled_at <= time - timedelta(hours=1)),
                       key=lambda f: f.settled_at)[-FUNDING_LOOKBACK:]
        if len(known) != FUNDING_LOOKBACK or any(f.source != 'OKX' or f.asset != asset or
                                             f.instrument != OKX_SWAP_INSTRUMENTS[asset] for f in known):
            raise ValueError('MISSING_CAUSAL_OKX_FUNDING_FIXES')
        # The frozen 3-fixes-per-day forecast is only meaningful when the
        # actual exchange instrument has an 8-hour settlement schedule.
        # Never annualize 1h/2h/4h funding as if it were 8h.
        if (any(y.settled_at-x.settled_at != timedelta(hours=8)
                for x,y in zip(known,known[1:])) or
            time - known[-1].settled_at > timedelta(hours=9)):
            raise ValueError('FUNDING_INTERVAL_OR_STALENESS_UNVERIFIED')
        # Forecast is NOT an exchange settlement. Use only already-settled
        # historical fixes; future position-specific settlement is unknown.
        projected_24h = 3 * sum(f.rate for f in known) / len(known)
        # Four taker fills in a round trip (spot+perp enter+exit), each stressed.
        threshold = ENTRY_FUNDING_TO_STRESS_COST * 4 * stress_fee_per_leg
        basis = recent[-1].basis
        eligible[asset] = (projected_24h > threshold and
                           all(f.rate > 0 for f in known) and
                           abs(basis) < BASIS_ENTRY_ABS)
    regime = _regime(bars['BTC'][-LOOKBACK_HOURS:])
    # Ex ante equal independent opportunities; cash for unqualified assets.
    weights = {asset: MAX_ASSET_SPOT if eligible[asset] else 0.0 for asset in ASSETS}
    return Decision(time, weights['BTC'], weights['ETH'], regime,
                    time - timedelta(hours=1), time - timedelta(hours=1),
                    'PREREGISTERED_RESEARCH_INTENT_ONLY')


def position_funding_cash(perp_units: float, mark_price: float, settled_rate: float) -> float:
    """Theoretical position-specific cash flow, not an OKX receipt.

    Positive funding: perp shorts receive; longs pay. Never substitute this
    calculation for a verified actual settled funding journal.
    """
    if not all(isfinite(x) for x in (perp_units, mark_price, settled_rate)):
        raise ValueError('nonfinite funding input')
    finite_positive(mark_price)
    return -perp_units * mark_price * settled_rate


def guard_basis_divergence(spot: float, perp: float) -> bool:
    return abs(finite_positive(perp) / finite_positive(spot) - 1) >= BASIS_EXIT_ABS


def report_permissions():
    return dict(status='PRE_ECONOMIC_SOURCE_GATED', historical_train_economics_run=False,
                validation_opened=False, final_holdout_opened=False,
                settled_funding_authenticated=False, fills_authenticated=False,
                native_fee_tier_authenticated=False, promotion_authorized=False,
                real_orders_enabled=False, paper_publication_authorized=False)
