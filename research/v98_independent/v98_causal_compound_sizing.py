#!/usr/bin/env python3
"""V98-only causal equity-sized target calculator (no historical performance claim).

The weight is decided at the PREVIOUS candle close. Sizing uses equity available
at the current open after gap PnL and native funding, but before execution fees.
No future close or future funding enters the decision.
"""
import math


def size_at_open(weights, previous_units, opens, previous_closes, funding_rates,
                 previous_equity, *, gross_cap=1.0, max_leverage=2.0):
    assets = tuple(sorted(weights))
    if not assets or any(set(x) != set(assets) for x in
                         (previous_units, opens, previous_closes, funding_rates)):
        raise ValueError("INCOMPLETE_ASSET_GRID")
    numbers = [previous_equity, gross_cap, max_leverage]
    for mapping in (weights, previous_units, opens, previous_closes, funding_rates):
        numbers.extend(mapping.values())
    if not all(math.isfinite(float(x)) for x in numbers):
        raise ValueError("NONFINITE_INPUT")
    if previous_equity <= 0 or not 0 < gross_cap <= max_leverage:
        raise ValueError("INVALID_EQUITY_OR_CAP")
    if any(opens[a] <= 0 or previous_closes[a] <= 0 for a in assets):
        raise ValueError("INVALID_PRICE")
    if sum(abs(weights[a]) for a in assets) > gross_cap + 1e-12:
        raise ValueError("GROSS_CAP_BREACH")
    # Units survive the overnight gap. Funding settles on inventory held before
    # the rebalance; each cost scenario must call this with its own equity/units.
    pre = {a: previous_units[a] * opens[a] for a in assets}
    gap = sum(previous_units[a] * (opens[a] - previous_closes[a]) for a in assets)
    funding = -sum(pre[a] * funding_rates[a] for a in assets)
    available = previous_equity + gap + funding
    if not math.isfinite(available) or available <= 0:
        raise ValueError("INSOLVENT_BEFORE_EXECUTION")
    targets = {a: weights[a] * available for a in assets}
    if sum(abs(v) for v in targets.values()) > max_leverage * available + 1e-8:
        raise ValueError("LEVERAGE_BREACH")
    return {"available_equity_usd": available, "gap_pnl_usd": gap,
            "funding_cashflow_usd": funding, "pre_trade_notional_usd": pre,
            "target_notional_usd": targets}
