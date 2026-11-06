#!/usr/bin/env python3
"""V98-only hourly portfolio accounting. No alpha selection or performance claim.

Input rows are a complete four-asset hourly grid. Each row records the close
price and target signed USD notional decided using information available at
the PRIOR hour boundary. Execution at current open is deliberately not inferred
from close prices: callers must provide executable fill_price explicitly.
Funding is settled on PRE-trade inventory, never on the newly targeted position.
"""
import csv
import math
from collections import defaultdict
from phase243_native_funding_cashflow import ASSETS, HOUR_MS, validate_complete_inventory

def account(rows, funding, *, initial_equity_usd, taker_fee_bps, slippage_bps,
            cost_multiplier=1.0, max_gross_leverage=2.0):
    if not rows or not math.isfinite(initial_equity_usd) or initial_equity_usd <= 0:
        raise ValueError("INVALID_INITIAL_EQUITY")
    if any(not math.isfinite(x) or x < 0 for x in (taker_fee_bps, slippage_bps, cost_multiplier)):
        raise ValueError("INVALID_COST")
    if not math.isfinite(max_gross_leverage) or max_gross_leverage <= 0:
        raise ValueError("INVALID_LEVERAGE_CAP")
    grouped = defaultdict(dict)
    for r in rows:
        a, t = r["asset"], int(r["hour_open_ms"])
        if a not in ASSETS or t % HOUR_MS or a in grouped[t]:
            raise ValueError("INVALID_OR_DUPLICATE_ASSET_HOUR")
        grouped[t][a] = r
    hours = sorted(grouped)
    if hours[-1] >= 1767225600000:
        raise ValueError("TRAINING_BOUNDARY_VIOLATION")
    if any(b-a != HOUR_MS for a,b in zip(hours,hours[1:])):
        raise ValueError("MISSING_PORTFOLIO_HOUR")
    if any(set(grouped[t]) != set(ASSETS) for t in hours):
        raise ValueError("INCOMPLETE_CLEAN4_INVENTORY")
    inventory = []
    for t in hours:
        for a in ASSETS:
            r = grouped[t][a]
            n = float(r["pre_trade_notional_usd"])
            if not math.isfinite(n):
                raise ValueError("INVALID_NOTIONAL")
            inventory.append({"asset":a,"hour_open_ms":t,"signed_notional_usd_before_hour":n})
    validate_complete_inventory(inventory, funding)
    equity = initial_equity_usd
    previous = {a: 0.0 for a in ASSETS}
    previous_close = {}
    ledger = []
    for t in hours:
        pnl, cash, fees, traded, gross = 0., 0., 0., 0., 0.
        next_positions = {}
        for a in ASSETS:
            r = grouped[t][a]
            pre = float(r["pre_trade_notional_usd"])
            target = float(r["target_notional_usd"])
            close = float(r["close_price"])
            fill = float(r["fill_price"])
            if any(not math.isfinite(v) for v in (pre,target,close,fill)) or close <= 0 or fill <= 0:
                raise ValueError("INVALID_EXECUTION_DATA")
            if abs(pre - previous[a]) > 1e-7 * max(1,abs(pre),abs(previous[a])):
                raise ValueError("PRE_TRADE_INVENTORY_MISMATCH")
            # Pre-trade inventory earns price movement from prior close to current fill.
            if a in previous_close:
                pnl += pre * (fill / previous_close[a] - 1)
            elif pre:
                raise ValueError("NONZERO_UNFUNDED_INITIAL_INVENTORY")
            cash -= pre * funding[a].get(t,0.0)
            delta = target - pre
            traded += abs(delta)
            fees += abs(delta) * (taker_fee_bps + slippage_bps) / 10000 * cost_multiplier
            # Target inventory then earns current fill-to-close price movement.
            pnl += target * (close / fill - 1)
            gross += abs(target)
            next_positions[a] = target * close / fill
            previous_close[a] = close
        ending = equity + pnl + cash - fees
        if ending <= 0 or not math.isfinite(ending):
            raise ValueError("PORTFOLIO_INSOLVENT")
        if gross > max_gross_leverage * equity + 1e-8:
            raise ValueError("GROSS_LEVERAGE_LIMIT")
        ledger.append({"hour_open_ms":t,"starting_equity_usd":equity,
                       "price_pnl_usd":pnl,"funding_cashflow_usd":cash,
                       "execution_cost_usd":fees,"turnover_usd":traded,
                       "ending_equity_usd":ending})
        equity = ending
        previous = next_positions
    return ledger

def write_ledger(path, ledger):
    with open(path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=ledger[0].keys())
        w.writeheader()
        w.writerows(ledger)
