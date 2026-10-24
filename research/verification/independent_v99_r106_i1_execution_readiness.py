"""Independent byte-to-decision oracle for I1 partial source readiness. NO TRADES."""
from __future__ import annotations
import csv
import hashlib
import json
import shutil
import tempfile
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

START = datetime(2021, 12, 9, tzinfo=timezone.utc)
END = datetime(2023, 10, 1, tzinfo=timezone.utc)
FOLDS = [
    datetime(2021, 12, 9, tzinfo=timezone.utc),
    datetime(2022, 4, 20, 4, tzinfo=timezone.utc),
    datetime(2022, 8, 30, 9, tzinfo=timezone.utc),
    datetime(2023, 1, 9, 14, tzinfo=timezone.utc),
    datetime(2023, 5, 21, 19, tzinfo=timezone.utc),
    datetime(2023, 10, 1, tzinfo=timezone.utc),
]


def independently_verify(root, report_path):
    root = Path(root)
    report = json.loads(Path(report_path).read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    if report["schema"] != "V99_I1_ORIGINAL_SAMPLE_CAUSAL_EXECUTION_READINESS_V1":
        raise AssertionError("BAD_SCHEMA")
    if manifest["complete_train"] or manifest["asof_quote_coverage"]:
        raise AssertionError("FAKE_FULL_SOURCE")
    rows = []
    for item in manifest["days"]:
        b = (root / item["sample_file"]).read_bytes()
        if hashlib.sha256(b).hexdigest() != item["csv_sha256"]:
            raise AssertionError("ORIGINAL_SAMPLE_HASH_MISMATCH")
        with (root / item["sample_file"]).open(newline="") as fp:
            part = list(csv.DictReader(fp))
        if len(part) != item["rows_partial"]:
            raise AssertionError("ROW_COUNT")
        day = datetime.fromisoformat(item["date"]).replace(tzinfo=timezone.utc)
        lo = int(day.timestamp() * 1_000_000)
        for r in part:
            t = int(r["local_timestamp"])
            if not lo <= t < lo + 86_400_000_000:
                raise AssertionError("QUOTE_NOT_IN_ORIGINAL_DAY")
            rows.append(r)
    if len(rows) != 4000 or report["original_sample_rows"] != len(rows):
        raise AssertionError("ORIGINAL_SAMPLE_COUNT")
    # Recompute eligible quote groups independently from raw source bytes.
    coverage = {str(f): {"BTC": 0, "ETH": 0} for f in range(1, 6)}
    cursor = START
    n_decisions = 0
    eligible_count = 0
    censored = []
    while cursor < END:
        if cursor.weekday() == 0 and cursor.hour == 0:
            n_decisions += 1
            # Independent calendar maturity feasibility, no source-model import.
            # Strictly forbid any expiry in sealed validation.
            if cursor + timedelta(days=21) >= END:
                censored.append(cursor.isoformat())
                cursor += timedelta(hours=1)
                continue
            eligible_count += 1
            fold = next(i for i in range(1, 6) if FOLDS[i-1] <= cursor < FOLDS[i])
            cutoff_us = int(cursor.timestamp() * 1_000_000)
            books = defaultdict(set)
            for row in rows:
                arrival = int(row["local_timestamp"])
                exchange = int(row["timestamp"])
                if not exchange <= arrival <= cutoff_us or cutoff_us-arrival > 300_000_000:
                    continue
                parts = row["symbol"].split("-")
                if len(parts) != 4 or parts[0] not in ("BTC", "ETH") or parts[3] != "P":
                    continue
                try:
                    expiry = datetime.strptime(parts[1], "%d%b%y").replace(
                        hour=8, tzinfo=timezone.utc)
                    strike = float(parts[2])
                    bid, ask = float(row["bid_price"]), float(row["ask_price"])
                    bs, az = float(row["bid_amount"]), float(row["ask_amount"])
                except ValueError:
                    continue
                if not (21 <= (expiry-cursor).total_seconds()/86400 <= 45 and expiry < END):
                    continue
                if not (0 < bid < ask and bs > 0 and az > 0 and strike > 0):
                    continue
                books[(parts[0], expiry)].add(strike)
            for asset in ("BTC", "ETH"):
                if any(a == asset and len(strikes) >= 2
                       for (a, _), strikes in books.items()):
                    coverage[str(fold)][asset] += 1
        cursor += timedelta(hours=1)
    if n_decisions != 94 or n_decisions != report["train_decision_weeks"]:
        raise AssertionError("ORIGINAL_TRAIN_WEEK_COUNT")
    if eligible_count != 91 or len(censored) != 3:
        raise AssertionError("TRAIN_MATURITY_CALENDAR_MISMATCH")
    if (report["maturity_eligible_decision_weeks"] != eligible_count
            or report["right_censored_decision_weeks"] != len(censored)
            or report["right_censored_decision_utc"] != censored
            or report["required_asset_weekly_pairs"] != 2 * eligible_count):
        raise AssertionError("MATURITY_CENSORED_DENOMINATOR_MISMATCH")
    if coverage != report["five_fold_coverage"]:
        raise AssertionError("ORIGINAL_CAUSAL_FOLD_MISMATCH")
    if sum(sum(x.values()) for x in coverage.values()) != report["causal_two_strike_asset_weeks"]:
        raise AssertionError("ELIGIBLE_COUNT_MISMATCH")
    if any(report[k] for k in ("economic_train_executed", "validation_opened",
                               "holdout_opened", "orders_enabled", "promotion_authorized",
                               "complete_five_fold_coverage")):
        raise AssertionError("FORBIDDEN_PROMOTION_OR_FUTURE_ACCESS")
    # Negative control: a corrupted original quote byte must be rejected.
    from research.tools.v99_r106_i1_execution_readiness import verify_and_load
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp)
        shutil.copy2(root / "manifest.json", copy / "manifest.json")
        for item in manifest["days"]:
            shutil.copy2(root / item["sample_file"], copy / item["sample_file"])
        first = copy / manifest["days"][0]["sample_file"]
        first.write_bytes(first.read_bytes() + b"\n")
        try:
            verify_and_load(copy)
        except ValueError as exc:
            if "SOURCE_SHA_MISMATCH" not in str(exc):
                raise AssertionError("WRONG_NEGATIVE_CONTROL") from exc
        else:
            raise AssertionError("CORRUPTION_NOT_DETECTED")
    print(json.dumps({"status": "INDEPENDENT_ORIGINAL_SAMPLE_TO_WEEKLY_CAUSAL_COVERAGE_VERIFIED",
                      "source_rows": len(rows), "weekly_decisions": n_decisions,
                      "maturity_eligible_weeks": eligible_count,
                      "right_censored_weeks": len(censored),
                      "coverage": coverage, "negative_control": "PASS",
                      "economic_train": False, "promotion": False}, sort_keys=True))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_execution_readiness ROOT REPORT")
    independently_verify(sys.argv[1], sys.argv[2])
