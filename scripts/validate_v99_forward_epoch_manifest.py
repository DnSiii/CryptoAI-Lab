"""Fail-closed, read-only R106 forward epoch manifest gate.

This tool NEVER generates trades, fills, PnL, or orders. It validates a proposed
new namespace and provenance before any separate forward writer may run.
Usage: python scripts/validate_v99_forward_epoch_manifest.py manifest.json
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
import sys
from datetime import datetime, timezone
from pathlib import Path

VARIANTS = {"F1", "F12", "F3", "F7", "R98"}
REQUIRED_RECEIPT = {
    "source", "captured_at_utc", "event_at_utc", "instrument",
    "units", "quantity", "price", "fee_currency", "fee_amount",
    "settled_funding", "raw_sha256",
}


def utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset().total_seconds() != 0:
        raise ValueError("timestamp must be timezone-aware UTC")
    return dt.astimezone(timezone.utc)


def validate(m: dict) -> dict:
    if m.get("mode") != "RESEARCH_ONLY" or m.get("real_orders_enabled") is not False:
        raise ValueError("must remain RESEARCH_ONLY without real orders")
    if m.get("economics_status") != "UNVERIFIED":
        raise ValueError("economic promotion forbidden at epoch initialization")
    if set(m.get("variants", [])) != VARIANTS or len(m["variants"]) != 5:
        raise ValueError("exactly five unique frozen variant IDs required")
    if not m.get("epoch_id") or not str(m.get("output_namespace", "")).startswith("research-forward-epochs/"):
        raise ValueError("new versioned epoch ID and isolated output namespace required")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", str(m["epoch_id"])):
        raise ValueError("unsafe epoch ID")
    namespace = m["output_namespace"]
    if any(part in ("", ".", "..") for part in namespace.split("/")) or "\\" in namespace or namespace != f"research-forward-epochs/{m['epoch_id']}":
        raise ValueError("unsafe or mismatched forward namespace")
    predecessor = m["predecessor"]
    digest = predecessor["ledger_sha256"]
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("invalid predecessor SHA256")
    if not predecessor.get("commit_sha") or not predecessor.get("immutable_source"):
        raise ValueError("immutable predecessor location and commit required")
    boundary = utc(m["start_after_utc"])
    references = m["last_historical_reference_by_variant"]
    if set(references) != VARIANTS:
        raise ValueError("missing per-variant historical boundary")
    if any(boundary <= utc(references[v]) for v in VARIANTS):
        raise ValueError("forward boundary overlaps historical reference")
    events = m.get("receipts", [])
    last = boundary
    hashes = set()
    for r in events:
        if not REQUIRED_RECEIPT.issubset(r):
            raise ValueError("missing original receipt economic fields")
        for field in ("source", "instrument", "units", "fee_currency"):
            if not isinstance(r[field], str) or not r[field].strip():
                raise ValueError(f"missing receipt provenance: {field}")
        for field in ("quantity", "price", "fee_amount", "settled_funding"):
            try:
                amount = Decimal(str(r[field]))
            except (InvalidOperation, ValueError, TypeError):
                raise ValueError(f"invalid numeric receipt field: {field}") from None
            if not amount.is_finite() or (field in ("quantity", "price") and amount <= 0) or (field == "fee_amount" and amount < 0):
                raise ValueError(f"invalid economic receipt field: {field}")
        event, capture = utc(r["event_at_utc"]), utc(r["captured_at_utc"])
        if event < last or event <= boundary or capture < event:
            raise ValueError("pre-boundary, noncausal or out-of-order receipt")
        if len(r["raw_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in r["raw_sha256"]):
            raise ValueError("invalid raw receipt hash")
        if r["raw_sha256"] in hashes:
            raise ValueError("duplicate raw receipt")
        hashes.add(r["raw_sha256"])
        # Multiple independent fills may share an exchange timestamp; raw hashes
        # identify duplicate receipts without discarding legitimate same-time fills.
        last = event
    return {
        "validated_manifest_structure": True,
        "original_receipts_independently_verified": False,
        "economic_validation": False,
        "mode": "RESEARCH_ONLY",
        "receipts_declared": len(events),
        "epoch_id": m["epoch_id"],
    }


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_v99_forward_epoch_manifest.py manifest.json")
    manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(validate(manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
