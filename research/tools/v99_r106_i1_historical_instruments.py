"""Read-only first-party Deribit expired BTC/ETH option instrument registry.
No executable quote, historical fee, margin, account fill, economics or orders.
Precommitted: research/V99_R106_I1_HISTORICAL_NATIVE_INSTRUMENT_REGISTRY_PREREG_20261024.md
"""
from __future__ import annotations
import gzip
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://history.deribit.com/api/v2/public/get_instruments"
START = 1639008000000
END = 1696118400000
FIELDS = ("instrument_name", "creation_timestamp", "expiration_timestamp",
          "strike", "option_type", "settlement_currency", "contract_size",
          "min_trade_amount", "tick_size")


def fetch_original(asset):
    url = BASE + "?" + urlencode({"currency": asset, "kind": "option", "expired": "true"})
    error = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"Accept": "application/json",
                    "User-Agent": "V99-native-contract-source-only/1.0"}), timeout=100) as resp:
                if resp.status != 200:
                    raise ValueError("HTTP_NOT_200")
                raw = resp.read(220_000_001)
            if len(raw) > 220_000_000:
                raise ValueError("SOURCE_RESPONSE_TOO_LARGE")
            data = json.loads(raw)
            if data.get("error") or not isinstance(data.get("result"), list):
                raise ValueError("SOURCE_RPC_OR_SCHEMA_ERROR:" + str(data.get("error")))
            return raw, data["result"]
        except Exception as exc:
            error = exc
            time.sleep(attempt + 1)
    raise RuntimeError("ORIGINAL_INSTRUMENT_SOURCE_UNAVAILABLE:" + asset + ":" + repr(error))


def filter_registry(rows, asset):
    out = []
    skipped = {"nonput": 0, "out_of_train": 0, "invalid_metadata": 0}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("NON_OBJECT_SOURCE_INSTRUMENT")
        if row.get("kind") != "option" or row.get("option_type") != "put":
            skipped["nonput"] += 1
            continue
        try:
            name = row["instrument_name"]
            expiry = int(row["expiration_timestamp"])
            created = int(row["creation_timestamp"])
        except (KeyError, ValueError, TypeError):
            skipped["invalid_metadata"] += 1
            continue
        if not START <= expiry < END:
            skipped["out_of_train"] += 1
            continue
        parts = name.split("-")
        if len(parts) != 4 or parts[0] != asset or parts[3] != "P":
            raise ValueError("INSTRUMENT_NAME_ASSET_OR_TYPE_MISMATCH:" + str(name))
        try:
            named_expiry = datetime.strptime(parts[1].upper(), "%d%b%y").replace(tzinfo=timezone.utc)
            named_strike = float(parts[2])
            native_strike = float(row["strike"])
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("BAD_STRIKE_OR_EXPIRY_ID:" + name) from exc
        if (named_expiry.date() != datetime.fromtimestamp(expiry/1000,timezone.utc).date()
                or not math.isfinite(native_strike) or native_strike <= 0
                or named_strike != native_strike or created > expiry):
            raise ValueError("INCONSISTENT_OR_NONCAUSAL_NATIVE_INSTRUMENT:" + name)
        out.append({k: row.get(k) for k in FIELDS})
    out.sort(key=lambda x: x["instrument_name"])
    if len({x["instrument_name"] for x in out}) != len(out):
        raise ValueError("DUPLICATE_INSTRUMENT_ID")
    return out, skipped


def main(dest):
    root = Path(dest)
    root.mkdir(parents=True, exist_ok=True)
    registry = {}
    sources = {}
    for asset in ("BTC", "ETH"):
        raw, rows = fetch_original(asset)
        path = root / ("deribit_" + asset.lower() + "_original_instruments.json.gz")
        with gzip.open(path, "wb", compresslevel=6) as f:
            f.write(raw)
        subset, skipped = filter_registry(rows, asset)
        missing = {key: sum(r.get(key) is None for r in subset) for key in FIELDS}
        sources[asset] = {"endpoint": BASE, "original_raw_sha256": hashlib.sha256(raw).hexdigest(),
                          "original_response_bytes": len(raw), "original_instruments": len(rows),
                          "train_puts": len(subset), "missing_native_fields": missing,
                          "skipped": skipped, "original_gzip": path.name,
                          "not_asof_fee_or_margin_attestation": True}
        registry[asset] = subset
        print(json.dumps({"asset": asset, **{k: sources[asset][k] for k in
                ("original_instruments","train_puts","missing_native_fields","skipped")}},
                sort_keys=True), flush=True)
    report = {"schema": "V99_I1_DERIBIT_HISTORICAL_INSTRUMENT_REGISTRY_V1",
              "source_classification": "FIRST_PARTY_ARCHIVED_METADATA_NOT_ASOF_TRADABILITY",
              "train_start_ms": START, "train_end_exclusive_ms": END,
              "sources": sources, "registry": registry,
              "economic_train_executed": False, "historical_fee_authenticated": False,
              "native_margin_liquidation_authenticated": False,
              "historical_executable_quotes_authenticated": False,
              "validation_opened": False, "holdout_opened": False,
              "promotion_authorized": False, "orders_enabled": False}
    (root / "native_instrument_registry.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("FIRST_PARTY_NATIVE_REGISTRY_ONLY / NO PNL / NO ORDERS / NO PROMOTION")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_historical_instruments OUT_DIR")
    main(sys.argv[1])
