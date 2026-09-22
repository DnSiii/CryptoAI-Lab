from __future__ import annotations

import concurrent.futures
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "reports" / "candidate_v99_r106_phase118_aggtrades_availability_audit.json"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
START = dt.date(2021, 12, 1)
END_EXCLUSIVE = dt.date(2024, 1, 18)
FOLDS = [
    ("F1", dt.date(2021, 12, 1), dt.date(2022, 6, 13)),
    ("F2", dt.date(2022, 6, 14), dt.date(2022, 12, 24)),
    ("F3", dt.date(2022, 12, 25), dt.date(2023, 7, 7)),
    ("F4", dt.date(2023, 7, 8), dt.date(2024, 1, 17)),
]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-v99-r106-phase118"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def list_objects(prefix: str) -> list[dict]:
    objects, token = [], None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        root = ET.fromstring(get(S3 + "?" + urllib.parse.urlencode(q)))
        for node in root.findall("s3:Contents", NS):
            key = node.findtext("s3:Key", default="", namespaces=NS)
            size = int(node.findtext("s3:Size", default="0", namespaces=NS))
            modified = node.findtext("s3:LastModified", default="", namespaces=NS)
            if key:
                objects.append({"key": key, "size": size, "last_modified": modified})
        if root.findtext("s3:IsTruncated", default="false", namespaces=NS).lower() != "true":
            break
        token = root.findtext("s3:NextContinuationToken", namespaces=NS)
        if not token:
            raise RuntimeError("truncated listing without continuation token")
    return objects


def one(symbol: str):
    prefix = f"data/futures/um/daily/aggTrades/{symbol}/"
    admitted = []
    any_zip = 0
    for obj in list_objects(prefix):
        key = obj["key"]
        if key.endswith(".zip"):
            any_zip += 1
        m = re.search(rf"/{re.escape(symbol)}-aggTrades-(\d{{4}}-\d{{2}}-\d{{2}})\.zip$", key, re.I)
        if not m:
            continue
        date = dt.date.fromisoformat(m.group(1))
        if START <= date < END_EXCLUSIVE:
            admitted.append((date, key, int(obj["size"]), obj["last_modified"]))
    admitted.sort()
    return symbol, admitted, any_zip


def main() -> None:
    assert (PROJECT / "research/v99_r106_phase118_aggtrades_availability_prereg.md").exists()
    manifest = json.loads((PROJECT / "data/CANONICAL_MANIFEST_RESEARCH_PIT48.json").read_text())
    symbols = sorted(manifest["symbols"])

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        listed = list(pool.map(one, symbols))

    per_symbol = {}
    date_sets = {}
    total_any_zip = 0
    for symbol, files, any_zip in listed:
        total_any_zip += any_zip
        dates = {d for d, _, _, _ in files}
        date_sets[symbol] = dates
        if not files:
            per_symbol[symbol] = {
                "observed_files": 0, "first": None, "last": None, "expected_files": 0,
                "missing_dates": [], "coverage_ratio": 0.0, "listed_compressed_bytes": 0,
                "current_zip_objects_any_date": any_zip,
            }
            continue
        first, last = files[0][0], files[-1][0]
        expected = [first + dt.timedelta(days=i) for i in range((last - first).days + 1)]
        missing = [d.isoformat() for d in expected if d not in dates]
        per_symbol[symbol] = {
            "observed_files": len(files),
            "first": first.isoformat(),
            "last": last.isoformat(),
            "expected_files": len(expected),
            "missing_dates": missing,
            "coverage_ratio": len(dates) / len(expected),
            "listed_compressed_bytes": sum(size for _, _, size, _ in files),
            "first_object_last_modified": files[0][3],
            "last_object_last_modified": files[-1][3],
            "current_zip_objects_any_date": any_zip,
        }

    fold_coverage = []
    for name, lo, hi in FOLDS:
        calendar_days = (hi - lo).days + 1
        counts = {}
        for symbol in symbols:
            counts[symbol] = sum(lo <= d <= hi for d in date_sets.get(symbol, set()))
        values = list(counts.values())
        fold_coverage.append({
            "fold": name,
            "start": lo.isoformat(),
            "end": hi.isoformat(),
            "calendar_days": calendar_days,
            "min_daily_files_per_symbol": min(values) if values else 0,
            "max_daily_files_per_symbol": max(values) if values else 0,
            "mean_daily_files_per_symbol": sum(values) / len(values) if values else 0,
            "symbols_with_at_least_5_daily_files": sum(v >= 5 for v in values),
        })

    folds_supported_all_symbols = sum(
        row["symbols_with_at_least_5_daily_files"] == len(symbols) for row in fold_coverage
    )

    out = {
        "study": "V99 R106 Phase118 — Binance USD-M raw aggTrades AVAILABILITY/PROVENANCE AUDIT ONLY",
        "status": "AVAILABILITY_AUDIT_COMPLETE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "train_start": START.isoformat(),
        "train_end_exclusive": END_EXCLUSIVE.isoformat() + "T00:00:00Z",
        "holdout_market_values_not_downloaded_or_parsed": True,
        "archive_content_downloaded": False,
        "source": {
            "listing": S3,
            "prefix": "data/futures/um/daily/aggTrades/<SYMBOL>/",
            "official_public_archive": True,
        },
        "symbols": per_symbol,
        "fold_coverage": fold_coverage,
        "summary": {
            "symbols": len(symbols),
            "symbols_with_pretrain_data": sum(v["observed_files"] > 0 for v in per_symbol.values()),
            "observed_pretrain_files": sum(v["observed_files"] for v in per_symbol.values()),
            "current_zip_objects_any_date": total_any_zip,
            "missing_dates_within_observed_spans": sum(len(v["missing_dates"]) for v in per_symbol.values()),
            "listed_compressed_bytes_pretrain": sum(v["listed_compressed_bytes"] for v in per_symbol.values()),
            "folds_supported_all_symbols_at_5day_availability_floor": folds_supported_all_symbols,
            "temporally_admissible_for_integrity_stage": folds_supported_all_symbols >= 3,
        },
        "metadata_only": True,
        "alpha_prohibited": True,
        "return_relation_computed": False,
        "next_gate": "If temporally admissible, run a separate deterministic content-integrity/ingestion audit before any raw-aggTrades alpha preregistration.",
        "disclosure": "Phase118 downloads no trade archive content and computes no market-value feature, alpha, return relation, PnL, regime or benchmark comparison.",
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"summary": out["summary"], "fold_coverage": fold_coverage}, indent=2))


if __name__ == "__main__":
    main()
