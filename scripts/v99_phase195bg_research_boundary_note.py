"""Read-only V99 research backtest/paper separation."""
import json
import zipfile

def read(path):
    with zipfile.ZipFile(path) as z:
        return json.loads(z.read("reports/paper_v99_research_ledger.json"))

def audit(old, new):
    cutoff = old["paper_start_after_timestamp"]
    if cutoff != new["paper_start_after_timestamp"]:
        raise ValueError("paper boundary moved")
    counts = {}
    for name in ("r98", "f1", "f3", "f7", "f12"):
        a = {x["timestamp"]: x for x in old["backtest_reference"][name]["curve"]}
        b = {x["timestamp"]: x for x in new["backtest_reference"][name]["curve"]}
        counts[name] = {"historical_rewrites": sum(a[t] != b[t] for t in a.keys() & b.keys() if t < cutoff),
                        "forward_mislabeled": sum(t >= cutoff for t in b)}
    return {"status": "DATA_ONLY_HOLD" if any(any(x.values()) for x in counts.values()) else "OBSERVED_ONLY",
            "promotion_authorized": False, "variants": counts}
