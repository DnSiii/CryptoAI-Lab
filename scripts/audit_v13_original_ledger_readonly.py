#!/usr/bin/env python3
"""Read-only audit of original V13 ledger adjustments; never repairs history."""
import argparse
import json
import math
from pathlib import Path


def audit(path):
    ledger = json.loads(Path(path).read_text(encoding="utf-8"))
    counts = {"positive_reconciled": 0, "positive_missing_raw": 0,
              "zero_subcent_proven": 0, "zero_missing_raw": 0,
              "inconsistent": 0}
    findings = []
    for di, decision in enumerate(ledger.get("decisions", [])):
        for ai, item in enumerate(decision.get("adjustments", [])):
            raw = item.get("order_value_brl_unrounded")
            displayed = item.get("order_value_brl")
            try:
                amount = float(displayed)
                precise = None if raw is None else float(raw)
                delta = float(item["new_weight"]) - float(item["previous_weight"])
                valid = math.isfinite(amount) and amount >= 0 and math.isfinite(delta) and delta != 0
                if precise is not None:
                    valid &= math.isfinite(precise) and precise > 0 and round(precise, 2) == amount
                if not valid:
                    label = "inconsistent"
                elif amount == 0:
                    label = "zero_missing_raw" if precise is None else (
                        "zero_subcent_proven" if 0 < precise < 0.005 else "inconsistent")
                else:
                    label = "positive_missing_raw" if precise is None else "positive_reconciled"
            except (ValueError, TypeError, KeyError, OverflowError):
                label = "inconsistent"
            counts[label] += 1
            if label not in ("positive_reconciled",):
                findings.append({"decision_index": di, "adjustment_index": ai,
                                 "timestamp": decision.get("timestamp"),
                                 "symbol": item.get("symbol"), "classification": label,
                                 "displayed": displayed, "raw": raw,
                                 "previous_weight": item.get("previous_weight"),
                                 "new_weight": item.get("new_weight")})
    return {"source": str(path), "counts": counts, "findings": findings,
            "historical_integrity_certified": not (
                counts["zero_missing_raw"] or counts["inconsistent"] or counts["positive_missing_raw"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", help="Original unmodified reports/paper_v13_ledger.json")
    parser.add_argument("--output", help="Optional forensic JSON report")
    args = parser.parse_args()
    result = audit(args.ledger)
    report = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)
    if args.output:
        Path(args.output).write_text(report + "\n", encoding="utf-8")
    print(report)
    raise SystemExit(0 if result["historical_integrity_certified"] else 2)
