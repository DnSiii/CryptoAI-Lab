#!/usr/bin/env python3
"""V98-only authenticated Clean-4 seven-slot -> causal compound replay.

Transport/integration only: no strategy approval, optimization, or holdout.
A slot recorded for hour h is executed at the OPEN of hour h+1.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS
from research.v98_independent.v98_phase243_training_reader import load, START_MS, EXPECTED_HOURS
from research.v98_independent.v98_sevenslot_weight_to_targets import FIELDS, SLEEVES
from research.v98_independent.v98_compound_scenario_replay import replay


def run(slots, prices, price_manifest, funding, output, *, capital, fee_bps,
        slippage_bps, gross_cap=1., leverage_cap=2., multipliers=(1., 2., 4.)):
    paths = (slots, prices, price_manifest, funding, output)
    if any("v98_independent" not in Path(p).absolute().parts for p in paths):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    if not 0 < gross_cap <= leverage_cap or not all(
        math.isfinite(x) for x in (capital, fee_bps, slippage_bps, gross_cap, leverage_cap)
    ) or capital <= 0 or min(fee_bps, slippage_bps) < 0:
        raise ValueError("INVALID_ECONOMICS")
    data = load(prices, price_manifest, funding)
    weights = {}
    with Path(slots).open(newline="") as f:
        reader = csv.DictReader(f)
        if set(reader.fieldnames or ()) != set(FIELDS):
            raise ValueError("INVALID_SEVEN_SLOT_SCHEMA")
        for row in reader:
            asset = row["asset"]
            t = int(row["hour_open_ms"])
            if asset not in ASSETS or t < START_MS or t >= START_MS + EXPECTED_HOURS*HOUR_MS or t % HOUR_MS:
                raise ValueError("INVALID_ASSET_OR_TIME")
            if (t, asset) in weights:
                raise ValueError("DUPLICATE_SLOT")
            v = {k: float(row[k]) for k in FIELDS[2:]}
            if not all(math.isfinite(x) for x in v.values()):
                raise ValueError("NONFINITE_SLOT")
            if any(not 0 <= v[k] <= 1 for k in ("regime_router", "dynamic_allocator", "risk_governor")):
                raise ValueError("INVALID_CONTROL")
            raw = sum(v[k] for k in SLEEVES)
            if abs(raw) > 2 + 1e-12:
                raise ValueError("UNBOUNDED_SLEEVES")
            w = raw * v["regime_router"] * v["dynamic_allocator"]
            if abs(w) > v["risk_governor"] + 1e-12:
                raise ValueError("GOVERNOR_BREACH")
            weights[t, asset] = w
    if len(weights) != EXPECTED_HOURS*len(ASSETS):
        raise ValueError("INCOMPLETE_FULL_HISTORY_SLOTS")
    decisions = []
    for i in range(EXPECTED_HOURS):
        t = START_MS + i*HOUR_MS
        # No warmup trade: first hour has no prior close decision.
        w = {a: (weights[t-HOUR_MS, a] if i else 0.) for a in ASSETS}
        if sum(abs(x) for x in w.values()) > gross_cap + 1e-12:
            raise ValueError("GROSS_CAP_BREACH")
        decisions.append({"hour_open_ms": t, "decision_time_ms": t-HOUR_MS,
                          "weights": w})
    ledgers = replay(decisions, data["bars"], data["funding"],
                     first_hour_ms=START_MS, initial_equity_usd=capital,
                     fee_bps=fee_bps, slippage_bps=slippage_bps,
                     multipliers=multipliers, gross_cap=gross_cap,
                     leverage_cap=leverage_cap)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    metrics = {}
    for scenario, ledger in ledgers.items():
        if len(ledger) != EXPECTED_HOURS:
            raise ValueError("INCOMPLETE_REPLAY")
        path = output / ("compound_ledger_" + scenario + ".json")
        path.write_text(json.dumps(ledger, separators=(",", ":")) + "\n")
        metrics[scenario] = {"hours": len(ledger),
                             "final_equity_usd": ledger[-1]["ending_equity_usd"],
                             "total_cost_usd": sum(x["execution_cost_usd"] for x in ledger),
                             "ledger_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    summary = {"status": "ECONOMIC_REPLAY_ONLY_NOT_VALIDATED_ENGINE",
               "holdout_accessed": False, "source": "AUTHENTICATED_CLEAN4",
               "price_manifest_sha256": data["price_manifest_sha256"],
               "funding_manifest_sha256": data["funding_manifest_sha256"],
               "slots_sha256": hashlib.sha256(Path(slots).read_bytes()).hexdigest(),
               "execution": "PREVIOUS_HOUR_DECISION_NEXT_OPEN",
               "scenarios": metrics}
    (output / "compound_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True)+"\n")
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for name in ("slots", "prices", "price-manifest", "funding", "output"):
        p.add_argument("--"+name, required=True, type=Path)
    for name in ("capital", "fee-bps", "slippage-bps"):
        p.add_argument("--"+name, required=True, type=float)
    p.add_argument("--gross-cap", type=float, default=1.)
    p.add_argument("--leverage-cap", type=float, default=2.)
    a = p.parse_args()
    print(json.dumps(run(a.slots, a.prices, a.price_manifest, a.funding,
                         a.output, capital=a.capital, fee_bps=a.fee_bps,
                         slippage_bps=a.slippage_bps, gross_cap=a.gross_cap,
                         leverage_cap=a.leverage_cap), sort_keys=True))
