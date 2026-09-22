from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "reports" / "candidate_v99_r106_phase116_mark_index_data_audit.json"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
CDN = "https://data.binance.vision/"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
START = dt.date(2021, 12, 1)
END_EXCLUSIVE = dt.date(2024, 1, 18)
INTERVAL = "1h"
KINDS = ("markPriceKlines", "indexPriceKlines")


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-v99-r106-phase116"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def list_keys(prefix: str) -> list[str]:
    keys, token = [], None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        root = ET.fromstring(get(S3 + "?" + urllib.parse.urlencode(q)))
        keys += [n.text for n in root.findall("s3:Contents/s3:Key", NS) if n.text]
        if root.findtext("s3:IsTruncated", default="false", namespaces=NS).lower() != "true":
            break
        token = root.findtext("s3:NextContinuationToken", namespaces=NS)
        if not token:
            raise RuntimeError("truncated listing without continuation token")
    return keys


def parse_zip(raw: bytes, key: str) -> dict:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"crc {key}: {bad}")
        names = archive.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected zip member count {key}: {len(names)}")
        rows = list(csv.reader(io.TextIOWrapper(archive.open(names[0]), encoding="utf-8-sig")))
    if not rows:
        raise RuntimeError("empty " + key)
    if rows[0] and not rows[0][0].strip().lstrip("-").isdigit():
        rows = rows[1:]
    if not rows:
        raise RuntimeError("no data rows " + key)

    timestamps = []
    last = None
    for row in rows:
        if len(row) != 12:
            raise RuntimeError(f"kline row shape {key}: {len(row)}")
        try:
            ts = int(row[0])
            o, h, l, c = map(float, row[1:5])
        except (TypeError, ValueError) as exc:
            raise RuntimeError("parse " + key) from exc
        if not all(math.isfinite(x) for x in (o, h, l, c)):
            raise RuntimeError("nonfinite OHLC " + key)
        if last is not None and ts <= last:
            raise RuntimeError("nonmonotone/duplicate timestamp " + key)
        last = ts
        timestamps.append(ts)
    return {
        "rows": len(rows),
        "timestamps": timestamps,
        "first_timestamp": pd_iso(timestamps[0]),
        "last_timestamp": pd_iso(timestamps[-1]),
        "columns": 12,
    }


def pd_iso(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc).isoformat()


def verified(key: str) -> dict:
    raw = get(CDN + key)
    want = get(CDN + key + ".CHECKSUM").decode().split()[0]
    if hashlib.sha256(raw).hexdigest() != want:
        raise RuntimeError("sha256 " + key)
    return parse_zip(raw, key)


def verify_pair(job) -> dict:
    symbol, date, mark_key, index_key = job
    mark = verified(mark_key)
    index = verified(index_key)
    if mark["timestamps"] != index["timestamps"]:
        raise RuntimeError(f"timestamp misalignment {symbol} {date}")
    return {
        "symbol": symbol,
        "date": date.isoformat(),
        "mark_key": mark_key,
        "index_key": index_key,
        "rows": mark["rows"],
        "columns": mark["columns"],
        "timestamps_aligned": True,
        "first_timestamp": mark["first_timestamp"],
        "last_timestamp": mark["last_timestamp"],
    }


