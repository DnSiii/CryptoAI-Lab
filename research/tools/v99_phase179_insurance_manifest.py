#!/usr/bin/env python3
"""Deterministic, fail-closed TRAIN-only integrity manifest for Phase179.

Consumes a frozen first-party BitMEX insurance-history JSON array. It performs
no network access and computes no returns/PnL. Admission requires complete
TRAIN coverage under a cadence inferred only from TRAIN timestamps.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
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


def infer_cadence_seconds(ts: list[datetime]) -> int | None:
    """Robust deterministic cadence: modal positive inter-arrival gap."""
    gaps = [int((b-a).total_seconds()) for a, b in zip(ts, ts[1:]) if b > a]
    if not gaps:
        return None
    counts = Counter(gaps)
    # deterministic tie-break: smaller cadence wins
    return min(counts, key=lambda g: (-counts[g], g))


def month_key(t: datetime) -> str:
    return f"{t.year:04d}-{t.month:02d}"


def expected_months() -> list[str]:
    out, y, m = [], TRAIN_START.year, TRAIN_START.month
    while (y, m) <= (FIREWALL.year, FIREWALL.month):
        out.append(f"{y:04d}-{m:02d}")
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return out


def build_manifest(rows: list[dict], raw: bytes) -> dict:
    if not isinstance(rows, list) or not rows:
        raise ValueError("expected non-empty JSON array")
    parsed = []
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or "timestamp" not in r:
            raise ValueError(f"row {i} missing timestamp")
        t = parse_ts(str(r["timestamp"]))
        if t >= FIREWALL:
            raise ValueError(f"holdout/post-firewall row present: {t.isoformat()}")
        if t < TRAIN_START:
            continue
        currency = str(r.get("currency", ""))
        if not currency:
            raise ValueError(f"row {i} missing currency")
        parsed.append((t, currency, r))
    if not parsed:
        raise ValueError("no TRAIN rows")

    parsed.sort(key=lambda x: (x[0], x[1]))
    keys = [(t.isoformat(), c) for t, c, _ in parsed]
    duplicate_keys = len(keys) - len(set(keys))
    conflicts, seen = 0, {}
    for t, c, r in parsed:
        k = (t.isoformat(), c)
        canonical = json.dumps(r, sort_keys=True, separators=(",", ":"))
        if k in seen and seen[k] != canonical:
            conflicts += 1
        seen[k] = canonical

    canonical_rows = [r for _, _, r in parsed]
    canonical_bytes = (json.dumps(canonical_rows, sort_keys=True, separators=(",", ":")) + "\n").encode()
    currencies = sorted({c for _, c, _ in parsed})
    by_currency, failures = {}, []
    exp_months = expected_months()
    for c in currencies:
        ts = [t for t, cc, _ in parsed if cc == c]
        cadence = infer_cadence_seconds(ts)
        gaps = [int((b-a).total_seconds()) for a, b in zip(ts, ts[1:])]
        observed_months = sorted({month_key(t) for t in ts})
        missing_months = [m for m in exp_months if m not in observed_months]
        start_lag = int((ts[0] - TRAIN_START).total_seconds())
        end_lag = int((FIREWALL - ts[-1]).total_seconds())
        # A complete currency must begin no later than one inferred cadence after
        # TRAIN start and end no earlier than one cadence before the firewall.
        coverage_ok = cadence is not None and start_lag <= cadence and end_lag <= cadence
        # Jan-2024 is partial by design but still required.
        months_ok = not missing_months
        gap_limit = cadence * 2 if cadence is not None else None
        gap_ok = gap_limit is not None and all(g <= gap_limit for g in gaps)
        if not coverage_ok:
            failures.append(f"{c}:boundary_coverage")
        if not months_ok:
            failures.append(f"{c}:missing_months")
        if not gap_ok:
            failures.append(f"{c}:cadence_gaps")
        by_currency[c] = {
            "rows": len(ts), "min_timestamp": ts[0].isoformat(), "max_timestamp": ts[-1].isoformat(),
            "inferred_cadence_seconds": cadence, "max_gap_seconds": max(gaps) if gaps else None,
            "start_lag_seconds": start_lag, "end_lag_seconds": end_lag,
            "missing_months": missing_months, "coverage_ok": coverage_ok,
            "gap_ok": gap_ok,
        }
    if conflicts:
        failures.append("conflicting_duplicate_keys")

    return {
        "phase": 179, "train_start": TRAIN_START.isoformat(), "firewall_exclusive": FIREWALL.isoformat(),
        "raw_sha256": sha256(raw), "canonical_sha256": sha256(canonical_bytes),
        "rows_train": len(parsed), "duplicate_keys": duplicate_keys,
        "conflicting_duplicate_keys": conflicts, "currencies": currencies,
        "by_currency": by_currency, "failures": failures,
        "status": "FAIL" if failures else "INTEGRITY_PASS_DATA_ADMISSION_STILL_REQUIRES_SEMANTIC_AUDIT",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = Path(a.raw_json).read_bytes()
    try:
        manifest = build_manifest(json.loads(raw), raw)
    except (ValueError, json.JSONDecodeError) as e:
        raise SystemExit(f"FAIL: {e}")
    Path(a.out).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if manifest["status"] == "FAIL":
        raise SystemExit("FAIL: " + ",".join(manifest["failures"]))


if __name__ == "__main__":
    main()
