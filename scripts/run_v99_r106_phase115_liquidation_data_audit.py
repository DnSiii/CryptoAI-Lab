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
OUT = PROJECT / "reports" / "candidate_v99_r106_phase115_liquidation_data_audit.json"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
CDN = "https://data.binance.vision/"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
START = dt.date(2021, 12, 1)
END_EXCLUSIVE = dt.date(2024, 1, 18)


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-v99-r106-phase115"})
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


def verify(key: str) -> dict:
    raw = get(CDN + key)
    want = get(CDN + key + ".CHECKSUM").decode().split()[0]
    if hashlib.sha256(raw).hexdigest() != want:
        raise RuntimeError("sha256 " + key)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"crc {key}: {bad}")
        names = archive.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected zip member count {key}: {len(names)}")
        reader = csv.reader(io.TextIOWrapper(archive.open(names[0]), encoding="utf-8-sig"))
        rows = list(reader)

    if not rows:
        raise RuntimeError("empty " + key)
    header = rows[0]
    body = rows[1:] if any(not c.replace("_", "").isalnum() or not c.replace("_", "").isdigit() for c in header) else rows
    # Public liquidation snapshots are headered in the historical archive; keep raw schema inventory.
    lower = [str(c).strip().lower() for c in header]
    time_idx = lower.index("time") if "time" in lower else None
    numeric_idx = [i for i, name in enumerate(lower) if any(k in name for k in ("qty", "quantity", "price"))]

    exact = set()
    duplicate_rows = 0
    parsed_times = 0
    numeric_checked = 0
    for row in body:
        tup = tuple(row)
        if tup in exact:
            duplicate_rows += 1
        else:
            exact.add(tup)

        if time_idx is not None and time_idx < len(row):
            try:
                val = row[time_idx].strip()
                if val:
                    x = float(val)
                    if not math.isfinite(x):
                        raise ValueError
                    parsed_times += 1
            except (TypeError, ValueError):
                raise RuntimeError("bad event time " + key)

        for i in numeric_idx:
            if i >= len(row) or not row[i].strip():
                continue
            try:
                x = float(row[i])
            except ValueError as exc:
                raise RuntimeError("bad numeric " + key) from exc
            if not math.isfinite(x) or x < 0:
                raise RuntimeError("nonfinite/negative numeric " + key)
            numeric_checked += 1

    return {
        "key": key,
        "header": header,
        "rows": len(body),
        "duplicate_rows_exact": duplicate_rows,
        "duplicate_ratio_exact": duplicate_rows / max(1, len(body)),
        "parsed_time_rows": parsed_times,
        "numeric_fields_checked": numeric_checked,
    }


def main() -> None:
    assert (PROJECT / "research/v99_r106_phase115_liquidation_data_audit_prereg.md").exists()
    manifest = json.loads((PROJECT / "data/CANONICAL_MANIFEST_RESEARCH_PIT48.json").read_text())
    symbols = sorted(manifest["symbols"])

    def one(symbol: str):
        prefix = f"data/futures/um/daily/liquidationSnapshot/{symbol}/"
        admitted = []
        all_zip = 0
        for key in list_keys(prefix):
            if key.endswith(".zip"):
                all_zip += 1
            m = re.search(rf"/{re.escape(symbol)}-liquidationSnapshot-(\d{{4}}-\d{{2}}-\d{{2}})\.zip$", key, re.I)
            if not m:
                continue
            date = dt.date.fromisoformat(m.group(1))
            if START <= date < END_EXCLUSIVE:
                admitted.append((date, key))
        return symbol, sorted(admitted), all_zip

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        listed = list(pool.map(one, symbols))

    per_symbol, samples = {}, []
    total_any_archive = 0
    for symbol, files, all_zip in listed:
        total_any_archive += all_zip
        if not files:
            per_symbol[symbol] = {
                "observed_files": 0, "first": None, "last": None,
                "expected_files": 0, "missing_dates": [], "coverage_ratio": 0.0,
                "all_current_zip_objects_any_date": all_zip,
            }
            continue
        first, last = files[0][0], files[-1][0]
        observed = {d for d, _ in files}
        expected = [first + dt.timedelta(days=i) for i in range((last - first).days + 1)]
        missing = [d.isoformat() for d in expected if d not in observed]
        per_symbol[symbol] = {
            "observed_files": len(files), "first": first.isoformat(), "last": last.isoformat(),
            "expected_files": len(expected), "missing_dates": missing,
            "coverage_ratio": len(observed) / len(expected),
            "all_current_zip_objects_any_date": all_zip,
        }
        seen = set()
        for date, key in files:
            q = (date.year, (date.month - 1) // 3 + 1)
            if q not in seen:
                seen.add(q)
                samples.append(key)

    observed_total = sum(v["observed_files"] for v in per_symbol.values())
    verified = []
    if samples:
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            verified = list(pool.map(verify, samples))

    schemas = {}
    for row in verified:
        h = tuple(row["header"])
        schemas[h] = schemas.get(h, 0) + 1

    status = "DATA_AUDIT_COMPLETE" if observed_total > 0 else "DATA_SOURCE_UNAVAILABLE"
    out = {
        "study": "V99 R106 Phase115 — Binance USD-M liquidationSnapshot DATA AVAILABILITY/INTEGRITY AUDIT ONLY",
        "status": status,
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "train_start": START.isoformat(),
        "train_end_exclusive": END_EXCLUSIVE.isoformat() + "T00:00:00Z",
        "holdout_market_values_not_downloaded_or_parsed": True,
        "source": {
            "listing": S3,
            "download": CDN + "data/futures/um/daily/liquidationSnapshot/<SYMBOL>/",
            "official_public_archive": True,
        },
        "symbols": per_symbol,
        "summary": {
            "symbols": len(symbols),
            "symbols_with_pretrain_data": sum(v["observed_files"] > 0 for v in per_symbol.values()),
            "observed_pretrain_files": observed_total,
            "current_zip_objects_any_date": total_any_archive,
            "missing_dates_within_observed_spans": sum(len(v["missing_dates"]) for v in per_symbol.values()),
            "integrity_files_verified": len(verified),
            "sample_rows_verified": sum(v["rows"] for v in verified),
            "sample_exact_duplicate_rows": sum(v["duplicate_rows_exact"] for v in verified),
            "schema_variants": len(schemas),
        },
        "schema_inventory": [{"header": list(h), "sample_files": n} for h, n in schemas.items()],
        "integrity_sampling": {
            "method": "first available admitted archive per calendar quarter per canonical symbol",
            "samples": verified,
        },
        "alpha_prohibited": True,
        "return_relation_computed": False,
        "substitution_prohibited": True,
        "next_gate": "If sufficient archive history exists for >=3 existing temporal folds, separately preregister one liquidation alpha. Otherwise close the family for R106.",
        "disclosure": "No third-party replacement dataset, no return relation and no post-train market-value archive content used.",
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["summary"], indent=2))


if __name__ == "__main__":
    main()
