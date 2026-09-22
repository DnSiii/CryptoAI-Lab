from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import io
import json
import math
import time
import urllib.request
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "reports/candidate_v99_r106_phase119_aggtrades_integrity_probe.json"
BASE = "https://data.binance.vision/data/futures/um/daily/aggTrades"
DATES = ["2021-12-01", "2022-06-14", "2022-12-25", "2023-07-08"]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoAI-v99-r106-phase119"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def parse_bool(v: str) -> bool:
    x = v.strip().lower()
    if x not in {"true", "false"}:
        raise ValueError(f"invalid buyer-maker boolean: {v!r}")
    return x == "true"


def probe(symbol: str, date: str) -> dict:
    name = f"{symbol}-aggTrades-{date}.zip"
    url = f"{BASE}/{symbol}/{name}"
    t0 = time.monotonic()
    raw = get(url)
    checksum_text = get(url + ".CHECKSUM").decode("utf-8", errors="strict").strip()
    expected_sha = checksum_text.split()[0].lower()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != expected_sha:
        raise ValueError(f"SHA256 mismatch {name}")
    zf = zipfile.ZipFile(io.BytesIO(raw))
    bad_crc = zf.testzip()
    if bad_crc is not None:
        raise ValueError(f"ZIP CRC failed {name}:{bad_crc}")
    members = [x for x in zf.infolist() if not x.is_dir() and x.file_size > 0]
    if len(members) != 1:
        raise ValueError(f"expected one nonempty CSV member {name}, got {len(members)}")
    text = io.TextIOWrapper(zf.open(members[0]), encoding="utf-8-sig", newline="")
    reader = csv.reader(text)
    rows = iter(reader)
    first = next(rows, None)
    if first is None:
        raise ValueError(f"empty CSV {name}")
    headered = bool(first and first[0].strip().lower() in {"agg_trade_id", "aggtradeid", "a"})
    stream = rows if headered else iter([first, *rows])
    n = 0
    prev_id = None
    prev_ts = None
    for row in stream:
        if len(row) != 7:
            raise ValueError(f"unexpected field count {name}: {len(row)}")
        agg_id = int(row[0]); price = float(row[1]); qty = float(row[2])
        first_id = int(row[3]); last_id = int(row[4]); ts = int(row[5]); parse_bool(row[6])
        if not (math.isfinite(price) and price > 0 and math.isfinite(qty) and qty > 0):
            raise ValueError(f"nonpositive/nonfinite market value {name}")
        if first_id > last_id:
            raise ValueError(f"first_trade_id > last_trade_id {name}")
        if prev_id is not None and agg_id <= prev_id:
            raise ValueError(f"aggregate trade IDs not strictly increasing {name}")
        if prev_ts is not None and ts < prev_ts:
            raise ValueError(f"timestamps decreased {name}")
        prev_id, prev_ts = agg_id, ts
        n += 1
    if n == 0:
        raise ValueError(f"no data rows {name}")
    return {"symbol": symbol, "date": date, "rows": n, "compressed_bytes": len(raw), "sha256_verified": True,
            "zip_crc_verified": True, "headered": headered, "elapsed_seconds": time.monotonic() - t0}


def main() -> None:
    assert (PROJECT / "research/v99_r106_phase119_aggtrades_integrity_probe_prereg.md").exists()
    manifest = json.loads((PROJECT / "data/CANONICAL_MANIFEST_RESEARCH_PIT48.json").read_text())
    symbols = sorted(manifest["symbols"])
    targets = [(s, d) for s in symbols for d in DATES]
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda x: probe(*x), targets))
    elapsed = time.monotonic() - started
    out = {
        "study": "V99 R106 Phase119 — raw aggTrades deterministic integrity/throughput probe",
        "status": "INTEGRITY_PROBE_PASS",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "selection_scope": "train-only fixed fold-start sample",
        "sample_dates": DATES,
        "target_archives": len(targets),
        "archives_verified": len(results),
        "holdout_market_values_not_downloaded_or_parsed": True,
        "alpha_prohibited": True,
        "return_relation_computed": False,
        "checks": {"official_checksum_sha256": True, "zip_crc": True, "single_nonempty_csv": True,
                   "seven_fields": True, "positive_finite_price_qty": True, "first_id_lte_last_id": True,
                   "strictly_increasing_agg_id": True, "nondecreasing_timestamp": True, "buyer_maker_boolean": True},
        "resource": {"rows": sum(x["rows"] for x in results), "compressed_bytes": sum(x["compressed_bytes"] for x in results),
                     "wall_seconds": elapsed, "archives_per_second": len(results) / elapsed if elapsed else None},
        "per_archive": results,
        "next_gate": "PASS permits a separately preregistered train-only raw-microstructure hypothesis; no alpha inference is authorized by this probe.",
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ["status", "target_archives", "archives_verified", "resource"]}, indent=2))


if __name__ == "__main__":
    main()
