"""Read-only forensic audit for zero-valued paper adjustments.

Usage: python scripts/audit_paper_zero_value_adjustments.py reports/paper_v13_ledger.json
Does not modify, reconstruct or authorize any trade.
"""
import json
import math
import sys
from pathlib import Path


def inspect(ledger):
    anomalies = []
    for di, decision in enumerate(ledger.get("decisions", [])):
        for ai, adjustment in enumerate(decision.get("adjustments", [])):
            value = adjustment.get("order_value_brl")
            old = adjustment.get("previous_weight")
            new = adjustment.get("new_weight")
            record = {"decision_index": di, "adjustment_index": ai,
                      "decision_timestamp": decision.get("timestamp"),
                      "symbol": adjustment.get("symbol"),
                      "order_side": adjustment.get("order_side"),
                      "order_value_brl": value,
                      "previous_weight": old, "new_weight": new,
                      "raw_adjustment": adjustment}
            try:
                numeric = float(value)
                delta = float(new) - float(old)
            except (TypeError, ValueError):
                record["classification"] = "INVALID_NUMERIC_FIELDS"
            else:
                if not math.isfinite(numeric) or not math.isfinite(delta):
                    record["classification"] = "NONFINITE"
                elif numeric < 0:
                    record["classification"] = "NEGATIVE_VALUE"
                elif numeric == 0 and delta != 0:
                    # Zero cents might represent a rounded sub-cent order,
                    # but cannot be proven without pre-round notional and execution receipt.
                    record["classification"] = "ZERO_WITH_NONZERO_WEIGHT_UNRESOLVED"
                elif numeric == 0:
                    record["classification"] = "ZERO_WITH_ZERO_DELTA_UNRESOLVED"
                elif delta == 0:
                    record["classification"] = "POSITIVE_VALUE_ZERO_DELTA"
                else:
                    continue
            anomalies.append(record)
    return anomalies


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reports/paper_v13_ledger.json")
    ledger = json.loads(path.read_text(encoding="utf-8"))
    anomalies = inspect(ledger)
    print(json.dumps({"file": str(path), "anomaly_count": len(anomalies),
                      "anomalies": anomalies}, indent=2, ensure_ascii=False, default=str))
    # Fail closed: diagnostic output is not an exemption to the original verifier.
    return 1 if anomalies else 0


if __name__ == "__main__":
    sys.exit(main())
