#!/usr/bin/env python3
"""V98 A3: preregistered diversified sleeve portfolio (NOT an A2 parameter rescue).

Frozen hypothesis before any A3 economic replay: diversified long-only growth,
breakout opportunity, cross-sectional relative-value rebound, and recovery can
compound better than a winner-take-most momentum rotation. No V14/V15/V99 input.
No 2026+ data. Signals use completed bar i; integration must trade next open.
This is a candidate generator, not validation or an approved engine.
"""
import argparse
import csv
import math
from pathlib import Path
from research.v98_independent.v98_phase243_training_reader import load, START_MS
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS
from research.v98_independent.v98_sevenslot_weight_to_targets import FIELDS

def generate(prices, manifest, funding, output):
    output = Path(output)
    if "v98_independent" not in output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    data = load(prices, manifest, funding)
    close = {a: [float(b[3]) for b in data["bars"][a]] for a in ASSETS}
    n = data["hours"]
    state = {a: (0., 0., 0., 0., 1.) for a in ASSETS}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for i in range(n):
            if i >= 720 and i % 168 == 0:
                momentum = {a: close[a][i] / close[a][i-720] - 1 for a in ASSETS}
                weekly = {a: close[a][i] / close[a][i-168] - 1 for a in ASSETS}
                vols = {}
                for a in ASSETS:
                    p = close[a]
                    returns = [math.log(p[j] / p[j-1]) for j in range(i-167, i+1)]
                    vols[a] = math.sqrt(sum(x*x for x in returns) / len(returns))
                # Four separate hypotheses; fixed allocations, no outcome-driven tuning.
                growth = {a for a in ASSETS if momentum[a] > 0}
                opportunity = {a for a in ASSETS if weekly[a] > 0 and close[a][i] >= max(close[a][i-168:i+1])}
                # Relative-value: one weekly laggard, only if long-horizon trend remains positive.
                eligible = [a for a in ASSETS if momentum[a] > 0 and weekly[a] < 0]
                relative = {min(eligible, key=lambda a: (weekly[a], a))} if eligible else set()
                # Recovery: medium-horizon drawdown, positive long-horizon trend.
                recovery = {a for a in ASSETS if momentum[a] > 0 and
                            -0.25 < close[a][i] / max(close[a][i-336:i+1]) - 1 < -0.10}
                state = {}
                for a in ASSETS:
                    g = 0.40 / len(growth) if a in growth else 0.
                    o = 0.15 / len(opportunity) if a in opportunity else 0.
                    r = 0.15 if a in relative else 0.
                    s = 0.10 / len(recovery) if a in recovery else 0.
                    # Regime router uses only the asset's trailing realized volatility.
                    router = 0.5 if vols[a] > 0.035 else 1.
                    state[a] = (g, o, r, s, router)
            gross = sum(sum(state[a][:4]) * state[a][4] for a in ASSETS)
            # Enforce both portfolio gross budget and the preregistered 40% per-asset governor.
            # This is a deterministic feasibility projection, not a post-PnL parameter rescue.
            peak = max(sum(state[a][:4]) * state[a][4] for a in ASSETS)
            allocator = min(1., 0.75 / gross if gross else 1.,
                            0.4 / peak if peak else 1.)
            for a in ASSETS:
                g, o, r, s, router = state[a]
                governor = 0.4
                if (g+o+r+s)*router*allocator > governor + 1e-12:
                    raise ValueError("GOVERNOR_BREACH")
                writer.writerow(dict(zip(FIELDS, (a, START_MS+i*HOUR_MS,
                                                  g, o, r, s, router, allocator, governor))))
    return {"hours": n, "rows": n*len(ASSETS), "status": "A3_UNVALIDATED"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for key in ("prices", "manifest", "funding", "output"):
        parser.add_argument("--"+key, required=True, type=Path)
    args = parser.parse_args()
    print(generate(args.prices, args.manifest, args.funding, args.output))
