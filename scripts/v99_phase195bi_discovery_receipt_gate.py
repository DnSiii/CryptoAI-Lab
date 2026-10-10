"""Read-only V99 Phase195-BI point-in-time discovery provenance audit.

A closed market candle is not an authenticated exchange discovery receipt.
No promotion, no publication and no frozen-engine modifications are permitted.
"""
from __future__ import annotations

import json
import zipfile
from datetime import datetime, timedelta

IMMUTABLE = ("source", "start_month", "onboard_date", "discovered_at_utc", "eligible_after_timestamp")


def utc(value):
    if not isinstance(value, str):
        raise ValueError("timestamp required")
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError("explicit UTC required")
    return t


def first_safe_hour(receipt):
    t = utc(receipt)
    return t.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def strict_json(raw):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("duplicate JSON key: " + key)
            obj[key] = value
        return obj
    def reject(value):
        raise ValueError("nonfinite JSON: " + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject)


def read_zip(path):
    with zipfile.ZipFile(path) as z:
        return {
            "universe": strict_json(z.read("state/paper_v15_universe.json")),
            "sync": strict_json(z.read("reports/paper_data_sync_v15.json")),
            "ledger": strict_json(z.read("reports/paper_v15_ledger.json")),
        }


def audit(old, new):
    a = old["universe"]["symbols"]
    b = new["universe"]["symbols"]
    if old["ledger"].get("mode") != "PAPER_ONLY" or new["ledger"].get("mode") != "PAPER_ONLY":
        raise ValueError("paper-only required")
    added = sorted(set(b)-set(a))
    removed = sorted(set(a)-set(b))
    changed = {
        s: [f for f in IMMUTABLE if a[s].get(f) != b[s].get(f)]
        for s in a.keys() & b.keys()
    }
    changed = {s: fields for s, fields in changed.items() if fields}
    backdated = {}
    first_safe = {}
    for symbol, row in b.items():
        if row.get("source") != "dynamic_binance_discovery":
            continue
        first = first_safe_hour(row["discovered_at_utc"])
        first_safe[symbol] = first
        if utc(row["eligible_after_timestamp"]) < first:
            backdated[symbol] = {
                "eligible": row["eligible_after_timestamp"],
                "first_safe": first.isoformat(),
            }
    reported = new["sync"].get("new_symbols")
    if not isinstance(reported, list) or len(reported) != len(set(reported)):
        raise ValueError("invalid new-symbol receipt list")
    reissued = sorted(set(reported) & set(a))
    unreported = sorted(set(added)-set(reported))
    unsafe_actions, adjustments = [], 0
    last = None
    for event in new["ledger"]["decisions"]:
        t = utc(event["timestamp"])
        if last is not None and t <= last:
            raise ValueError("unordered or duplicate decisions")
        last = t
        for adjustment in event.get("adjustments", []):
            symbol = adjustment["symbol"]
            if symbol in first_safe:
                adjustments += 1
                if t < first_safe[symbol]:
                    unsafe_actions.append({"timestamp": t.isoformat(), "symbol": symbol})
    hold = bool(removed or changed or backdated or reissued or unreported or unsafe_actions)
    return {
        "status": "DATA_ONLY_HOLD" if hold else "OBSERVED_ONLY_NOT_CERTIFIED",
        "publication_authorized": False,
        "promotion_authorized": False,
        "source_receipts_authenticated": False,
        "added": added,
        "removed": removed,
        "changed_immutable": changed,
        "retroactive_eligibility": backdated,
        "reissued_new": reissued,
        "unreported_new": unreported,
        "observed_dynamic_adjustments": adjustments,
        "premature_observed_actions": unsafe_actions,
        "observations_are_capped": True,
    }


if __name__ == "__main__":
    import sys
    result = audit(read_zip(sys.argv[1]), read_zip(sys.argv[2]))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(2 if result["status"] == "DATA_ONLY_HOLD" else 0)
