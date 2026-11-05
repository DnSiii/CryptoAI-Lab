#!/usr/bin/env python3
"""Acquire ONLY Phase243 Clean-4 Binance USD-M 1h monthly original archives.

Source-only: no alpha, no holdout, no PnL. Each original ZIP is accompanied
by the provider's .CHECKSUM receipt; absence/mismatch fails closed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import tempfile
import urllib.request
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
MONTHS = tuple(f"{y:04d}-{m:02d}" for y in range(2022, 2026)
               for m in range(1, 13) if (y, m) >= (2022, 12))
BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
MAX_ZIP_BYTES = 12_000_000

def _fetch(url: str, cap: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "V98-Independent-Source-Audit/1"})
    with urllib.request.urlopen(req, timeout=35) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError("SOURCE_REDIRECT_OR_STATUS_REFUSED")
        raw = response.read(cap + 1)
    if not raw or len(raw) > cap:
        raise ValueError("SOURCE_EMPTY_OR_OVERSIZE")
    return raw

def acquire(root: Path, *, limit: int | None = None) -> dict:
    root = Path(root)
    if "v98_independent" not in root.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    for p in (root.absolute(), *root.absolute().parents):
        if p.is_symlink():
            raise ValueError("SYMLINKED_ROOT")
    if root.exists() and not root.is_dir():
        raise ValueError("ROOT_NOT_DIRECTORY")
    receipts = {}
    jobs = [(a, m) for a in ASSETS for m in MONTHS]
    if limit is not None:
        if limit < 1:
            raise ValueError("LIMIT_MUST_BE_POSITIVE")
        jobs = jobs[:limit]
    for asset, month in jobs:
        name = f"{asset}-1h-{month}.zip"
        url = f"{BASE}/{asset}/1h/{name}"
        zip_path = root / "klines" / asset / "1h" / name
        checksum_path = zip_path.with_name(name + ".CHECKSUM")
        for p in (zip_path.parent, zip_path, checksum_path):
            if p.is_symlink():
                raise ValueError("SYMLINKED_OUTPUT")
        checksum = _fetch(url + ".CHECKSUM", 4096).decode("ascii").strip()
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?([^/\\\s]+)", checksum)
        if not match or match.group(2) != name:
            raise ValueError(f"PROVIDER_CHECKSUM_FORMAT_INVALID: {name}")
        expected = match.group(1).lower()
        if zip_path.exists():
            actual = hashlib.sha256(zip_path.read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError(f"EXISTING_ARCHIVE_CONFLICT: {name}")
        else:
            data = _fetch(url, MAX_ZIP_BYTES)
            actual = hashlib.sha256(data).hexdigest()
            if actual != expected:
                raise ValueError(f"PROVIDER_SHA256_MISMATCH: {name}")
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=zip_path.parent, prefix=".v98_source_", delete=False) as f:
                tmp = Path(f.name)
                try:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                except BaseException:
                    tmp.unlink(missing_ok=True)
                    raise
            try:
                if zip_path.exists():
                    raise FileExistsError("RACE_OUTPUT_EXISTS")
                os.link(tmp, zip_path)
            finally:
                tmp.unlink(missing_ok=True)
        if checksum_path.exists():
            if checksum_path.read_text().strip() != checksum:
                raise ValueError(f"EXISTING_CHECKSUM_CONFLICT: {name}")
        else:
            checksum_path.write_text(checksum + "\n")
        receipts[f"{asset}/{month}"] = {"sha256": expected, "url": url, "checksum_url": url + ".CHECKSUM"}
    return {"source_only": True, "promotion_eligible": False, "holdout_accessed": False,
            "assets": list(ASSETS), "months": len(MONTHS), "verified_archives": len(receipts),
            "receipts": receipts}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--limit", type=int, default=None, help="Bounded diagnostic, not full coverage")
    args = p.parse_args()
    print(json.dumps(acquire(args.archive_root, limit=args.limit), sort_keys=True))
