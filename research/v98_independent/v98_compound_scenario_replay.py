#!/usr/bin/env python3
"""V98-only causal, scenario-independent equity compounding replay.

Input decisions: {hour_open_ms, decision_time_ms, weights:{asset: signed fraction}}.
Weights are frozen at previous close, applied at current open. No alpha search.
Funding settles on pre-trade inventory; fees on executed turnover.
"""
import math
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS
from research.v98_independent.v98_causal_compound_sizing import size_at_open

END_MS = 1767225600000

def replay(decisions, bars, funding, *, first_hour_ms, initial_equity_usd,
           fee_bps, slippage_bps, multipliers=(1., 2., 3.),
           gross_cap=1., leverage_cap=2.):
    if not decisions or set(bars) != set(ASSETS) or set(funding) != set(ASSETS):
        raise ValueError("INCOMPLETE_CLEAN4_INPUT")
    if not (math.isfinite(initial_equity_usd) and initial_equity_usd > 0):
        raise ValueError("INVALID_EQUITY")
    if any(not math.isfinite(x) or x < 0 for x in (fee_bps, slippage_bps)):
        raise ValueError("INVALID_COST")
    if not multipliers or any(not math.isfinite(x) or x < 0 for x in multipliers):
        raise ValueError("INVALID_SCENARIO")
    if first_hour_ms % HOUR_MS or first_hour_ms < 1669852800000:
        raise ValueError("INVALID_START")
    if first_hour_ms + len(decisions)*HOUR_MS > END_MS:
        raise ValueError("TRAINING_BOUNDARY")
    if any(len(bars[a]) != len(decisions) for a in ASSETS):
        raise ValueError("INCOMPLETE_BAR_GRID")
    states = {str(m): {"equity": float(initial_equity_usd),
                       "units": {a: 0. for a in ASSETS},
                       "previous_closes": None, "ledger": []} for m in multipliers}
    if len(states) != len(multipliers):
        raise ValueError("DUPLICATE_SCENARIO")
    for i, decision in enumerate(decisions):
        t = first_hour_ms + i*HOUR_MS
        if int(decision["hour_open_ms"]) != t or int(decision["decision_time_ms"]) > t-HOUR_MS:
            raise ValueError("NONCAUSAL_OR_MISSING_DECISION")
        weights = decision["weights"]
        if set(weights) != set(ASSETS):
            raise ValueError("INCOMPLETE_WEIGHT_GRID")
        opens, closes = {}, {}
        for a in ASSETS:
            bar = bars[a][i]
            op, cl = float(bar[0]), float(bar[3])
            if not all(math.isfinite(x) and x > 0 for x in (op, cl)):
                raise ValueError("INVALID_PRICE")
            opens[a], closes[a] = op, cl
        rates = {a: float(funding[a].get(t, 0.)) for a in ASSETS}
        for key, state in states.items():
            previous_closes = state["previous_closes"] or opens
            sizing = size_at_open(weights, state["units"], opens, previous_closes,
                                  rates, state["equity"], gross_cap=gross_cap,
                                  max_leverage=leverage_cap)
            available = sizing["available_equity_usd"]
            target = sizing["target_notional_usd"]
            pre = sizing["pre_trade_notional_usd"]
            turnover = sum(abs(target[a]-pre[a]) for a in ASSETS)
            cost = turnover*(fee_bps+slippage_bps)*float(key)/10000.
            entry_equity = available-cost
            if entry_equity <= 0:
                raise ValueError("INSOLVENT_AT_ENTRY")
            if sum(abs(x) for x in target.values()) > leverage_cap*entry_equity + 1e-8:
                raise ValueError("ENTRY_LEVERAGE_BREACH")
            intrabar = sum(target[a]*(closes[a]/opens[a]-1.) for a in ASSETS)
            ending = entry_equity + intrabar
            if not math.isfinite(ending) or ending <= 0:
                raise ValueError("INSOLVENT_AT_CLOSE")
            units = {a: target[a]/opens[a] for a in ASSETS}
            if sum(abs(units[a]*closes[a]) for a in ASSETS) > leverage_cap*ending + 1e-8:
                raise ValueError("CLOSING_LEVERAGE_BREACH")
            state["ledger"].append({"hour_open_ms": t, "starting_equity_usd": state["equity"],
                                    "gap_pnl_usd": sizing["gap_pnl_usd"],
                                    "funding_cashflow_usd": sizing["funding_cashflow_usd"],
                                    "intrabar_pnl_usd": intrabar, "execution_cost_usd": cost,
                                    "turnover_usd": turnover, "ending_equity_usd": ending})
            state["equity"], state["units"], state["previous_closes"] = ending, units, closes
    return {key: state["ledger"] for key, state in states.items()}
