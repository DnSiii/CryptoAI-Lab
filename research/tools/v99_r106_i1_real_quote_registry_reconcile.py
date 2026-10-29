"""One original public 2022-05-01 Deribit options day vs first-party expired registry.

Source-only, no strategy, fills, economics or sealed dates. Preregistered before
implementation in V99_R106_I1_REAL_QUOTE_VS_FIRSTPARTY_REGISTRY_RECONCILIATION_PREREG_20261028.md.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

URL = "https://datasets.tardis.dev/v1/deribit/quotes/2022/05/01/OPTIONS.csv.gz"
SHA = "e22d150bbe4e2cbe7c2230905f939b32e1bbbc73d94279258f699cd9e5948b0d"
ROWS = 4_253_565
CLOCK = int(datetime(2022, 5, 2, tzinfo=timezone.utc).timestamp() * 1000)
MIN_TENOR = 28 * 86_400_000
MAX_TENOR = 35 * 86_400_000
MAX_BYTES = 180_000_000


def original_registry(root: Path) -> dict:
    manifest = json.loads((root / "native_instrument_registry.json").read_text())
    if manifest.get("schema") != "V99_I1_DERIBIT_HISTORICAL_INSTRUMENT_REGISTRY_V1":
        raise ValueError("INVALID_ORIGINAL_REGISTRY_SCHEMA")
    by_asset = {}
    for asset in ("BTC", "ETH"):
        info = manifest["sources"][asset]
        raw = gzip.decompress((root / info["original_gzip"]).read_bytes())
        if hashlib.sha256(raw).hexdigest() != info["original_raw_sha256"]:
            raise ValueError("FIRSTPARTY_ORIGINAL_SHA_MISMATCH")
        response = json.loads(raw)["result"]
        if len(response) != info["original_instruments"]:
            raise ValueError("FIRSTPARTY_ORIGINAL_ROW_COUNT_MISMATCH")
        by_asset[asset] = {r["instrument_name"]: r for r in response
                           if r.get("kind") == "option" and r.get("option_type") == "put"}
    return by_asset


def download_original(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(URL, headers={"User-Agent": "V99-source-only-registry-reconcile/1.0"})
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(request, timeout=180) as response:
        if response.status != 200:
            raise ValueError("ORIGINAL_SAMPLE_HTTP_NOT_200")
        with path.open("xb") as target:
            while True:
                block = response.read(1 << 20)
                if not block:
                    break
                size += len(block)
                if size > MAX_BYTES:
                    raise ValueError("ORIGINAL_SAMPLE_TOO_LARGE")
                digest.update(block)
                target.write(block)
    if digest.hexdigest() != SHA:
        raise ValueError("ORIGINAL_SAMPLE_SHA_MISMATCH")


def symbol_contract(name: str):
    parts = name.split("-")
    if len(parts) != 4 or parts[0] not in ("BTC", "ETH") or parts[3] != "P":
        return None
    try:
        expiry = datetime.strptime(parts[1].upper(), "%d%b%y").replace(hour=8, tzinfo=timezone.utc)
        strike = float(parts[2])
    except (ValueError, OverflowError):
        return None
    if not math.isfinite(strike) or strike <= 0:
        return None
    return parts[0], int(expiry.timestamp() * 1000), strike


def run(path: Path, registry_dir: Path) -> dict:
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA:
        raise ValueError("ORIGINAL_SAMPLE_SHA_MISMATCH")
    reg = original_registry(registry_dir)
    symbols: dict[str, tuple[int, bool]] = {}
    rows = 0
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {"exchange", "symbol", "timestamp", "local_timestamp",
                    "bid_price", "ask_price", "bid_amount", "ask_amount"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("ORIGINAL_SAMPLE_FIELDS_MISSING")
        for row in reader:
            rows += 1
            if row["exchange"] != "deribit":
                raise ValueError("ORIGINAL_SAMPLE_WRONG_EXCHANGE")
            contract = symbol_contract(row["symbol"])
            if contract is None:
                continue
            try:
                arrival = int(row["local_timestamp"])
                venue = int(row["timestamp"])
                bid, ask, bs, a_s = (float(row[k]) for k in
                    ("bid_price", "ask_price", "bid_amount", "ask_amount"))
            except (ValueError, TypeError) as exc:
                raise ValueError("INVALID_ORIGINAL_ROW") from exc
            if not 0 <= venue <= arrival < CLOCK * 1000:
                raise ValueError("INVALID_ORIGINAL_ARRIVAL_CLOCK")
            valid = all(math.isfinite(v) and v > 0 for v in (bid, ask, bs, a_s)) and bid < ask
            previous = symbols.get(row["symbol"])
            if previous is None:
                symbols[row["symbol"]] = (arrival, valid)
            else:
                symbols[row["symbol"]] = (min(arrival, previous[0]), valid or previous[1])
    if rows != ROWS:
        raise ValueError("ORIGINAL_SAMPLE_ROW_COUNT_MISMATCH")
    stats = {a: defaultdict(int) for a in ("BTC", "ETH")}
    for symbol, (arrival, has_valid_bbo) in symbols.items():
        asset, expiry, strike = symbol_contract(symbol)
        record = reg[asset].get(symbol)
        fixed = MIN_TENOR <= expiry - CLOCK <= MAX_TENOR
        s = stats[asset]
        s["unique_quoted_put_symbols"] += 1
        s["valid_bbo_quoted_put_symbols"] += int(has_valid_bbo)
        s["fixed_28_35d_quote_symbols"] += int(fixed)
        s["fixed_28_35d_valid_bbo_symbols"] += int(fixed and has_valid_bbo)
        if record is None:
            s["quoted_symbols_missing_from_firstparty_registry"] += 1
            s["fixed_28_35d_symbols_missing_from_registry"] += int(fixed)
        else:
            s["quoted_symbols_present_in_firstparty_registry"] += 1
            if (int(record["expiration_timestamp"]) != expiry
                    or float(record["strike"]) != strike):
                raise ValueError("ORIGINAL_CONTRACT_IDENTITY_MISMATCH")
            if int(record["creation_timestamp"]) > arrival // 1000:
                s["firstparty_created_after_original_quote_arrival"] += 1
                s["fixed_created_after_quote_arrival"] += int(fixed)
    aggregate = {a: dict(sorted(s.items())) for a, s in stats.items()}
    # Zero-valued keys are material to independent audit and interpretation.
    keys = ("unique_quoted_put_symbols", "valid_bbo_quoted_put_symbols",
            "fixed_28_35d_quote_symbols", "fixed_28_35d_valid_bbo_symbols",
            "quoted_symbols_missing_from_firstparty_registry",
            "fixed_28_35d_symbols_missing_from_registry",
            "quoted_symbols_present_in_firstparty_registry",
            "firstparty_created_after_original_quote_arrival",
            "fixed_created_after_quote_arrival")
    aggregate = {a: {k: aggregate[a].get(k, 0) for k in keys} for a in ("BTC", "ETH")}
    contradicted = any(aggregate[a][k] for a in ("BTC", "ETH") for k in
                      ("quoted_symbols_missing_from_firstparty_registry",
                       "firstparty_created_after_original_quote_arrival"))
    return {"schema": "V99_I1_ORIGINAL_QUOTE_REGISTRY_RECONCILIATION_V1",
            "status": ("REGISTRY_COMPLETENESS_OR_CHRONOLOGY_FALSIFIED" if contradicted
                       else "SAMPLED_DAY_NO_REGISTRY_CONTRADICTION"),
            "source_day": "2022-05-01", "decision_day": "2022-05-02",
            "original_sample_sha256": SHA, "original_quote_rows": rows,
            "assets": aggregate, "source_only": True,
            "economic_train_executed": False, "roi_calculated": False,
            "validation_opened": False, "holdout_opened": False,
            "promotion_authorized": False, "orders_enabled": False,
            "historical_option_lifecycles_certified": 0}


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_real_quote_registry_reconcile SAMPLE_GZIP REGISTRY_DIR OUT_JSON")
    sample, root, out = map(Path, sys.argv[1:])
    if not sample.exists():
        download_original(sample)
    result = run(sample, root)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
