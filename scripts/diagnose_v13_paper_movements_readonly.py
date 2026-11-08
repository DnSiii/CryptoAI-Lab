#!/usr/bin/env python3
"""Read-only V13 paper movement forensics. No ledger mutation or trade creation."""
import argparse
import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path

def classify(adjustment):
    try:
        delta = Decimal(str(adjustment["new_weight"])) - Decimal(str(adjustment["previous_weight"]))
        shown = Decimal(str(adjustment["order_value_brl"]))
        raw_value = adjustment.get("order_value_brl_unrounded")
        raw = Decimal(str(raw_value)) if raw_value is not None else None
        if not delta.is_finite() or not shown.is_finite() or (raw is not None and not raw.is_finite()):
            return "INCONSISTENT_NONFINITE"
        if delta == 0:
            return "INCONSISTENT_ZERO_DELTA"
        if adjustment.get("order_side") != ("buy" if delta > 0 else "sell"):
            return "INCONSISTENT_SIDE"
        if shown > 0:
            return "POSITIVE_DISPLAYED_VALUE"
        if shown == 0 and raw is not None and Decimal(0) < raw < Decimal("0.005") and round(raw, 2) == shown:
            return "LEGITIMATE_SUBCENT_DISPLAY"
        return "INCONSISTENT_ZERO_OR_NEGATIVE_VALUE"
    except (KeyError, InvalidOperation, ValueError, TypeError):
        return "INCONSISTENT_MALFORMED"

def inspect(path):
    ledger = json.loads(Path(path).read_text(encoding="utf-8"))
    records = []
    for di, decision in enumerate(ledger.get("decisions", [])):
        for ai, adjustment in enumerate(decision.get("adjustments", [])):
            status = classify(adjustment)
            if status != "POSITIVE_DISPLAYED_VALUE":
                records.append({"decision_index": di, "adjustment_index": ai, "classification": status,
                                "raw_adjustment": adjustment})
    return {"source": str(path), "read_only": True, "movement_exceptions": records,
            "inconsistent_count": sum(x["classification"].startswith("INCONSISTENT") for x in records),
            "subcent_count": sum(x["classification"] == "LEGITIMATE_SUBCENT_DISPLAY" for x in records)}

def selftest():
    base = {"previous_weight": "0", "new_weight": "0.1", "order_side": "buy", "order_value_brl": "0.00"}
    cases = [
        ({"order_value_brl_unrounded": "0.0049"}, "LEGITIMATE_SUBCENT_DISPLAY"),
        ({"order_value_brl_unrounded": "0.005"}, "INCONSISTENT_ZERO_OR_NEGATIVE_VALUE"),
        ({"order_value_brl_unrounded": "0"}, "INCONSISTENT_ZERO_OR_NEGATIVE_VALUE"),
        ({"order_value_brl_unrounded": "-0.001"}, "INCONSISTENT_ZERO_OR_NEGATIVE_VALUE"),
        ({"order_value_brl_unrounded": "NaN"}, "INCONSISTENT_NONFINITE"),
        ({"order_value_brl_unrounded": "Infinity"}, "INCONSISTENT_NONFINITE"),
        ({"order_value_brl_unrounded": "0.0049", "order_side": "sell"}, "INCONSISTENT_SIDE"),
        ({"order_value_brl_unrounded": "0.0049", "new_weight": "0"}, "INCONSISTENT_ZERO_DELTA"),
        ({"order_value_brl_unrounded": "0.0049", "order_value_brl": "-0.01"}, "INCONSISTENT_ZERO_OR_NEGATIVE_VALUE"),
        ({"order_value_brl_unrounded": "0.0049", "order_value_brl": "0.01"}, "POSITIVE_DISPLAYED_VALUE"),
    ]
    for override, expected in cases:
        actual = classify({**base, **override})
        assert actual == expected, (override, actual, expected)
    print("V13 movement forensic adversarial tests: 10 PASS (fixtures only)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default="reports/paper_v13_ledger.json")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        result = inspect(args.ledger)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        if result["inconsistent_count"]:
            raise SystemExit(2)
