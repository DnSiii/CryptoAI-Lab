"""Independent original-byte source-day procurement oracle; no primary imports."""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

START = datetime(2021, 12, 13, tzinfo=timezone.utc)
EDGES = [1639008000000,1650427200000,1661850000000,1673272800000,1684695600000,1696118400000]
DAY = 86_400_000


def verify(root_path, signal_path, result_path):
    root, signal_path = Path(root_path), Path(signal_path)
    report = json.loads(Path(result_path).read_text())
    original_bytes = signal_path.read_bytes()
    signal = json.loads(original_bytes)
    registry_bytes = (root/"native_instrument_registry.json").read_bytes()
    registry = json.loads(registry_bytes)
    if (signal.get("schema") != "V99_I1_ORIGINAL_TRAIN_CAUSAL_30D_SIGNAL_V1"
            or signal.get("source_original") is not True
            or signal.get("observations") != 182
            or len(signal.get("rows", [])) != 182
            or signal.get("economic_train_executed") is not False
            or registry.get("schema") != "V99_I1_DERIBIT_HISTORICAL_INSTRUMENT_REGISTRY_V1"
            or set(registry.get("sources", {})) != {"BTC","ETH"}):
        raise ValueError("UNVERIFIED_ORIGINAL_INPUT")
    puts = {}
    for asset in ("BTC", "ETH"):
        source = registry["sources"][asset]
        raw = gzip.decompress((root/source["original_gzip"]).read_bytes())
        if (hashlib.sha256(raw).hexdigest() != source["original_raw_sha256"]
                or len(raw) != source["original_response_bytes"]):
            raise ValueError("ORIGINAL_DERIBIT_HASH_MISMATCH")
        original = json.loads(raw)["result"]
        if len(original) != source["original_instruments"]:
            raise ValueError("ORIGINAL_DERIBIT_ROW_MISMATCH")
        puts[asset] = [row for row in original
                       if row.get("kind") == "option" and row.get("option_type") == "put"]
    possibilities = []
    positive_count = 0
    for week in range(90):
        monday = START + timedelta(weeks=week)
        ms = int(monday.timestamp()*1000)
        fold = next((i for i in range(1,6) if EDGES[i-1] <= ms < EDGES[i]), None)
        if fold is None:
            raise ValueError("ORIGINAL_FOLD_OUT_OF_RANGE")
        source_rows = signal["rows"][week*2:week*2+2]
        for j, asset in enumerate(("BTC", "ETH")):
            row = source_rows[j]
            if (row["decision_ms"] != ms or row["asset"] != asset
                    or row["fold"] != fold):
                raise ValueError("ORIGINAL_CAUSAL_SIGNAL_GRID_MISMATCH")
            positive_count += row["signal"] == "POSITIVE_EX_ANTE_PREMIUM"
        sunday = monday - timedelta(days=1)
        if sunday.day == 1:
            continue
        assets = []
        for j, asset in enumerate(("BTC","ETH")):
            if source_rows[j]["signal"] != "POSITIVE_EX_ANTE_PREMIUM":
                continue
            expiries = defaultdict(list)
            for row in puts[asset]:
                exp, created = row.get("expiration_timestamp"), row.get("creation_timestamp")
                if (exp is None or created is None or created > ms
                        or not 28*DAY <= exp-ms <= 35*DAY
                        or exp >= EDGES[-1] or row.get("settlement_currency") != asset):
                    continue
                if any(row.get(k) is None or float(row[k]) <= 0
                       for k in ("strike","contract_size","min_trade_amount","tick_size")):
                    continue
                expiries[exp].append(row)
            valid = []
            for expiry, rows in expiries.items():
                if len({float(row["strike"]) for row in rows}) >= 2:
                    valid.append((expiry, -len({float(row["strike"]) for row in rows}),
                                  sorted(row["instrument_name"] for row in rows)))
            if valid:
                expiry, _, symbols = min(valid)
                assets.append({
                    "asset": asset, "fold": fold,
                    "listed_expiry_utc": datetime.fromtimestamp(expiry/1000,timezone.utc).isoformat(),
                    "native_put_symbols_same_expiry": symbols,
                    "retrospective_listed_pair_only": True,
                })
        if assets:
            possibilities.append({
                "monday_decision_utc": monday.isoformat(),
                "sunday_source_date_utc": sunday.date().isoformat(),
                "fold": fold, "assets": assets,
            })
    if positive_count != 132:
        raise ValueError("ORIGINAL_SIGNAL_COUNT_CHANGED")
    possibilities.sort(key=lambda x: (-len(x["assets"]), x["monday_decision_utc"]))
    expected = possibilities[0] if possibilities else None
    if (report.get("schema") != "V99_I1_SINGLE_PRESELECTED_PAID_SOURCE_DAY_V1"
            or report.get("target") != expected
            or report.get("eligible_nonfree_mondays_count_audit_only") != len(possibilities)
            or report.get("original_signal_sha256") != hashlib.sha256(original_bytes).hexdigest()
            or report.get("original_registry_projection_sha256") != hashlib.sha256(registry_bytes).hexdigest()
            or report.get("source_registry_run") != 40148052668
            or report.get("source_signal_run") != 40326586848
            or report.get("status") != ("ONE_PRESELECTED_LICENSED_SAMPLE_REQUEST_NOT_RECEIVED"
                                       if expected else "NO_ELIGIBLE_TARGET_SOURCE_HOLD")):
        raise ValueError("INDEPENDENT_ORIGINAL_SOURCE_TARGET_DISAGREEMENT")
    for key in ("source_license_received","original_sunday_quotes_received",
                "original_executable_two_strike_books_certified",
                "historical_native_fee_tier_certified","economic_train_executed",
                "roi_calculated","validation_opened","holdout_opened",
                "orders_enabled","promotion_authorized"):
        if report.get(key) is not False:
            raise ValueError("FALSE_ECONOMIC_OR_LICENSE_CERTIFICATION")
    if report.get("historical_option_lifecycles_certified") != 0:
        raise ValueError("FORGED_CERTIFIED_OPTION_LIFECYCLES")
    return {"independent_original_byte_verified": True,
            "eligible_paid_source_mondays": len(possibilities),
            "target": expected, "economic_train_executed": False,
            "promotion_authorized": False}


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_one_day_procurement ROOT SIGNAL REPORT")
    print(json.dumps(verify(*sys.argv[1:]), sort_keys=True))
