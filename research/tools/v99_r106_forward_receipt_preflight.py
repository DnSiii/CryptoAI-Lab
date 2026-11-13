"""Fail-closed, read-only as-of receipt gate for a NEW V99 forward epoch.

No legacy reads/writes, trading, or publication. A passing manifest is necessary,
not sufficient: independent accounting and CI must still authorize the epoch.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

def utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be explicit UTC Z")
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.utcoffset() != timedelta(0):
        raise ValueError("non-UTC timestamp")
    return t

def check(manifest, raw_dir, *, phase="historical"):
    if phase not in ("historical", "forward"):
        raise ValueError("unknown receipt phase")
    errors = []
    if manifest.get("mode") != "RESEARCH_ONLY_NO_REAL_ORDERS":
        errors.append("REAL_ORDER_MODE_NOT_FORBIDDEN")
    try:
        start = utc(manifest["epoch_start_utc"])
        if start.minute or start.second or start.microsecond:
            errors.append("NON_HOURLY_EPOCH_START")
    except (KeyError, TypeError, ValueError):
        errors.append("INVALID_EPOCH_START")
        start = None
    if not manifest.get("epoch_id") or manifest.get("legacy_epoch_id") == manifest.get("epoch_id"):
        errors.append("MISSING_OR_REUSED_EPOCH_ID")
    receipts = manifest.get("receipts")
    if not isinstance(receipts, list) or not receipts:
        receipts = []
        errors.append("NO_SOURCE_RECEIPTS")
    seen = set()
    grouped = {}
    for i, r in enumerate(receipts):
        prefix = f"receipt[{i}]"
        try:
            venue, symbol, kind = (r[k] for k in ("venue", "symbol", "kind"))
            if not all(isinstance(x, str) and x.strip() for x in (venue, symbol, kind)):
                raise ValueError("blank identity")
            key = (venue, symbol, kind, r["close_utc"])
            if key in seen:
                errors.append(prefix + ":DUPLICATE_RECEIPT")
            seen.add(key)
            close, acquired = utc(r["close_utc"]), utc(r["acquired_utc"])
            if close.minute or close.second or close.microsecond:
                errors.append(prefix + ":NON_HOURLY_CLOSE")
            if acquired < close:
                errors.append(prefix + ":LOOKAHEAD_ACQUISITION")
            if phase == "historical":
                if start and close > start:
                    errors.append(prefix + ":AFTER_EPOCH_START")
                if start and acquired > start:
                    errors.append(prefix + ":NOT_AVAILABLE_AS_OF_START")
            elif start and close < start:
                errors.append(prefix + ":FORWARD_RECEIPT_BEFORE_EPOCH")
            if not isinstance(r.get("source_url_or_archive_id"), str) or not r["source_url_or_archive_id"].strip():
                errors.append(prefix + ":NO_PROVENANCE")
            name = r["raw_file"]
            if not isinstance(name, str) or Path(name).name != name or name in (".", ".."):
                raise ValueError("unsafe raw filename")
            path = raw_dir / name
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            expected = r["sha256"]
            if len(expected) != 64 or digest != expected:
                errors.append(prefix + ":RAW_HASH_MISMATCH")
            if kind == "funding" and not r.get("settlement_event_id"):
                errors.append(prefix + ":MISSING_FUNDING_SETTLEMENT_ID")
            if kind == "execution" and not r.get("fee_tier"):
                errors.append(prefix + ":MISSING_NATIVE_FEE_TIER")
            grouped.setdefault((venue, symbol, kind), []).append(close)
        except (KeyError, TypeError, ValueError, OSError) as e:
            errors.append(prefix + ":INVALID_OR_MISSING_RAW_RECEIPT:" + type(e).__name__)
    for key, dates in grouped.items():
        dates.sort()
        if any(b-a != timedelta(hours=1) for a,b in zip(dates,dates[1:])):
            errors.append("NONCONTIGUOUS_HOURLY_RECEIPTS:" + "/".join(key))
    return {"status": "RECEIPTS_PRECHECK_PASS_NOT_PUBLICATION_AUTHORIZATION" if not errors else "BLOCKED",
            "errors": sorted(set(errors)), "receipt_count": len(receipts),
            "publication_authorized": False, "real_orders_authorized": False,
            "holdout_accessed": False, "legacy_mutated": False}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    try:
        result = check(json.loads(args.manifest.read_text(encoding="utf-8")), args.raw_dir)
    except (OSError, ValueError, TypeError) as e:
        result = {"status": "BLOCKED", "errors": ["INVALID_MANIFEST:" + type(e).__name__],
                  "publication_authorized": False, "real_orders_authorized": False}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] == "BLOCKED":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
