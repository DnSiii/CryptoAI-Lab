"""Independent arithmetic reconciliation of V98 B0 execution ledgers.

This checks accounting identities without importing the execution engine.
It is not a strategy-validation or promotion gate.
"""
import argparse
import json
import math
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")

def reconcile(entries, summary, initial_equity=10000., tolerance=1e-9):
    if not entries or summary["hours"] != len(entries) + 1:
        raise ValueError("INCOMPLETE_LEDGER")
    previous = float(initial_equity)
    max_residual = 0.
    for i, entry in enumerate(entries, 1):
        if entry["index"] != i:
            raise ValueError("NONCONTIGUOUS_LEDGER")
        values = [entry[k] for k in ("equity", "pre_fill_equity", "turnover",
                                    "cost_return", "gross_return", "funding_return", "drawdown")]
        if not all(isinstance(v, (float, int)) and math.isfinite(v) for v in values):
            raise ValueError("NONFINITE_LEDGER")
        before = entry["weights_before_fill"]
        after = entry["weights_after_fill"]
        if set(before) != set(ASSETS) or set(after) != set(ASSETS):
            raise ValueError("INVALID_ASSETS")
        if not all(math.isfinite(v) for v in list(before.values()) + list(after.values())):
            raise ValueError("NONFINITE_WEIGHTS")
        expected_pre = previous * (1 + entry["gross_return"] + entry["funding_return"])
        expected_post = entry["pre_fill_equity"] * (1 - entry["cost_return"])
        expected_turnover = sum(abs(after[a] - before[a]) for a in ASSETS)
        if entry["cost_return"] < 0 or entry["cost_return"] >= 1 or entry["equity"] <= 0:
            raise ValueError("INVALID_ACCOUNT")
        for actual, expected in ((entry["pre_fill_equity"], expected_pre),
                                 (entry["equity"], expected_post),
                                 (entry["turnover"], expected_turnover)):
            residual = abs(actual - expected) / max(1., abs(expected))
            max_residual = max(max_residual, residual)
            if residual > tolerance:
                raise ValueError("LEDGER_RECONCILIATION_FAILED")
        previous = entry["equity"]
    final = summary["final_equity"]
    if not math.isfinite(final) or final <= 0:
        raise ValueError("INVALID_FINAL_EQUITY")
    return {"status": "ARITHMETIC_RECONCILED_NOT_STRATEGY_VALIDATED",
            "observations": len(entries), "max_relative_residual": max_residual,
            "last_fill_equity": previous, "final_close_equity": final,
            "final_mark_return": final / previous - 1}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--directory", type=Path, required=True)
    a = p.parse_args()
    if "v98_independent" not in a.directory.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    summary = json.loads((a.directory / "b0_next_open_summary.json").read_text())
    result = {}
    for scenario in ("1x", "2x", "4x"):
        with (a.directory / f"b0_next_open_summary_{scenario}_ledger.jsonl").open() as f:
            entries = [json.loads(line) for line in f]
        result[scenario] = reconcile(entries, summary["results"][scenario])
    (a.directory / "b0_independent_arithmetic_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
