#!/usr/bin/env python3
"""V98 Independent Phase206 transport-v2: realized Binance USD-M funding history.

Official Binance archive transport only. Training data is strictly < 2026-01-01 UTC.
No signal/returns/PnL are computed here.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]
START_YEAR, START_MONTH = 2022, 1
END_YEAR, END_MONTH = 2025, 12
END_EXCLUSIVE_MS = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
BASE = "https://data.binance.vision/data/futures/um/monthly/fundingRate"
OUT = Path("research/v98_independent/data/phase206_funding")
UA = "CryptoAI-Lab-V98-Independent-Phase206-Archive/1.0"


def months():
    y, m = START_YEAR, START_MONTH
    while (y, m) <= (END_YEAR, END_MONTH):
        yield y, m
        m += 1
        if m == 13:
            y += 1
            m = 1


def fetch(url: str) -> bytes:
    last = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=60) as r:
                if getattr(r, "status", 200) != 200:
                    raise RuntimeError(f"HTTP {getattr(r, 'status', None)} {url}")
                return r.read()
        except Exception as exc:
            last = exc
            if attempt == 4:
                raise RuntimeError(f"archive transport failed: {url}: {type(exc).__name__}: {exc}") from exc
            time.sleep(min(2 ** attempt, 10))
    raise RuntimeError(str(last))


def checksum_expected(raw: bytes, expected_filename: str) -> str:
    text = raw.decode("utf-8-sig").strip()
    if not text:
        raise RuntimeError(f"empty CHECKSUM for {expected_filename}")
    parts = text.split()
    if len(parts) < 2:
        raise RuntimeError(f"invalid CHECKSUM payload for {expected_filename}: {text!r}")
    digest = parts[0].strip().lower()
    filename = parts[-1].lstrip("*./")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise RuntimeError(f"invalid checksum digest for {expected_filename}")
    if Path(filename).name != expected_filename:
        raise RuntimeError(f"checksum filename mismatch: {filename} != {expected_filename}")
    return digest


def parse_archive(blob: bytes, source_name: str):
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(csv_names) != 1:
            raise RuntimeError(f"expected one CSV in {source_name}; found {csv_names}")
        payload = zf.read(csv_names[0]).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(payload))
    if not reader.fieldnames:
        raise RuntimeError(f"missing CSV header in {source_name}")
    normalized = {str(x).strip().lower(): x for x in reader.fieldnames}
    required = {"calc_time", "funding_interval_hours", "last_funding_rate"}
    if set(normalized) != required:
        raise RuntimeError(f"unexpected funding schema in {source_name}: {reader.fieldnames}")
    rows = []
    for row in reader:
        ts = int(str(row[normalized["calc_time"]]).strip())
        interval = str(row[normalized["funding_interval_hours"]]).strip()
        rate = str(row[normalized["last_funding_rate"]]).strip()
        # Parse only for integrity; preserve source decimal text in canonical output.
        float(interval)
        float(rate)
        if ts >= END_EXCLUSIVE_MS:
            raise RuntimeError(f"holdout contamination in {source_name}: {ts}")
        rows.append((ts, interval, rate))
    if not rows:
        raise RuntimeError(f"empty funding archive {source_name}")
    return rows


def acquire_symbol(symbol: str):
    all_rows = []
    source_files = []
    for y, m in months():
        filename = f"{symbol}-fundingRate-{y:04d}-{m:02d}.zip"
        url = f"{BASE}/{symbol}/{filename}"
        checksum_url = url + ".CHECKSUM"
        checksum_raw = fetch(checksum_url)
        expected = checksum_expected(checksum_raw, filename)
        blob = fetch(url)
        actual = hashlib.sha256(blob).hexdigest()
        if actual != expected:
            raise RuntimeError(f"SHA256 mismatch {filename}: {actual} != {expected}")
        rows = parse_archive(blob, filename)
        all_rows.extend(rows)
        source_files.append({
            "file": filename,
            "url": url,
            "zip_sha256": actual,
            "checksum_sha256": hashlib.sha256(checksum_raw).hexdigest(),
            "rows": len(rows),
        })
    all_rows.sort(key=lambda x: x[0])
    timestamps = [x[0] for x in all_rows]
    if len(timestamps) != len(set(timestamps)):
        raise RuntimeError(f"duplicate funding timestamps {symbol}")
    if any(b <= a for a, b in zip(timestamps, timestamps[1:])):
        raise RuntimeError(f"non-monotonic funding {symbol}")
    if not timestamps or max(timestamps) >= END_EXCLUSIVE_MS:
        raise RuntimeError(f"invalid cutoff {symbol}")
    return all_rows, source_files


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "phase": "206",
        "namespace": "V98 Independent",
        "mode": "DATA_ACQUISITION_ONLY",
        "transport_amendment": "research/v98_independent/phase206_transport_amendment.md",
        "source": "Binance official Data Collection USD-M monthly fundingRate archive",
        "base_url": BASE,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "requested_start_month": "2022-01",
        "requested_end_month": "2025-12",
        "exclusive_cutoff_utc": "2026-01-01T00:00:00Z",
        "symbols": {},
        "integrity": {"holdout_opened": False, "alpha_or_pnl_computed": False},
    }
    for symbol in SYMBOLS:
        rows, source_files = acquire_symbol(symbol)
        p = OUT / f"{symbol}_funding.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["fundingTime_ms", "fundingTime_utc", "fundingRate", "fundingIntervalHours"])
            for ts, interval, rate in rows:
                w.writerow([
                    ts,
                    datetime.fromtimestamp(ts / 1000, timezone.utc).isoformat(),
                    rate,
                    interval,
                ])
        gaps = []
        for (a, _, _), (b, _, _) in zip(rows, rows[1:]):
            if b - a > 12 * 3600 * 1000:
                gaps.append({"from_ms": a, "to_ms": b, "hours": round((b - a) / 3600000, 3)})
        manifest["symbols"][symbol] = {
            "rows": len(rows),
            "first_ms": rows[0][0],
            "last_ms": rows[-1][0],
            "canonical_csv_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "gaps_gt_12h": gaps,
            "source_files": source_files,
        }
    canonical = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    (OUT / "manifest.json").write_text(canonical, encoding="utf-8")
    print(canonical)


if __name__ == "__main__":
    main()
