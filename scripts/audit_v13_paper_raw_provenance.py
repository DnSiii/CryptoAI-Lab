"""Read-only forensic report for V13 paper zero-display adjustments.

Run after the paper ledger has been generated, before modifying any historical data.
Never infers or manufactures missing raw execution values.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "reports/paper_v13_ledger.json"


def classify(adjustment: dict) -> str:
    try:
        shown = float(adjustment["order_value_brl"])
        delta = float(adjustment["new_weight"]) - float(adjustment["previous_weight"])
    except (KeyError, ValueError, TypeError, OverflowError):
        return "invalid_display_or_weight"
    if not math.isfinite(shown) or shown < 0 or not math.isfinite(delta) or delta == 0:
        return "invalid_display_or_weight"
    raw = adjustment.get("order_value_brl_unrounded")
    if raw is None:
        return "missing_raw_provenance" if shown == 0 else "positive_display_without_raw"
    try:
        raw = float(raw)
    except (ValueError, TypeError, OverflowError):
        return "invalid_raw"
    if not math.isfinite(raw) or raw <= 0:
        return "invalid_raw"
    if round(raw, 2) != shown:
        return "raw_display_mismatch"
    if shown == 0:
        return "verified_subcent" if 0 < raw < 0.005 else "invalid_zero"
    return "verified_positive"


def main() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    counts = Counter()
    examples = {}
    for di, decision in enumerate(ledger.get("decisions", [])):
        for ai, adjustment in enumerate(decision.get("adjustments", [])):
            category = classify(adjustment)
            counts[category] += 1
            if category not in examples:
                examples[category] = {
                    "decision_index": di, "adjustment_index": ai,
                    "symbol": adjustment.get("symbol"),
                    "order_value_brl": adjustment.get("order_value_brl"),
                    "order_value_brl_unrounded": adjustment.get("order_value_brl_unrounded"),
                }
    print(json.dumps({"counts": dict(counts), "first_examples": examples}, indent=2, ensure_ascii=False))
    failures = ("missing_raw_provenance", "positive_display_without_raw", "invalid_display_or_weight", "invalid_raw",
                "raw_display_mismatch", "invalid_zero")
    if any(counts[k] for k in failures):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
