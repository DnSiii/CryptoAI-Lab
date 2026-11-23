"""C27 split-vs-full historical continuation gate; Clean-4 training only.

A split at an interior training open carries the complete two-clock state.
No 2026 data, holdout, or external engine is loaded. This is a regression
against the existing full-history implementation, not independent validation.
"""
import argparse
import json
import math
from pathlib import Path
from .phase243_native_funding_cashflow import ASSETS, HOUR_MS
from .v98_phase243_training_reader import load, START_MS
from .v98_composed_c26 import c26_model, c26_allocator, WARMUP
from .v98_c27_authenticated_runner import replay, ASSET_BUFFER, GROSS_BUFFER
from .v98_c27_two_clock_governor import planned_trim, execute_queued_units
from .v98_b0_causal_overlay import governor_multiplier

SPLIT = 12000  # fixed before looking at any split result; 2024 training only

def resumed_suffix(bars, funding, scale, prefix, split=SPLIT):
    if split <= WARMUP + 1 or split >= 27048 or len(prefix) != split - 1:
        raise ValueError("C27_SPLIT_CLOCK")
    last = prefix[-1]
    if last["index"] != split - 1:
        raise ValueError("C27_SPLIT_LEDGER_INDEX")
    equity = float(last["equity"])
    peak = max([10000.] + [max(r["equity"], r["pre_fill_equity"]) for r in prefix])
    weights = dict(last["weights_after_fill"])
    queued = dict(last["queued_next_open_sell_fractions"])
    histories = {a: [bars[a][j][3] for j in range(split)] for a in ASSETS}
    decision_equity, decision_peak = equity, peak
    model, router = c26_model()
    result = []
    for i in range(split, 27048):
        previous = dict(weights)
        returns = {a: bars[a][i][0] / bars[a][i-1][0] - 1 for a in ASSETS}
        gross_by_asset = {a: previous[a] * returns[a] for a in ASSETS}
        funding_by_asset = {a: -previous[a] * funding[a].get(i, 0.) for a in ASSETS}
        gross = sum(gross_by_asset.values())
        carry = sum(funding_by_asset.values())
        factor = 1 + gross + carry
        if factor <= 0 or not math.isfinite(factor):
            raise ValueError("C27_SPLIT_INSOLVENT_MARK")
        equity *= factor
        weights = {a: previous[a] * (1 + returns[a]) / factor for a in ASSETS}
        marked = dict(weights)
        post_queue = execute_queued_units(marked, queued)
        strategic = i >= WARMUP + 1 and (i - (WARMUP + 1)) % 168 == 0
        if strategic:
            history = {a: tuple(histories[a]) for a in ASSETS}
            cached = model(history)
            router_value = router(history["BTCUSDT"])
            routers = {a: router_value for a in ASSETS}
            target = c26_allocator(cached, routers, governor_multiplier(decision_equity, decision_peak))
            target = {a: max(0., min(float(target[a]), ASSET_BUFFER)) for a in ASSETS}
            total = sum(target.values())
            if total > GROSS_BUFFER:
                target = {a: target[a] * GROSS_BUFFER / total for a in ASSETS}
            order_type = "strategic"
        else:
            target = post_queue
            order_type = "safety" if any(queued.values()) else "hold"
        turnover = sum(abs(target[a] - marked[a]) for a in ASSETS)
        cost = turnover * .0006 * scale
        if cost >= 1 or not math.isfinite(cost):
            raise ValueError("C27_SPLIT_INSOLVENT_COST")
        before_cost = equity
        peak = max(peak, before_cost)
        equity *= 1 - cost
        weights = dict(target)
        peak = max(peak, equity)
        buffered = planned_trim(weights, asset_cap=ASSET_BUFFER, gross_cap=GROSS_BUFFER)
        queued = {a: 0. if weights[a] <= 1e-12 else max(0., min(1., 1 - buffered[a] / weights[a]))
                  for a in ASSETS}
        result.append(dict(index=i, equity=equity, pre_fill_equity=before_cost,
            weights_before_fill=marked, weights_after_fill=dict(weights),
            turnover=turnover, cost_return=cost, drawdown=1-equity/peak,
            gross_return=gross, funding_return=carry, gross_by_asset=gross_by_asset,
            funding_by_asset=funding_by_asset, order_type=order_type,
            queued_next_open_sell_fractions=dict(queued),
            hard_cap_breach_after_fill=(max(weights.values()) > .40+1e-10 or
                                        sum(weights.values()) > .90+1e-10)))
        decision_equity, decision_peak = equity, peak
        for a in ASSETS:
            histories[a].append(bars[a][i][3])
    return result

def audit(prices, manifest, funding_path):
    data = load(prices, manifest, funding_path)
    if data["hours"] != 27048:
        raise ValueError("C27_SPLIT_INCOMPLETE_HISTORY")
    indexed = {a: {} for a in ASSETS}
    for a in ASSETS:
        for stamp, rate in data["funding"][a].items():
            offset = stamp - START_MS
            if offset % HOUR_MS or not 0 <= offset < 27048 * HOUR_MS:
                raise ValueError("C27_SPLIT_FUNDING_STAMP")
            indexed[a][offset // HOUR_MS] = rate
    verdict = {}
    for scale in (1., 2., 4.):
        _, full = replay(data["bars"], indexed, scale)
        resumed = resumed_suffix(data["bars"], indexed, scale, full[:SPLIT-1])
        expected = full[SPLIT-1:]
        if len(resumed) != len(expected):
            raise ValueError("C27_SPLIT_LENGTH")
        for j, (actual, reference) in enumerate(zip(resumed, expected)):
            if actual != reference:
                fields = [k for k in reference if actual.get(k) != reference[k]]
                raise ValueError(f"C27_SPLIT_DIVERGENCE scale={scale} index={SPLIT+j} fields={fields}")
        verdict[f"{int(scale)}x"] = {"split_index": SPLIT, "compared_hours": len(expected),
                                     "status": "BYTE_EQUAL_ECONOMIC_ROWS_TRAINING_ONLY"}
    return verdict

def main():
    p = argparse.ArgumentParser()
    for name in ("prices", "manifest", "funding", "output"):
        p.add_argument("--"+name, required=True, type=Path)
    args = p.parse_args()
    if "v98_independent" not in args.output.resolve().parts:
        raise ValueError("C27_SPLIT_NAMESPACE")
    verdict = audit(args.prices, args.manifest, args.funding)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(verdict, sort_keys=True, indent=2)+"\\n")
    print("C27_SPLIT_CONTINUATION_TRAINING_ONLY", json.dumps(verdict, sort_keys=True))

if __name__ == "__main__":
    main()
