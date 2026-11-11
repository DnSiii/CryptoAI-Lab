"""Causal B0 portfolio integration, synthetic-testable; NOT a validated PnL.

A row represents one COMPLETED hourly candle with native funding booked at
that timestamp. Sleeves must be supplied as pre-registered, deterministic
functions of completed closes only. No 2026+ training data is accepted.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from .v98_b0_hourly_ledger import LedgerState, transition
from .v98_b0_causal_overlay import regime_multiplier, governor_multiplier, compose_weights

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
CUTOFF = datetime(2026, 1, 1, tzinfo=timezone.utc)

@dataclass(frozen=True)
class HourBar:
    timestamp: datetime
    closes: dict
    funding: dict

def replay_b0(rows, sleeve_fn, *, initial_equity=10000.0,
              fee_rate=0.0004, slippage_rate=0.0002,
              cost_scale=1.0):
    """Return state and audited hourly entries; no signals from future bars.

    At close t: mark prior weights through t, compute next target using
    completed closes through t and equity from t-1 (conservative causal lag),
    then pay rebalance costs at close t. The new target earns bar t+1.
    """
    if initial_equity <= 0 or cost_scale < 0:
        raise ValueError("INVALID_INITIAL_STATE")
    state = LedgerState(initial_equity, initial_equity, dict.fromkeys(ASSETS, 0.0))
    histories = {asset: [] for asset in ASSETS}
    previous = None
    previous_timestamp = None
    entries = []
    for bar in rows:
        if bar.timestamp.tzinfo is None or bar.timestamp.utcoffset() is None:
            raise ValueError("NAIVE_TIMESTAMP")
        instant = bar.timestamp.astimezone(timezone.utc)
        if instant >= CUTOFF:
            raise ValueError("TRAINING_CUTOFF_2026")
        if previous_timestamp is not None and (instant - previous_timestamp).total_seconds() != 3600:
            raise ValueError("NONCONTIGUOUS_HOURLY_GRID")
        if set(bar.closes) != set(ASSETS) or set(bar.funding) != set(ASSETS):
            raise ValueError("CLEAN4_GRID_REQUIRED")
        if any(not (0 < float(bar.closes[a]) < float("inf")) for a in ASSETS):
            raise ValueError("INVALID_CLOSE")
        for asset in ASSETS:
            histories[asset].append(float(bar.closes[asset]))
        if previous is not None:
            returns = {a: bar.closes[a] / previous[a] - 1 for a in ASSETS}
            sleeves = sleeve_fn({a: tuple(histories[a]) for a in ASSETS})
            routers = {a: regime_multiplier(histories[a]) for a in ASSETS}
            governor = governor_multiplier(state.equity, state.peak)
            targets = compose_weights(sleeves, routers, governor)
            state, audit = transition(state, returns, bar.funding, targets,
                                      fee_rate=fee_rate*cost_scale,
                                      slippage_rate=slippage_rate*cost_scale)
            entries.append({"timestamp": instant.isoformat(), **audit,
                            "router": routers, "governor": governor,
                            "weights": dict(state.weights)})
        previous = dict(bar.closes)
        previous_timestamp = instant
    return state, entries
