"""Read-only V99 historical/forward partition; never authorizes publication."""
from __future__ import annotations
import json
import math
from datetime import datetime, timedelta
NAMES = ("r98", "f1", "f3", "f7", "f12")

def utc(value):
    if not isinstance(value, str):
        raise ValueError("explicit UTC required")
    ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if ts.tzinfo is None or ts.utcoffset() != timedelta(0):
        raise ValueError("explicit UTC required")
    return ts

def partition(rows, boundary):
    cutoff = utc(boundary)
    if not isinstance(rows, list) or not rows:
        raise ValueError("nonempty backtest curve required")
    historical, quarantine, last = [], [], None
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("curve row must be an object")
        ts = utc(row.get("timestamp"))
        if last is not None and ts <= last:
            raise ValueError("duplicate or unordered backtest timestamps")
        last = ts
        for field in ("equity_multiple", "daily_return_pct"):
            value = row.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("missing/nonfinite " + field)
        if row["equity_multiple"] <= 0:
            raise ValueError("nonpositive equity multiple")
        (historical if ts < cutoff else quarantine).append(row)
    if not historical:
        raise ValueError("no historical rows before paper boundary")
    return {"historical_curve": historical, "quarantined_forward_rows": len(quarantine),
            "last_historical": historical[-1]["timestamp"],
            "first_quarantined": quarantine[0]["timestamp"] if quarantine else None}

def audit_references(published, candidate):
    boundary = published.get("paper_start_after_timestamp")
    if utc(candidate.get("paper_start_after_timestamp")) != utc(boundary):
        raise ValueError("paper boundary moved")
    if published.get("mode") != "PAPER_ONLY" or candidate.get("mode") != "PAPER_ONLY":
        raise ValueError("PAPER_ONLY required")
    out = {}
    for name in NAMES:
        old = partition(published["backtest_reference"][name]["curve"], boundary)
        new = partition(candidate["backtest_reference"][name]["curve"], boundary)
        p = {utc(r["timestamp"]): r for r in old["historical_curve"]}
        q = {utc(r["timestamp"]): r for r in new["historical_curve"]}
        changed = sorted(t for t in p.keys() & q.keys() if p[t] != q[t])
        old_meta = {k: v for k,v in published["backtest_reference"][name].items() if k != "curve"}
        new_meta = {k: v for k,v in candidate["backtest_reference"][name].items() if k != "curve"}
        out[name] = {
            "published_historical_rows": len(p), "candidate_historical_rows": len(q),
            "published_forward_mislabeled": old["quarantined_forward_rows"],
            "candidate_forward_mislabeled": new["quarantined_forward_rows"],
            "historical_changed": len(changed),
            "first_historical_changed": changed[0].isoformat() if changed else None,
            "historical_missing": len(p.keys()-q.keys()),
            "historical_new": len(q.keys()-p.keys()),
            "historical_metadata_changed": old_meta != new_meta}
    return {"status": "DATA_ONLY_HOLD", "publication_authorized": False,
            "promotion_authorized": False, "train_only_certified": False,
            "source_time_authenticated": False, "paper_boundary": boundary, "variants": out}

if __name__ == "__main__":
    import sys, zipfile
    def load(path):
        if path.endswith(".zip"):
            with zipfile.ZipFile(path) as z:
                return json.loads(z.read("reports/paper_v99_research_ledger.json"))
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    print(json.dumps(audit_references(load(sys.argv[1]), load(sys.argv[2])), indent=2))
