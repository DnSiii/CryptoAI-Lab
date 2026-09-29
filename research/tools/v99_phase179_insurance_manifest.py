#!/usr/bin/env python3
"""Deterministic, fail-closed TRAIN-only integrity manifest for Phase179.

Consumes a previously captured first-party BitMEX insurance-history JSON array.
It intentionally performs no network access and computes no returns/PnL.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

TRAIN_START = datetime(2021, 12, 1, tzinfo=timezone.utc)
FIREWALL = datetime(2024, 1, 18, tzinfo=timezone.utc)


def parse_ts(v: str) -> datetime:
    d = datetime.fromisoformat(v.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("naive timestamp forbidden")
    return d.astimezone(timezone.utc)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = Path(a.raw_json).read_bytes()
    rows = json.loads(raw)
    if not isinstance(rows, list) or not rows:
        raise SystemExit("FAIL: expected non-empty JSON array")

    parsed = []
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or "timestamp" not in r:
            raise SystemExit(f"FAIL: row {i} missing timestamp")
        t = parse_ts(str(r["timestamp"]))
        if t >= FIREWALL:
            raise SystemExit(f"FAIL: holdout/post-firewall row present: {t.isoformat()}")
        if t < TRAIN_START:
            continue
        currency = str(r.get("currency", ""))
        if not currency:
            raise SystemExit(f"FAIL: row {i} missing currency")
        parsed.append((t, currency, r))
    if not parsed:
        raise SystemExit("FAIL: no TRAIN rows")

    parsed.sort(key=lambda x: (x[0], x[1]))
    keys = [(t.isoformat(), c) for t, c, _ in parsed]
    dup = len(keys) - len(set(keys))
    conflicts = 0
    seen = {}
    for t, c, r in parsed:
        k = (t.isoformat(), c)
        canonical = json.dumps(r, sort_keys=True, separators=(",", ":"))
        if k in seen and seen[k] != canonical:
            conflicts += 1
        seen[k] = canonical

    canonical_rows = [r for _, _, r in parsed]
    canonical_bytes = (json.dumps(canonical_rows, sort_keys=True, separators=(",", ":")) + "\n").encode()
    currencies = sorted({c for _, c, _ in parsed})
    by_currency = {}
    for c in currencies:
        ts = [t for t, cc, _ in parsed if cc == c]
        gaps = [(b-a).total_seconds() for a,b in zip(ts, ts[1:])]
        by_currency[c] = {"rows": len(ts), "min_timestamp": ts[0].isoformat(), "max_timestamp": ts[-1].isoformat(), "max_gap_seconds": max(gaps) if gaps else None}

    manifest = {
        "phase": 179,
        "train_start": TRAIN_START.isoformat(),
        "firewall_exclusive": FIREWALL.isoformat(),
        "raw_sha256": sha256(raw),
        "canonical_sha256": sha256(canonical_bytes),
        "rows_train": len(parsed),
        "duplicate_keys": dup,
        "conflicting_duplicate_keys": conflicts,
        "currencies": currencies,
        "by_currency": by_currency,
        "status": "FAIL" if conflicts else "INTEGRITY_PROBE_ONLY_NOT_DATA_ADMISSION",
    }
    Path(a.out).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if conflicts:
        raise SystemExit("FAIL: conflicting duplicate keys")

if __name__ == "__main__":
    main()
