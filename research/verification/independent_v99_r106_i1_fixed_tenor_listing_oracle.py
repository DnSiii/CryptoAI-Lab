"""Independent original-byte 28–35d I1 native listing oracle, no production imports."""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

EDGES = [1639008000000, 1650427200000, 1661850000000,
         1673272800000, 1684695600000, 1696118400000]
START_MONDAY = datetime(2021, 12, 13, tzinfo=timezone.utc)
DAY = 86_400_000


def verify(source_dir, signal_path, report_path):
    root = Path(source_dir)
    registry = json.loads((root/"native_instrument_registry.json").read_text())
    report = json.loads(Path(report_path).read_text())
    signal = json.loads(Path(signal_path).read_text())
    if (report.get("schema") != "V99_I1_FIRSTPARTY_FIXED_TENOR_LISTING_180_INTENTS_V1"
            or signal.get("schema") != "V99_I1_ORIGINAL_TRAIN_CAUSAL_30D_SIGNAL_V1"
            or signal.get("source_original") is not True
            or signal.get("observations") != 182
            or report.get("asset_week_intents") != 180
            or report.get("historical_option_lifecycles_certified") != 0):
        raise ValueError("ORACLE_FORGED_LISTING_OR_SIGNAL_REPORT")
    original = {}
    for asset in ("BTC", "ETH"):
        info = registry["sources"][asset]
        raw = gzip.decompress((root/info["original_gzip"]).read_bytes())
        if hashlib.sha256(raw).hexdigest() != info["original_raw_sha256"]:
            raise ValueError("ORACLE_ORIGINAL_DERIBIT_BYTES_HASH_MISMATCH")
        all_rows = json.loads(raw)["result"]
        if len(all_rows) != info["original_instruments"]:
            raise ValueError("ORACLE_ORIGINAL_INSTRUMENT_COUNT_MISMATCH")
        original[asset] = [r for r in all_rows if
                           r.get("kind") == "option" and r.get("option_type") == "put"]
    expected = []
    folds = {str(i): {"positive": 0, "listed_pairs": 0,
                       "positive_and_listed": 0, "positive_without_listing": 0}
             for i in range(1, 6)}
    for w in range(90):
        d = START_MONDAY + timedelta(weeks=w)
        clock = int(d.timestamp()*1000)
        fold = next((i for i in range(1,6)
                     if EDGES[i-1] <= clock < EDGES[i]), None)
        if fold is None:
            raise ValueError("ORACLE_FOLD_OUTSIDE_TRAIN")
        for j, asset in enumerate(("BTC", "ETH")):
            original_signal = signal["rows"][2*w+j]
            if (original_signal.get("decision_ms") != clock
                    or original_signal.get("asset") != asset
                    or original_signal.get("fold") != fold):
                raise ValueError("ORACLE_CAUSAL_INTENT_GRID_MISMATCH")
            by_expiry = defaultdict(set)
            for c in original[asset]:
                exp = c.get("expiration_timestamp")
                created = c.get("creation_timestamp")
                if (exp is None or created is None
                        or not created <= clock
                        or not 28*DAY <= exp-clock <= 35*DAY
                        or exp >= EDGES[-1]
                        or c.get("settlement_currency") != asset):
                    continue
                if any(c.get(k) is None or float(c[k]) <= 0 for k in
                       ("strike", "contract_size", "min_trade_amount", "tick_size")):
                    continue
                by_expiry[exp].add(float(c["strike"]))
            maximum = max((len(v) for v in by_expiry.values()), default=0)
            listed = maximum >= 2
            positive = original_signal["signal"] == "POSITIVE_EX_ANTE_PREMIUM"
            f = folds[str(fold)]
            f["positive"] += int(positive)
            f["listed_pairs"] += int(listed)
            f["positive_and_listed"] += int(positive and listed)
            f["positive_without_listing"] += int(positive and not listed)
            expected.append({
                "decision_ms": clock, "asset": asset, "fold": fold,
                "signal": original_signal["signal"],
                "max_same_expiry_native_put_strikes": maximum,
                "native_listed_pair_necessary_only": listed,
                "positive_signal_and_listed_pair": positive and listed,
            })
    if expected != report.get("rows") or folds != report.get("folds"):
        raise ValueError("ORACLE_ORIGINAL_FIXED_TENOR_LISTING_DISAGREEMENT")
    positive = sum(r["signal"]=="POSITIVE_EX_ANTE_PREMIUM" for r in expected)
    listed = sum(r["native_listed_pair_necessary_only"] for r in expected)
    intersection = sum(r["positive_signal_and_listed_pair"] for r in expected)
    no_list = positive-intersection
    zeros = [int(k) for k,v in folds.items() if v["positive_and_listed"]==0]
    if (report["positive_intents"] != positive or report["listed_pair_intents"] != listed
            or report["positive_and_listed_intents"] != intersection
            or report["positive_without_listing"] != no_list
            or report["zero_positive_listed_folds"] != zeros):
        raise ValueError("ORACLE_LISTING_COUNTS_DISAGREE")
    if any(report.get(k) is not False for k in (
            "native_fee_margin_index_authenticated", "economic_train_executed",
            "roi_calculated", "validation_opened", "holdout_opened",
            "orders_enabled", "promotion_authorized")):
        raise ValueError("ORACLE_FORGED_ECONOMIC_STATUS")
    return {"independent_original_raw_deribit_bytes_verified": True,
            "asset_week_intents": 180, "positive_intents": positive,
            "listed_pair_intents": listed,
            "positive_and_listed_intents": intersection,
            "positive_without_listing": no_list,
            "zero_positive_listed_folds": zeros,
            "source_only": True, "promotion_authorized": False}


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_fixed_tenor_listing_oracle REGISTRY_DIR ORIGINAL_SIGNAL_JSON REPORT_JSON")
    print(json.dumps(verify(*sys.argv[1:]), sort_keys=True))
