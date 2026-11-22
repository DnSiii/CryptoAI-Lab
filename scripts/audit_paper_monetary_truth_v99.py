#!/usr/bin/env python3
"""Read-only, fail-closed forensic classification of published V13 order values.

Never modifies ledger, never derives missing historical raw notionals.
Run: python scripts/audit_paper_monetary_truth_v99.py [ledger.json] [output.json]
"""
from __future__ import annotations
import hashlib
import json
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
    duplicate_keys = []
    for decision_index, decision in enumerate(ledger.get("decisions", [])):
        timestamp = decision.get("timestamp")
        for adjustment_index, row in enumerate(decision.get("adjustments", [])):
            key = (timestamp, row.get("symbol"))
            if key in seen:
                duplicate_keys.append({"decision_index": decision_index, "adjustment_index": adjustment_index, "timestamp": timestamp, "symbol": row.get("symbol")})
            else:
                seen.add(key)
            category = classify(row)
            counts[category] += 1
            if len(examples.get(category, [])) < 8:
                row_canonical = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
                row_sha256 = hashlib.sha256(row_canonical.encode("utf-8")).hexdigest()
                examples.setdefault(category, []).append({
                    "decision_index": decision_index, "adjustment_index": adjustment_index,
                    "row_sha256": row_sha256,
                    "timestamp": timestamp, "symbol": row.get("symbol"),
                    "display": row.get("order_value_brl"),
                    "raw": row.get("order_value_brl_unrounded"),
                })
    return {"total": sum(counts.values()), "counts": dict(sorted(counts.items())),
            "evidence_identity": "sha256 of canonical original adjustment JSON; never a reconstructed trade",
            "examples": examples, "duplicate_order_key_count": len(duplicate_keys),
            "duplicate_order_key_examples": duplicate_keys[:8], "read_only": True,
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
    # A duplicate identity must never hide an invalid monetary amount.
    sample = {"decisions": [{"timestamp": "2026-01-01", "adjustments": [
        {"symbol": "BTCUSDT", "order_value_brl": 0, "order_value_brl_unrounded": 0.004},
        {"symbol": "BTCUSDT", "order_value_brl": 0, "order_value_brl_unrounded": 0.006}]}]}
    duplicate_report = audit(sample)
    assert duplicate_report["counts"] == {"inconsistent_zero": 1, "legitimate_subcent": 1}
    assert duplicate_report["duplicate_order_key_count"] == 1
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
