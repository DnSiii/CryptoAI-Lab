"""Fail-closed selection of an original, independently audited same-hour OKX pair.

No economic calculations, paper mutation, holdout, orders or synthetic fallback.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from research.tools.v99_r106_asof_pair_gate import audit
from research.tools.v99_r106_receipt_append import utc

MAX_AGE_SECONDS = 2 * 3600

def select(root: Path, *, now: datetime | None = None, audit_fn=audit):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    market_root, terms_root = root / "markets", root / "terms"
    if not market_root.is_dir() or not terms_root.is_dir():
        raise ValueError("original receipt stream missing")
    candidates = sorted(
        {p.name for p in market_root.iterdir() if p.is_dir() and not p.is_symlink()}
        & {p.name for p in terms_root.iterdir() if p.is_dir() and not p.is_symlink()},
        reverse=True,
    )
    rejected = []
    for bucket in candidates:
        try:
            bucket_time = datetime.strptime(bucket, "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
            if bucket_time > now or (now - bucket_time).total_seconds() > MAX_AGE_SECONDS:
                raise ValueError("bucket outside explicit 2h freshness budget")
            report = audit_fn(market_root / bucket, terms_root / bucket)
            times = [utc(report["market_acquired_utc"]), utc(report["terms_acquired_utc"])]
            if any(t > now or (now - t).total_seconds() > MAX_AGE_SECONDS for t in times):
                raise ValueError("acquisition stale or in future")
            if any(t.strftime("%Y-%m-%dT%H") != bucket for t in times):
                raise ValueError("acquisition outside source bucket")
            if abs((times[0] - times[1]).total_seconds()) > 25 * 60:
                raise ValueError("acquisition skew exceeds 25 minutes")
            if report.get("paper_publication_authorized") is not False or report.get("promotion_authorized") is not False:
                raise ValueError("unexpected publication authorization")
            return {"status": "DATA_ONLY_FRESH_PAIR", "bucket": bucket,
                    "report": report, "rejected_newer_buckets": rejected,
                    "paper_publication_authorized": False, "promotion_authorized": False}
        except (ValueError, KeyError, TypeError, OSError) as exc:
            rejected.append({"bucket": bucket, "reason": str(exc)})
    raise ValueError("NO_FRESH_VERIFIED_PAIR: " + repr(rejected))
