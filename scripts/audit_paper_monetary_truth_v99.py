#!/usr/bin/env python3
"""Read-only, fail-closed forensic classification of published V13 order values.

Never modifies ledger, never derives missing historical raw notionals.
Run: python scripts/audit_paper_monetary_truth_v99.py [ledger.json] [output.json]
"""
from __future__ import annotations
import json
import math
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path

CENT = Decimal("0.01")
HALF_CENT = Decimal("0.005")

def number(value):
    if isinstance(value, bool) or value is None:
        raise ValueError("missing/non-numeric")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("non-numeric") from exc
    if not d.is_finite():
        raise ValueError("non-finite")
    return d

def classify(row):
    try:
        displayed = number(row["order_value_brl"])
    except (KeyError, ValueError):
        return "invalid_display"
    if displayed < 0 or displayed != displayed.quantize(CENT):
        return "invalid_display"
    raw_field = row.get("order_value_brl_unrounded")
    if raw_field is None:
        return "missing_raw_zero_display" if displayed == 0 else "missing_raw_positive_display"
    try:
        raw = number(raw_field)
    except ValueError:
        return "invalid_raw"
    if raw <= 0:
        return "invalid_raw"
    if displayed == 0:
        if raw < HALF_CENT and raw.quantize(CENT, rounding=ROUND_HALF_EVEN) == 0:
            return "legitimate_subcent"
        return "inconsistent_zero"
    if raw.quantize(CENT, rounding=ROUND_HALF_EVEN) != displayed:
        return "inconsistent_positive"
    return "reconciled_positive"

def audit(ledger):
    counts = Counter()
    examples = {}
    seen = set()
    for decision in ledger.get("decisions", []):
        timestamp = decision.get("timestamp")
        for row in decision.get("adjustments", []):
            key = (timestamp, row.get("symbol"))
            if key in seen:
                category = "duplicate_order_key"
            else:
                seen.add(key)
                category = classify(row)
            counts[category] += 1
            if len(examples.get(category, [])) < 8:
                examples.setdefault(category, []).append({
                    "timestamp": timestamp, "symbol": row.get("symbol"),
                    "display": row.get("order_value_brl"),
                    "raw": row.get("order_value_brl_unrounded"),
                })
    return {"total": sum(counts.values()), "counts": dict(sorted(counts.items())),
            "examples": examples, "read_only": True,
            "historical_values_reconstructed": False}

def self_test():
    cases = [
        ({"order_value_brl": 0, "order_value_brl_unrounded": 0.004}, "legitimate_subcent"),
        ({"order_value_brl": 0, "order_value_brl_unrounded": 0.006}, "inconsistent_zero"),
        ({"order_value_brl": 0}, "missing_raw_zero_display"),
        ({"order_value_brl": 0.01, "order_value_brl_unrounded": 0.014}, "reconciled_positive"),
        ({"order_value_brl": 0.01, "order_value_brl_unrounded": 0.019}, "inconsistent_positive"),
        ({"order_value_brl": 0, "order_value_brl_unrounded": float("nan")}, "invalid_raw"),
        ({"order_value_brl": 0, "order_value_brl_unrounded": -0.001}, "invalid_raw"),
        ({"order_value_brl": float("inf")}, "invalid_display"),
        ({"order_value_brl": 0.005, "order_value_brl_unrounded": 0.005}, "invalid_display"),
    ]
    for row, expected in cases:
        actual = classify(row)
        assert actual == expected, (row, actual, expected)

if __name__ == "__main__":
    self_test()
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reports/paper_v13_ledger.json")
    report = audit(json.loads(path.read_text(encoding="utf-8")))
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(output, encoding="utf-8")
    print(output)
