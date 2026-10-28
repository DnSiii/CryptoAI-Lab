"""Local, resumable-in-place intake of licensed 661-day ORIGINAL Deribit option tapes.

This DOES NOT download, purchase, certify vendor completeness, certify fills,
or execute a strategy. Existing raw gzip files are never modified.
Preregistered in research/V99_R106_I1_661D_LOCAL_ORIGINAL_TAPE_IMPORT_PREREG_20261028.md.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

FIRST = date(2021, 12, 9)
END = date(2023, 10, 1)
DAYS = (END - FIRST).days
SCHEMA = "V99_I1_FIXED_28_35D_661_DAY_TRAIN_LIFECYCLE_TAPE_V1"
FIELDS = {"exchange", "symbol", "timestamp", "local_timestamp",
          "bid_price", "ask_price", "bid_amount", "ask_amount"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _day_file(root: Path, day: date) -> Path:
    p = root / (day.isoformat() + ".csv.gz")
    if not p.is_file() or p.is_symlink():
        raise ValueError("MISSING_OR_SYMLINKED_ORIGINAL_DAY:" + day.isoformat())
    return p


def scan_day(path: Path, day: date) -> dict:
    lower = int(datetime(day.year, day.month, day.day,
                         tzinfo=timezone.utc).timestamp() * 1_000_000)
    upper = lower + 86_400_000_000
    count = 0
    previous = -1
    qualifying_puts = {"BTC": 0, "ETH": 0}
    try:
        with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if not FIELDS.issubset(reader.fieldnames or []):
                raise ValueError("MISSING_ORIGINAL_QUOTE_COLUMNS:" + day.isoformat())
            for row in reader:
                count += 1
                if row["exchange"] != "deribit":
                    raise ValueError("WRONG_ORIGINAL_EXCHANGE:" + day.isoformat())
                try:
                    event, arrival = int(row["timestamp"]), int(row["local_timestamp"])
                except (ValueError, TypeError, OverflowError) as exc:
                    raise ValueError("INVALID_ORIGINAL_CLOCK:" + day.isoformat()) from exc
                if not (0 <= event <= arrival and lower <= arrival < upper
                        and previous <= arrival):
                    raise ValueError("NONCAUSAL_OR_OUT_OF_ORDER_CLOCK:" + day.isoformat())
                previous = arrival
                # A dated file with futures, only one coin, or zero-sized books
                # is NOT a complete two-asset options source inventory.
                # Invalid market rows are retained in the original bytes but
                # cannot qualify as necessary option-source evidence.
                parts = row["symbol"].split("-")
                if len(parts) != 4 or parts[0] not in qualifying_puts or parts[3] != "P":
                    continue
                try:
                    expiry = datetime.strptime(parts[1].upper(), "%d%b%y").date()
                    strike = float(parts[2])
                    bid, ask, bid_size, ask_size = (float(row[k]) for k in
                        ("bid_price", "ask_price", "bid_amount", "ask_amount"))
                except (ValueError, TypeError, OverflowError):
                    continue
                if (day < expiry <= day + timedelta(days=45)
                        and all(math.isfinite(v) and v > 0 for v in
                                (strike, bid, ask, bid_size, ask_size))
                        and bid < ask):
                    qualifying_puts[parts[0]] += 1
    except (OSError, EOFError, UnicodeError, csv.Error) as exc:
        raise ValueError("CORRUPT_ORIGINAL_GZIP:" + day.isoformat()) from exc
    if count == 0:
        raise ValueError("EMPTY_ORIGINAL_DAY:" + day.isoformat())
    for asset, n in qualifying_puts.items():
        if n == 0:
            raise ValueError("MISSING_QUALIFYING_ORIGINAL_PUT_QUOTES:"
                             + day.isoformat() + ":" + asset)
    return {"date": day.isoformat(), "file": path.name,
            "sha256": sha256(path), "rows": count,
            "qualifying_original_put_quote_rows_by_asset": qualifying_puts,
            # Self-declared from local import, NOT a vendor gap attestation.
            "complete_capture": True}


def build_manifest(root: Path, *, fixture: bool, license_evidence: Path | None = None) -> dict:
    root = Path(root)
    if type(fixture) is not bool:
        raise ValueError("INVALID_FIXTURE_FLAG")
    if not root.is_dir() or root.is_symlink():
        raise ValueError("MISSING_OR_UNSAFE_ORIGINAL_ROOT")
    manifest = root / "manifest.json"
    if manifest.exists() or manifest.is_symlink():
        raise ValueError("REFUSE_OVERWRITE_EXISTING_MANIFEST")
    if not fixture:
        if license_evidence is None:
            raise ValueError("NONFIXTURE_LICENSE_EVIDENCE_REQUIRED")
        evidence = Path(license_evidence)
        if not evidence.is_file() or evidence.is_symlink() or evidence.stat().st_size == 0:
            raise ValueError("MISSING_OR_UNSAFE_LICENSE_EVIDENCE")
        evidence_sha = sha256(evidence)
    else:
        if license_evidence is not None:
            raise ValueError("FIXTURE_MUST_NOT_CLAIM_LICENSE_EVIDENCE")
        evidence_sha = None
    dates = [FIRST + timedelta(days=i) for i in range(DAYS)]
    expected = {d.isoformat() + ".csv.gz" for d in dates}
    observed = {p.name for p in root.glob("*.csv.gz")}
    if observed != expected:
        raise ValueError("INCOMPLETE_OR_EXTRA_SEALED_ORIGINAL_DAYS:"
                         + str(len(expected-observed)) + "_missing_"
                         + str(len(observed-expected)) + "_extra")
    days = [scan_day(_day_file(root, d), d) for d in dates]
    return {"schema": SCHEMA, "venue": "deribit", "fixture": fixture,
            "train_start": FIRST.isoformat(), "train_end_exclusive": END.isoformat(),
            "days": days,
            "import_original_compressed_bytes_hashed": True,
            "source_manifest_self_declared_not_vendor_certified": True,
            "quote_content_presence_not_lifecycle_or_vendor_certified": True,
            "license_evidence_sha256_not_legal_verification": evidence_sha,
            "economic_train_executed": False, "validation_opened": False,
            "holdout_opened": False, "orders_enabled": False,
            "promotion_authorized": False}


def run(root: Path, *, fixture: bool, license_evidence: Path | None = None) -> dict:
    root = Path(root)
    manifest = build_manifest(root, fixture=fixture, license_evidence=license_evidence)
    target = root / "manifest.json"
    if target.exists() or target.is_symlink():
        raise ValueError("REFUSE_OVERWRITE_EXISTING_MANIFEST")
    # All 661 days validated BEFORE any manifest is published.
    descriptor, temporary = tempfile.mkstemp(prefix=".manifest.", suffix=".tmp", dir=root)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if target.exists() or target.is_symlink():
            raise ValueError("REFUSE_OVERWRITE_EXISTING_MANIFEST")
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(json.dumps({"status": "LOCAL_ORIGINAL_BYTE_MANIFEST_ONLY_NOT_ECONOMICS",
                      "fixture": fixture, "days": len(manifest["days"]),
                      "rows": sum(d["rows"] for d in manifest["days"]),
                      "vendor_gap_certified": False, "economic_train_executed": False,
                      "promotion_authorized": False}, sort_keys=True))
    return manifest


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4) or sys.argv[2] not in ("fixture", "nonfixture"):
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_local_tape_import ROOT fixture|nonfixture [LICENSE_EVIDENCE_FILE]")
    run(Path(sys.argv[1]), fixture=sys.argv[2] == "fixture",
        license_evidence=Path(sys.argv[3]) if len(sys.argv) == 4 else None)
