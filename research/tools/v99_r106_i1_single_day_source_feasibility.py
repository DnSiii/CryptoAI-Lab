"""One fixed I1 licensed-source day: necessary quote feasibility, NEVER economics.

2022-01-23 UTC only. Preregistration:
research/V99_R106_I1_SINGLE_DAY_SOURCE_FEASIBILITY_PREREG_20261029.md
No trading, PnL, post-TRAIN observations, or promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from research.tools.v99_r106_i1_local_tape_import import (
    scan_day, require_hourly_original_coverage,
)
from research.tools.v99_r106_i1_source_driven_entry_book import _one_sunday
from research.verification.independent_v99_r106_i1_single_day_source import replay

DAY = date(2022, 1, 23)
DECISION_MS = int(datetime(2022, 1, 24, tzinfo=timezone.utc).timestamp() * 1000)
SCHEMA = "V99_I1_PREREGISTERED_ONE_DAY_SOURCE_FEASIBILITY_V1"


def _pair_counts(books):
    counts = {}
    for asset in ("BTC", "ETH"):
        grouped = defaultdict(list)
        for row in books[asset]:
            grouped[row["expiry_ms"]].append(row)
        pairs = 0
        for rows in grouped.values():
            for i, left in enumerate(rows):
                for right in rows[i + 1:]:
                    if (left["strike_usd"] != right["strike_usd"]
                            and abs(left["arrival_us"] - right["arrival_us"]) <= 1_000_000
                            and abs(left["venue_us"] - right["venue_us"]) <= 1_000_000):
                        pairs += 1
        counts[asset] = pairs
    return counts


def inspect(path, *, fixture=False, license_evidence=None, expected_sha256=None):
    path = Path(path)
    if path.name != "2022-01-23.csv.gz":
        raise ValueError("ONLY_PREREGISTERED_SOURCE_DAY_ALLOWED")
    if not path.is_file() or path.is_symlink():
        return {"schema": SCHEMA, "status": "SOURCE_MISSING", "certified_lifecycles": 0,
                "economic_train_executed": False, "promotion_authorized": False}
    if type(fixture) is not bool:
        raise ValueError("INVALID_FIXTURE_FLAG")
    if not fixture:
        evidence = Path(license_evidence) if license_evidence is not None else None
        if (evidence is None or not evidence.is_file() or evidence.is_symlink()
                or evidence.stat().st_size == 0):
            raise ValueError("LOCAL_WRITTEN_LICENSE_EVIDENCE_REQUIRED")
    if expected_sha256 is not None and (
            not isinstance(expected_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
        raise ValueError("INVALID_EXTERNAL_SOURCE_SHA256")
    scanned = scan_day(path, DAY)
    require_hourly_original_coverage(scanned)
    if expected_sha256 is not None and scanned["sha256"] != expected_sha256:
        raise ValueError("EXTERNAL_SOURCE_SHA256_MISMATCH")
    books, invalid, stale, rows = _one_sunday(path, scanned["rows"], DAY, DECISION_MS)
    primary = _pair_counts(books)
    independent = replay(path)
    if (independent["sha256"] != scanned["sha256"]
            or independent["rows"] != rows
            or independent["pairs_by_asset"] != primary
            or independent["coverage_hours_by_asset"] !=
               scanned["live_original_put_arrival_hours_by_asset"]):
        raise ValueError("INDEPENDENT_ORIGINAL_DAY_REPLAY_DISAGREEMENT")
    feasible = any(primary.values())
    return {
        "schema": SCHEMA, "source_day": DAY.isoformat(),
        "decision_utc": "2022-01-24T00:00:00+00:00",
        "status": "SOURCE_FEASIBLE_ONLY_NOT_ECONOMICS" if feasible else "SOURCE_VETO_NOT_LOSS",
        "fixture": fixture, "original_gzip_sha256": scanned["sha256"],
        "external_sha256_matched": expected_sha256 is not None,
        "vendor_completeness_attested": False,
        "written_license_legally_verified": False,
        "original_quote_rows": rows,
        "source_hour_coverage": scanned["live_original_put_arrival_hours_by_asset"],
        "fresh_synchronized_two_strike_pairs_by_asset": primary,
        "latest_invalid_books_by_asset": invalid,
        "latest_stale_books_by_asset": stale,
        "independent_original_byte_replay_passed": True,
        "source_feasible_only": feasible,
        "historical_native_fees_margin_delivery_verified": False,
        "certified_lifecycles": 0, "economic_train_executed": False,
        "roi_calculated": False, "validation_opened": False,
        "holdout_opened": False, "promotion_authorized": False,
        "orders_enabled": False, "paper_publication_authorized": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_day_gzip")
    p.add_argument("--license-evidence")
    p.add_argument("--expected-sha256", help="independently supplied vendor digest")
    args = p.parse_args()
    report = inspect(args.original_day_gzip, license_evidence=args.license_evidence,
                     expected_sha256=args.expected_sha256)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
