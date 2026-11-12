"""Read-only gate for a NEW V99 R106 forward journal. Never creates trades.

The candidate journal is supplied externally; this tool cannot infer missing fills.
No mutation, no exchange connectivity, no promotion or publication.
"""
import argparse
import hashlib
import json
import math
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = ("epoch_id", "epoch_start_utc", "mode", "initial_capital", "events")
MODE = "RESEARCH_ONLY_NO_REAL_ORDERS"

def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def verify(journal, provenance):
    errors = []
    if not isinstance(journal, dict) or any(k not in journal for k in REQUIRED):
        return {"status": "BLOCKED", "errors": ["INVALID_JOURNAL_SCHEMA"], "publication_authorized": False}
    if journal["mode"] != MODE:
        errors.append("UNSAFE_MODE")
    if journal["epoch_id"] != provenance.get("epoch_id"):
        errors.append("EPOCH_ID_MISMATCH")
    if journal["epoch_start_utc"] != provenance.get("epoch_start_utc"):
        errors.append("EPOCH_START_MISMATCH")
    if provenance.get("status") != "RECEIPTS_PRECHECK_PASS_NOT_PUBLICATION_AUTHORIZATION" or provenance.get("errors"):
        errors.append("PROVENANCE_NOT_VERIFIED")
    try:
        capital = Decimal(str(journal["initial_capital"]))
        if not capital.is_finite() or capital <= 0:
            errors.append("INVALID_INITIAL_CAPITAL")
    except (InvalidOperation, TypeError, ValueError):
        errors.append("INVALID_INITIAL_CAPITAL")
    events = journal["events"]
    if not isinstance(events, list):
        errors.append("INVALID_EVENTS")
        events = []
    previous = "0" * 64
    ids = set()
    last_time = None
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"EVENT_{i}_INVALID")
            continue
        if event.get("type") not in ("MARK", "FILL", "FUNDING", "FEE"):
            errors.append(f"EVENT_{i}_UNKNOWN_TYPE")
        if not isinstance(event.get("receipt_sha256"), str) or len(event["receipt_sha256"]) != 64 or any(ch not in "0123456789abcdef" for ch in event["receipt_sha256"]):
            errors.append(f"EVENT_{i}_MISSING_RECEIPT_HASH")
        if event.get("event_id") in ids or not event.get("event_id"):
            errors.append(f"EVENT_{i}_DUPLICATE_OR_MISSING_ID")
        ids.add(event.get("event_id"))
        timestamp = event.get("event_utc")
        try:
            if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
                raise ValueError("timestamp must be UTC Z")
            instant = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if instant.utcoffset() != timezone.utc.utcoffset(None) or (last_time is not None and instant < last_time):
                raise ValueError("non-UTC or decreasing timestamp")
            last_time = instant
        except (ValueError, TypeError, OverflowError):
            errors.append(f"EVENT_{i}_INVALID_ORDER")
        if event.get("prev_hash") != previous:
            errors.append(f"EVENT_{i}_CHAIN_BREAK")
        payload = {k: v for k, v in event.items() if k != "hash"}
        digest = hashlib.sha256(canonical(payload)).hexdigest()
        if event.get("hash") != digest:
            errors.append(f"EVENT_{i}_HASH_MISMATCH")
        previous = digest
        if event.get("type") == "FILL" and not all(event.get(k) for k in ("fill_id", "fee_tier", "executed_qty", "executed_price")):
            errors.append(f"EVENT_{i}_INCOMPLETE_FILL")
        if event.get("type") == "FUNDING" and not event.get("settlement_event_id"):
            errors.append(f"EVENT_{i}_UNSETTLED_FUNDING")
    if journal.get("head_hash") != previous:
        errors.append("HEAD_HASH_MISMATCH")
    # Structural integrity is necessary, not sufficient. Independent accounting,
    # receipt-to-event matching and economic certification remain separate gates.
    return {"status": "STRUCTURAL_PRECHECK_ONLY" if not errors else "BLOCKED",
            "errors": sorted(set(errors)), "event_count": len(events),
            "publication_authorized": False, "real_orders_authorized": False,
            "economic_validation_complete": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--journal", type=Path, required=True)
    p.add_argument("--provenance-result", type=Path, required=True)
    args = p.parse_args()
    result = verify(json.loads(args.journal.read_text()), json.loads(args.provenance_result.read_text()))
    print(json.dumps(result, sort_keys=True))
    if result["status"] == "BLOCKED":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
