#!/usr/bin/env python3
"""HQ distinct, preregistered, source-only official spot mask protocol.

The older complete-grid spot source stays rejected. No PnL, holdout or trading.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import io
import json
import math
import time
import urllib.request
import zipfile
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
MONTHS = ((2022, 12),) + tuple((y, m) for y in (2023, 2024) for m in range(1, 13))
SOURCE = "https://data.binance.vision/data/spot/monthly/klines"
GAP = int(dt.datetime(2023, 3, 24, 13, tzinfo=dt.timezone.utc).timestamp() * 1000)
KNOWN_GAPS = {(a, GAP) for a in ASSETS}
PINNED_MARCH = {
    "BTCUSDT": "7f2afb8e0179a57ac31eab5205660298ba5eb77039ac2e21aef9b715ff3d06ce",
    "ETHUSDT": "90d268be1e0d39f7411f88ca3c0f21fe110fee7ff3c1dd054555e1fea6e22d8d",
    "BNBUSDT": "55bba490654b69c26cc1989f17902737535682f70491132f66246fbea3b7017a",
    "SOLUSDT": "7345fc8807e3e73e11595b5b371bf96d414048f77d1498964fa5c5f8fe3f02e7",
}
PINNED_100_SHA_MANIFEST = "02f1eef3fb3bd5a8a4f7ab7e60379474f091c961f9be98217b8b9792f75ef3a9"
PINNED_PARTIAL_CLOSE = {
    "BTCUSDT": 1679661581646,
    "ETHUSDT": 1679661583061,
    "BNBUSDT": 1679661581451,
    "SOLUSDT": 1679661586948,
}
PARTIAL_OPEN = GAP - 3600000

FIELDS = ("asset", "open_time_ms", "observed", "full_hour", "open", "high", "low", "close", "quote_volume")
OUT = Path(__file__).resolve().parent / "hq_gap_aware_spot_source_only"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def month_hours(y: int, m: int) -> list[int]:
    start = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc)
    end = dt.datetime(y + 1, 1, 1, tzinfo=dt.timezone.utc) if m == 12 else dt.datetime(y, m + 1, 1, tzinfo=dt.timezone.utc)
    return list(range(int(start.timestamp() * 1000), int(end.timestamp() * 1000), 3600000))


def parse_month(raw: bytes, asset: str, y: int, m: int) -> tuple[list[tuple[str, ...]], list[int]]:
    filename = f"{asset}-1h-{y}-{m:02d}.csv"
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = [n for n in archive.namelist() if not n.endswith("/")]
        if members != [filename]:
            raise ValueError("HQ_ZIP_MEMBER_MISMATCH " + filename)
        with archive.open(filename) as f:
            rows = list(csv.reader(io.TextIOWrapper(f, encoding="utf-8", newline="")))
    expected = month_hours(y, m)
    expected_set = set(expected)
    seen: dict[int, tuple[str, ...]] = {}
    prev = -1
    for row in rows:
        if len(row) != 12:
            raise ValueError("HQ_SPOT_SCHEMA " + filename)
        t = int(row[0])
        if t not in expected_set or t <= prev:
            raise ValueError("HQ_SPOT_UTC_OR_ORDER " + filename)
        prev = t
        if t in seen:
            raise ValueError("HQ_SPOT_DUPLICATE " + filename)
        close_time = int(row[6])
        pinned_partial = PINNED_PARTIAL_CLOSE[asset] if t == PARTIAL_OPEN else None
        if (close_time != (pinned_partial if pinned_partial is not None else t + 3599999)
                or close_time < t or close_time >= t + 3600000):
            raise ValueError("HQ_SPOT_CLOSE_TIME " + filename + " t=" + str(t) +
                             " observed_close=" + str(close_time))
        o, h, l, c, v, q, tb, tq = (float(row[i]) for i in (1, 2, 3, 4, 5, 7, 9, 10))
        trades = float(row[8])
        reserved = float(row[11])
        values = (o, h, l, c, v, q, tb, tq, trades, reserved)
        if (not all(math.isfinite(x) for x in values) or
                min(o, h, l, c) <= 0 or min(v, q, tb, tq, trades) < 0 or
                trades != int(trades) or reserved != 0 or
                l > min(o, c) or h < max(o, c) or h < l):
            raise ValueError("HQ_SPOT_GEOMETRY " + filename)
        tol = 1e-6 * max(1.0, q)
        taker_tol = 1e-6 * max(1.0, tq)
        sell_v, sell_q = v - tb, q - tq
        sell_tol = 1e-6 * max(1.0, abs(sell_q))
        if (q < v*l-tol or q > v*h+tol or
                tq < tb*l-taker_tol or tq > tb*h+taker_tol or
                tb > v + 1e-6*max(1.0, v) or tq > q + tol or
                sell_v < -1e-6*max(1.0, v) or sell_q < -tol or
                sell_q < sell_v*l-sell_tol or sell_q > sell_v*h+sell_tol or
                ((v == 0) != (q == 0)) or ((tb == 0) != (tq == 0))):
            raise ValueError("HQ_SPOT_VOLUME_CONSERVATION " + filename)
        seen[t] = (asset, str(t), "1", "0" if pinned_partial is not None else "1",
                   row[1], row[2], row[3], row[4], row[7])
    missing = sorted(expected_set - set(seen))
    if {(asset, t) for t in missing} != (KNOWN_GAPS & {(asset, t) for t in expected}):
        raise ValueError("HQ_UNEXPECTED_MISSINGNESS " + filename + " " + repr(missing))
    canonical = [seen[t] if t in seen else (asset, str(t), "0", "0", "", "", "", "", "") for t in expected]
    return canonical, missing


def window_valid(observed: list[bool], end: int, lookback: int) -> bool:
    """Completed-hour inclusive causal window over observed AND full-hour eligibility."""
    if lookback <= 0 or end < lookback - 1 or end >= len(observed):
        return False
    return all(observed[end - lookback + 1:end + 1])


def source_eligible_mask(rows: list[tuple[str, ...]]) -> list[bool]:
    """Only genuine 60-minute publisher bars are eligible for spot features."""
    return [row[2] == "1" and row[3] == "1" for row in rows]


def canonical_from_verified(cache: dict[tuple[str, int, int], bytes], checksums: dict[tuple[str, int, int], str]):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(FIELDS)
    receipts = []
    observed = 0
    partial = 0
    missing = []
    for asset in ASSETS:
        for y, m in MONTHS:
            key = (asset, y, m)
            raw = cache[key]
            sidecar = checksums[key].strip().split()
            filename = f"{asset}-1h-{y}-{m:02d}.zip"
            if (len(sidecar) != 2 or sidecar[1].lstrip("*") != filename):
                raise ValueError("HQ_PROVIDER_CHECKSUM_FILENAME " + str(key))
            expected = sidecar[0].lower()
            if len(expected) != 64 or any(x not in "0123456789abcdef" for x in expected):
                raise ValueError("HQ_PROVIDER_CHECKSUM_SCHEMA " + str(key))
            actual = sha(raw)
            if actual != expected:
                raise ValueError("HQ_PROVIDER_SHA_MISMATCH " + str(key))
            if (y, m) == (2023, 3) and actual != PINNED_MARCH[asset]:
                raise ValueError("HQ_PINNED_MARCH_SOURCE_CHANGED " + asset)
            lines, absent = parse_month(raw, asset, y, m)
            writer.writerows(lines)
            observed += len(lines) - len(absent)
            partial_in_month = sum(row[2] == "1" and row[3] == "0" for row in lines)
            partial += partial_in_month
            missing.extend((asset, t) for t in absent)
            receipts.append({"asset": asset, "month": f"{y}-{m:02d}", "sha256": actual,
                             "observed": len(lines) - len(absent), "masked": len(absent),
                             "partial_hour": partial_in_month})
    if set(missing) != KNOWN_GAPS or observed != 73148 or partial != 4 or len(receipts) != 100:
        raise ValueError("HQ_GLOBAL_COVERAGE_INTEGRITY")
    manifest = "".join(f'{r["asset"]}|{r["month"]}|{r["sha256"]}\n' for r in receipts).encode("utf-8")
    if sha(manifest) != PINNED_100_SHA_MANIFEST:
        raise ValueError("HQ_MANIFEST_PIN_MISMATCH")
    return stream.getvalue().encode("utf-8"), receipts


def get(url: str) -> bytes:
    error = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "V98-HQ-independent-source/1.0"})
            with urllib.request.urlopen(request, timeout=35) as response:
                if response.geturl().split("/")[2] != "data.binance.vision" or not response.geturl().startswith("https://"):
                    raise ValueError("HQ_PROVIDER_REDIRECT_ORIGIN")
                cap = 2048 if url.endswith(".CHECKSUM") else 12_000_000
                data = response.read(cap + 1)
            if not data or len(data) > cap:
                raise ValueError("HQ_EMPTY_OR_OVERSIZED_PROVIDER_OBJECT")
            return data
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError("HQ_SOURCE_UNAVAILABLE " + url + " " + repr(error))


def run():
    cache = {}
    checksums = {}
    for asset in ASSETS:
        for y, m in MONTHS:
            key = (asset, y, m)
            filename = f"{asset}-1h-{y}-{m:02d}.zip"
            url = f"{SOURCE}/{asset}/1h/{filename}"
            cache[key] = get(url)
            checksums[key] = get(url + ".CHECKSUM").decode("ascii")
            if sha(cache[key]) != checksums[key].strip().split()[0].lower():
                raise ValueError("HQ_DOWNLOAD_CHECKSUM " + filename)
            print("HQ_VERIFIED", filename, flush=True)
    a, receipts = canonical_from_verified(cache, checksums)
    b, other = canonical_from_verified(cache, checksums)
    if a != b or receipts != other:
        raise ValueError("HQ_NONDETERMINISTIC_CANONICAL")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "hq_spot_calendar_masked.csv").write_bytes(a)
    receipt = {"decision": "PASS_HQ_MASKED_SOURCE_ONLY_NOT_ECONOMIC",
               "publisher_checksums_verified": 100, "observed_asset_hours": 73148,
               "calendar_asset_hours": 73152, "masked_asset_hours": 4,
               "publisher_early_close_partial_asset_hours": 4,
               "eligible_full_hour_asset_hours": 73144,
               "partial_open_utc": "2023-03-24T12:00:00Z",
               "pinned_partial_close_ms": PINNED_PARTIAL_CLOSE,
               "missing_utc": "2023-03-24T13:00:00Z", "missing_assets": list(ASSETS),
               "canonical_sha256": sha(a), "canonical_bytes": len(a),
               "two_pass_identical": True, "archives": receipts,
               "publisher_manifest_sha256": PINNED_100_SHA_MANIFEST,
               "complete_grid_source_rejection_still_active": True,
               "validation_2025_read": False, "data_2026_read": False,
               "historical_system_pnl_computed": False, "alpha_selected": False,
               "external_benchmarks_used": False, "trading_authorized": False}
    (OUT / "hq_masked_source_receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print("HQ_SOURCE_ONLY_PASS", sha(a), flush=True)


if __name__ == "__main__":
    run()
