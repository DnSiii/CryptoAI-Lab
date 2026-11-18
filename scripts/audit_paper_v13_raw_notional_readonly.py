"""Read-only raw/display reconciliation of immutable V13 historical paper."""
import json
import math
from collections import Counter
from pathlib import Path

ledger = json.loads(Path("reports/paper_v13_ledger.json").read_text())
counts = Counter()
examples_by_class = {}
for i, decision in enumerate(ledger.get("decisions", [])):
    for j, adj in enumerate(decision.get("adjustments", [])):
        display = adj.get("order_value_brl")
        raw = adj.get("order_value_brl_unrounded")
        try:
            d = float(display)
            r = float(raw) if raw is not None else None
            delta = float(adj["new_weight"]) - float(adj["previous_weight"])
            if not math.isfinite(d) or not math.isfinite(delta) or delta == 0:
                classification = "invalid_display_or_delta"
            elif r is None:
                classification = "positive_missing_raw" if d > 0 else "invalid_missing_raw"
            elif not math.isfinite(r) or r <= 0:
                classification = "invalid_raw"
            elif d == 0 and 0 < r < 0.005 and round(r, 2) == d:
                classification = "valid_subcent"
            elif d > 0 and round(r, 2) == d:
                classification = "valid_positive_reconciled"
            else:
                classification = "positive_mismatch" if d > 0 else "invalid_zero"
        except (TypeError, ValueError, OverflowError, KeyError):
            classification = "invalid_parse"
        counts[classification] += 1
        if classification not in ("valid_positive_reconciled", "valid_subcent") and len(examples_by_class.setdefault(classification, [])) < 12:
            examples_by_class[classification].append({"decision_index": i, "adjustment_index": j,
                             "timestamp": decision.get("timestamp"), "symbol": adj.get("symbol"),
                             "display": display, "raw": raw,
                             "previous_weight": adj.get("previous_weight"),
                             "new_weight": adj.get("new_weight"),
                             "classification": classification})
print(json.dumps({"counts": dict(sorted(counts.items())), "examples_by_class": examples_by_class,
                  "latest_data_timestamp": ledger.get("latest_data_timestamp")},
                 ensure_ascii=False, indent=2, default=str))
bad = sum(n for k, n in counts.items() if k not in ("valid_positive_reconciled", "valid_subcent", "positive_missing_raw"))
if bad:
    raise SystemExit(f"FAIL CLOSED: {bad} inconsistent original movements; historical paper unchanged")
if counts["positive_missing_raw"]:
    print("CAUTION: positive records missing raw precision cannot be independently reconciled")
