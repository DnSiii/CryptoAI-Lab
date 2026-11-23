"""Read-only raw/display reconciliation of immutable V13 historical paper."""
import json
import math
from collections import Counter
from pathlib import Path

ledger = json.loads(Path("reports/paper_v13_ledger.json").read_text())
counts = Counter()
examples_by_class = {}
mismatch_ratios = []
mismatch_by_day_symbol = Counter()
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
        if classification == "positive_mismatch" and r is not None and math.isfinite(r) and r > 0:
            mismatch_by_day_symbol[(str(decision.get('timestamp', 'unknown'))[:10], str(adj.get('symbol', 'unknown')))] += 1
            mismatch_ratios.append({"decision_index": i, "adjustment_index": j,
                                    "timestamp": decision.get("timestamp"), "symbol": adj.get("symbol"),
                                    "ratio": d / r, "display": d, "raw": r})
        if classification not in ("valid_positive_reconciled", "valid_subcent") and len(examples_by_class.setdefault(classification, [])) < 12:
            examples_by_class[classification].append({"decision_index": i, "adjustment_index": j,
                             "timestamp": decision.get("timestamp"), "symbol": adj.get("symbol"),
                             "display": display, "raw": raw,
                             "previous_weight": adj.get("previous_weight"),
                             "new_weight": adj.get("new_weight"),
                             "classification": classification})
ratio_summary = {}
if mismatch_ratios:
    values = sorted(item["ratio"] for item in mismatch_ratios)
    ratio_summary = {"count": len(values), "min": values[0],
                     "median": values[len(values) // 2], "max": values[-1],
                     "near_1_01236_within_0_001": sum(abs(v - 1.01236) < 0.001 for v in values),
                     "first_12": mismatch_ratios[:12]}
print(json.dumps({"counts": dict(sorted(counts.items())), "examples_by_class": examples_by_class,
                  "positive_mismatch_ratio_diagnostics": ratio_summary,
                  "mismatch_by_day_symbol": [{"day": day, "symbol": symbol, "count": count}
                     for (day, symbol), count in sorted(mismatch_by_day_symbol.items())],
                  "latest_data_timestamp": ledger.get("latest_data_timestamp")},
                 ensure_ascii=False, indent=2, default=str))
bad = sum(n for k, n in counts.items() if k not in ("valid_positive_reconciled", "valid_subcent", "positive_missing_raw"))
if bad or counts["positive_missing_raw"]:
    raise SystemExit(f"FAIL CLOSED: {bad} inconsistent movements; {counts['positive_missing_raw']} missing original raw amounts; historical paper unchanged")
