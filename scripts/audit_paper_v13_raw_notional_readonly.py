"""Read-only audit of original V13 paper ledger; never rewrites trades."""
import json
import math
from pathlib import Path

path = Path("reports/paper_v13_ledger.json")
ledger = json.loads(path.read_text())
counts = {"valid_positive": 0, "valid_subcent": 0, "invalid": 0}
for i, decision in enumerate(ledger.get("decisions", [])):
    for j, adj in enumerate(decision.get("adjustments", [])):
        display = adj.get("order_value_brl")
        raw = adj.get("order_value_brl_unrounded")
        delta = float(adj["new_weight"]) - float(adj["previous_weight"])
        try:
            d = float(display)
            r = float(raw) if raw is not None else None
            valid_positive = math.isfinite(d) and d > 0
            valid_subcent = (d == 0 and r is not None and math.isfinite(r)
                            and 0 < r < 0.005 and delta != 0
                            and round(r, 2) == d)
        except (TypeError, ValueError, OverflowError):
            valid_positive = valid_subcent = False
        key = "valid_positive" if valid_positive else "valid_subcent" if valid_subcent else "invalid"
        counts[key] += 1
        if key != "valid_positive":
            print(json.dumps({"decision_index": i, "adjustment_index": j,
                              "timestamp": decision.get("timestamp"),
                              "symbol": adj.get("symbol"), "display": display,
                              "raw": raw, "delta": delta, "classification": key},
                             ensure_ascii=False, default=str))
print(json.dumps({"counts": counts, "latest_data_timestamp": ledger.get("latest_data_timestamp")}))
if counts["invalid"]:
    raise SystemExit("FAIL CLOSED: inconsistent movements in historical ledger")
