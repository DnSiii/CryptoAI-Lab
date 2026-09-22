from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "reports" / "candidate_v99_r106_phase112_premium_index_data_audit.json"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
CDN = "https://data.binance.vision/"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
INTERVAL = "1h"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-v99-r106-phase112"})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


def list_keys(prefix: str) -> list[str]:
    keys: list[str] = []
    token = None
    while True:
        query = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            query["continuation-token"] = token
        root = ET.fromstring(get(S3 + "?" + urllib.parse.urlencode(query)))
        keys += [node.text for node in root.findall("s3:Contents/s3:Key", NS) if node.text]
        truncated = root.findtext("s3:IsTruncated", default="false", namespaces=NS).lower() == "true"
        if not truncated:
            break
        token = root.findtext("s3:NextContinuationToken", namespaces=NS)
        if not token:
            raise RuntimeError("truncated listing without continuation token")
    return keys


def parse_rows(raw: bytes, key: str) -> tuple[int, int, str]:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"crc {key}: {bad}")
        names = archive.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected zip member count {key}: {len(names)}")
        rows = list(csv.reader(io.TextIOWrapper(archive.open(names[0]), encoding="utf-8-sig")))
    if not rows:
        raise RuntimeError(f"empty {key}")

    # Binance historical kline files may be headerless; tolerate a textual header but
    # validate the actual data rows deterministically.
    data_rows = rows
    if rows and rows[0] and not rows[0][0].strip().lstrip("-").isdigit():
        data_rows = rows[1:]
    if not data_rows:
        raise RuntimeError(f"no data rows {key}")

    timestamps: list[int] = []
    for row in data_rows:
        if len(row) != 12:
            raise RuntimeError(f"kline row shape {key}: {len(row)}")
        try:
            ts = int(row[0])
            vals = [float(row[i]) for i in (1, 2, 3, 4)]
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"parse {key}") from exc
        if not all(v == v and abs(v) != float("inf") for v in vals):
            raise RuntimeError(f"nonfinite OHLC {key}")
        timestamps.append(ts)
    if timestamps != sorted(timestamps) or len(timestamps) != len(set(timestamps)):
        raise RuntimeError(f"nonmonotone/duplicate timestamps {key}")

    first = dt.datetime.fromtimestamp(timestamps[0] / 1000, tz=dt.timezone.utc).isoformat()
    last = dt.datetime.fromtimestamp(timestamps[-1] / 1000, tz=dt.timezone.utc).isoformat()
    return len(data_rows), 12, first + " -> " + last


def verify(key: str) -> dict:
    raw = get(CDN + key)
    checksum = get(CDN + key + ".CHECKSUM").decode().split()[0]
    got = hashlib.sha256(raw).hexdigest()
    if got != checksum:
        raise RuntimeError(f"sha256 {key}")
    row_count, columns, span = parse_rows(raw, key)
    return {"key": key, "rows": row_count, "columns": columns, "timestamp_span": span}


def main() -> None:
    prereg = PROJECT / "research" / "v99_r106_phase112_premium_index_data_audit_prereg.md"
    assert prereg.exists(), "Phase112 preregistration missing"

    phase63 = json.loads((PROJECT / "reports" / "candidate_v99_r106_phase63_metrics_data_audit.json").read_text())
    assert phase63["status"] == "DATA_AUDIT_COMPLETE"
    assert phase63["holdout_not_listed_or_parsed"]
    train_end = dt.date.fromisoformat(phase63["train_end"])

    manifest = json.loads((PROJECT / "data" / "CANONICAL_MANIFEST_RESEARCH_PIT48.json").read_text())
    symbols = sorted(manifest["symbols"])

    def one(symbol: str):
        prefix = f"data/futures/um/daily/premiumIndexKlines/{symbol}/{INTERVAL}/"
        found = []
        for key in list_keys(prefix):
            m = re.search(rf"/{re.escape(symbol)}-{INTERVAL}-(\d{{4}}-\d{{2}}-\d{{2}})\.zip$", key, re.I)
            if not m:
                continue
            date = dt.date.fromisoformat(m.group(1))
            if date <= train_end:
                found.append((date, key))
        found.sort()
        return symbol, found

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        listed = list(pool.map(one, symbols))

    per_symbol = {}
    samples: list[str] = []
    for symbol, files in listed:
        if not files:
            per_symbol[symbol] = {
                "observed_files": 0,
                "first": None,
                "last": None,
                "expected_files": 0,
                "missing_dates": [],
                "coverage_ratio": 0.0,
            }
            continue

        first, last = files[0][0], files[-1][0]
        observed = {date for date, _ in files}
        expected = [first + dt.timedelta(days=i) for i in range((last - first).days + 1)]
        missing = [date.isoformat() for date in expected if date not in observed]
        per_symbol[symbol] = {
            "observed_files": len(files),
            "first": first.isoformat(),
            "last": last.isoformat(),
            "expected_files": len(expected),
            "missing_dates": missing,
            "coverage_ratio": len(observed) / len(expected),
        }

        seen_months = set()
        for date, key in files:
            ym = (date.year, date.month)
            if ym not in seen_months:
                seen_months.add(ym)
                samples.append(key)

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        verified = list(pool.map(verify, samples))

    out = {
        "study": "V99 R106 Phase112 — orthogonal Binance USD-M premiumIndexKlines DATA AUDIT ONLY",
        "status": "DATA_AUDIT_COMPLETE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "train_end": train_end.isoformat(),
        "holdout_not_listed_or_parsed": True,
        "source": {
            "listing": S3,
            "download": CDN + "data/futures/um/daily/premiumIndexKlines/<SYMBOL>/1h/",
            "official_public_archive": True,
            "interval": INTERVAL,
        },
        "symbols": per_symbol,
        "summary": {
            "symbols": len(symbols),
            "symbols_with_data": sum(v["observed_files"] > 0 for v in per_symbol.values()),
            "observed_files": sum(v["observed_files"] for v in per_symbol.values()),
            "missing_dates": sum(len(v["missing_dates"]) for v in per_symbol.values()),
            "integrity_files_verified": len(verified),
            "sample_rows_verified": sum(v["rows"] for v in verified),
            "row_columns": sorted({v["columns"] for v in verified}),
        },
        "integrity_sampling": {
            "method": "first available archive of every calendar month per symbol, all <= train_end",
            "checks": ["SHA256", "ZIP CRC", "nonempty CSV", "12-column row shape", "parseable monotone unique open timestamps", "finite OHLC"],
            "samples": verified,
        },
        "alpha_prohibited": True,
        "return_relation_computed": False,
        "next_gate": "Review availability/integrity only. Any premium/basis alpha requires a separate post-audit preregistration before return/PnL evaluation.",
        "disclosure": "No holdout observation and no relation to returns, PnL, regimes, V99 or benchmark outcomes is computed in Phase112.",
    }

    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["summary"], indent=2))


if __name__ == "__main__":
    main()
