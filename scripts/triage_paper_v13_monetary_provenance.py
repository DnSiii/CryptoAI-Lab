#!/usr/bin/env python3
"""Read-only monetary provenance triage for an existing V13 paper ledger.

Never repairs, overwrites, synthesizes or promotes historical orders.
Usage: python scripts/triage_paper_v13_monetary_provenance.py reports/paper_v13_ledger.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
import hashlib
import json
from pathlib import Path

CENT = Decimal("0.01")
HALF_CENT = Decimal("0.005")


def classify(row: dict) -> tuple[str, str | None]:
    try:
        displayed = Decimal(str(row["order_value_brl"]))
    except (KeyError, InvalidOperation, ValueError, TypeError):
        return "invalid_display", None
    if not displayed.is_finite() or displayed < 0:
        return "invalid_display", None
    raw = row.get("order_value_brl_unrounded")
    if raw is None:
        return ("missing_raw_positive" if displayed > 0 else "zero_missing_raw"), None
    try:
        precise = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        return "invalid_raw", None
    if not precise.is_finite() or precise <= 0:
        return "invalid_raw", None
    rounded = precise.quantize(CENT, rounding=ROUND_HALF_EVEN)
    if displayed == 0:
        if 0 < precise < HALF_CENT and rounded == 0:
            return "legitimate_subcent", None
        return "invalid_zero", None
    if rounded == displayed:
        return "reconciled", None
    ratio = displayed / precise
    return "raw_display_mismatch", str(ratio.quantize(Decimal("0.000001")))


def audit(data: dict) -> dict:
    counts = Counter()
    ratios = Counter()
    examples = {}
    duplicates = 0
    seen = set()
    for event in data.get("decisions", []):
        timestamp = event.get("timestamp")
        for row in event.get("adjustments", []):
            key = (timestamp, row.get("symbol"))
            if key in seen:
                duplicates += 1
            seen.add(key)
            status, ratio = classify(row)
            counts[status] += 1
            if ratio:
                ratios[ratio] += 1
            if status not in examples:
                examples[status] = {
                    "timestamp": timestamp, "symbol": row.get("symbol"),
                    "display": row.get("order_value_brl"),
                    "raw": row.get("order_value_brl_unrounded"),
                }
    return {
        "decisions": len(data.get("decisions", [])),
        "adjustments": sum(counts.values()),
        "duplicate_timestamp_symbol": duplicates,
        "classes": dict(sorted(counts.items())),
        "mismatch_ratio_top10": ratios.most_common(10),
        "first_example_per_class": examples,
        "status": "BLOCKED" if duplicates or any(counts[k] for k in (
            "invalid_display", "invalid_raw", "zero_missing_raw", "invalid_zero",
            "raw_display_mismatch", "missing_raw_positive")) else "RECONCILED",
        "caveat": "Missing historical raw precision cannot be reconstructed or certified from displayed cents.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    raw = args.ledger.read_bytes()
    report = audit(json.loads(raw))
    report["ledger_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "RECONCILED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