def main() -> None:
    assert (PROJECT / "research/v99_r106_phase116_mark_index_data_audit_prereg.md").exists()
    manifest = json.loads((PROJECT / "data/CANONICAL_MANIFEST_RESEARCH_PIT48.json").read_text())
    symbols = sorted(manifest["symbols"])

    def one(job):
        kind, symbol = job
        prefix = f"data/futures/um/daily/{kind}/{symbol}/{INTERVAL}/"
        found = []
        for key in list_keys(prefix):
            m = re.search(rf"/{re.escape(symbol)}-{INTERVAL}-(\d{{4}}-\d{{2}}-\d{{2}})\.zip$", key, re.I)
            if not m:
                continue
            date = dt.date.fromisoformat(m.group(1))
            if START <= date < END_EXCLUSIVE:
                found.append((date, key))
        return kind, symbol, sorted(found)

    jobs = [(kind, symbol) for kind in KINDS for symbol in symbols]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        listed = list(pool.map(one, jobs))

    by_kind = {kind: {} for kind in KINDS}
    key_maps = {kind: {} for kind in KINDS}
    for kind, symbol, files in listed:
        key_maps[kind][symbol] = dict(files)
        if not files:
            by_kind[kind][symbol] = {
                "observed_files": 0, "first": None, "last": None,
                "expected_files": 0, "missing_dates": [], "coverage_ratio": 0.0,
            }
            continue
        first, last = files[0][0], files[-1][0]
        observed = {d for d, _ in files}
        expected = [first + dt.timedelta(days=i) for i in range((last - first).days + 1)]
        missing = [d.isoformat() for d in expected if d not in observed]
        by_kind[kind][symbol] = {
            "observed_files": len(files), "first": first.isoformat(), "last": last.isoformat(),
            "expected_files": len(expected), "missing_dates": missing,
            "coverage_ratio": len(observed) / len(expected),
        }

    paired = {}
    samples = []
    for symbol in symbols:
        mark = key_maps["markPriceKlines"].get(symbol, {})
        index = key_maps["indexPriceKlines"].get(symbol, {})
        dates = sorted(set(mark) & set(index))
        if not dates:
            paired[symbol] = {
                "paired_files": 0, "first": None, "last": None,
                "expected_files": 0, "missing_dates": [], "coverage_ratio": 0.0,
            }
            continue
        first, last = dates[0], dates[-1]
        observed = set(dates)
        expected = [first + dt.timedelta(days=i) for i in range((last - first).days + 1)]
        missing = [d.isoformat() for d in expected if d not in observed]
        paired[symbol] = {
            "paired_files": len(dates), "first": first.isoformat(), "last": last.isoformat(),
            "expected_files": len(expected), "missing_dates": missing,
            "coverage_ratio": len(observed) / len(expected),
        }
        seen = set()
        for date in dates:
            q = (date.year, (date.month - 1) // 3 + 1)
            if q not in seen:
                seen.add(q)
                samples.append((symbol, date, mark[date], index[date]))

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        verified_pairs = list(pool.map(verify_pair, samples))

    out = {
        "study": "V99 R106 Phase116 — Binance USD-M mark/index paired-kline DATA AUDIT ONLY",
        "status": "DATA_AUDIT_COMPLETE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "train_start": START.isoformat(),
        "train_end_exclusive": END_EXCLUSIVE.isoformat() + "T00:00:00Z",
        "strict_boundary_policy": "daily archive date strictly before train_end; boundary-day archive excluded",
        "holdout_market_values_not_downloaded_or_parsed": True,
        "source": {
            "official_public_archive": True,
            "interval": INTERVAL,
            "mark": CDN + "data/futures/um/daily/markPriceKlines/<SYMBOL>/1h/",
            "index": CDN + "data/futures/um/daily/indexPriceKlines/<SYMBOL>/1h/",
        },
        "per_source": by_kind,
        "paired": paired,
        "summary": {
            "symbols": len(symbols),
            "symbols_with_mark_data": sum(v["observed_files"] > 0 for v in by_kind["markPriceKlines"].values()),
            "symbols_with_index_data": sum(v["observed_files"] > 0 for v in by_kind["indexPriceKlines"].values()),
            "symbols_with_paired_data": sum(v["paired_files"] > 0 for v in paired.values()),
            "mark_files": sum(v["observed_files"] for v in by_kind["markPriceKlines"].values()),
            "index_files": sum(v["observed_files"] for v in by_kind["indexPriceKlines"].values()),
            "paired_files": sum(v["paired_files"] for v in paired.values()),
            "paired_missing_dates": sum(len(v["missing_dates"]) for v in paired.values()),
            "integrity_pairs_verified": len(verified_pairs),
            "sample_rows_verified_each_side": sum(v["rows"] for v in verified_pairs),
            "timestamp_alignment_failures": 0,
            "row_columns": sorted({v["columns"] for v in verified_pairs}),
        },
        "integrity_sampling": {
            "method": "first paired admitted daily archive of every calendar quarter per canonical symbol",
            "checks": ["SHA256", "ZIP CRC", "12-column rows", "finite OHLC", "strict unique timestamps", "exact mark/index timestamp alignment"],
            "samples": verified_pairs,
        },
        "alpha_prohibited": True,
        "basis_values_computed": False,
        "return_relation_computed": False,
        "next_gate": "Assess temporal admissibility only. Any basis/dislocation alpha requires separate post-audit preregistration before PnL.",
        "disclosure": "No mark-index basis values, return relation, candidate PnL, regime selection, benchmark selection or holdout market values are computed in Phase116.",
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["summary"], indent=2))


if __name__ == "__main__":
    main()
