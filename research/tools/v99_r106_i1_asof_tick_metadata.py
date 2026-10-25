"""Read-only V99 I1 historical Deribit tick-size metadata drift screen.

Uses original first-party 2026-fetched expired-instrument bytes from the archived
TRAIN-only artifact. Retrospective API fields are NOT as-of trade rules.
No market prices, strategy, economic TRAIN, validation, holdout, or orders.
"""
import gzip
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

START, END = 1639008000000, 1696118400000
CHANGE_DAY = int(datetime(2023, 7, 6, tzinfo=timezone.utc).timestamp() * 1000)
CHANGE_NEXT_DAY = CHANGE_DAY + 86_400_000


def normalize(value):
    if value is None:
        return "MISSING"
    try:
        return format(Decimal(str(value)).normalize(), "f")
    except Exception as exc:
        raise ValueError("INVALID_NATIVE_TICK") from exc


def aggregate(folder):
    from research.verification.independent_v99_r106_i1_historical_instruments import audit
    root = Path(folder)
    if not audit(root):
        raise ValueError("ORIGINAL_INSTRUMENT_ORACLE_FAILED")
    manifest = json.loads((root / "native_instrument_registry.json").read_text())
    report = {"schema": "V99_I1_RETROSPECTIVE_TICK_METADATA_SCREEN_V1",
              "historical_tick_grid_certified": False,
              "historical_native_lot_certified": False,
              "historical_fee_margin_certified": False,
              "source_asof_classification": "RETROSPECTIVE_API_NOT_ASOF_TERMS",
              "change_notice": "https://support.deribit.com/hc/en-us/articles/25944779257373-6-July-2023-TS",
              "change_day_utc": "2023-07-06",
              "original_sources": {}, "assets": {},
              "economic_train_executed": False, "validation_opened": False,
              "holdout_opened": False, "promotion_authorized": False,
              "orders_enabled": False}
    for asset in ("BTC", "ETH"):
        source = manifest["sources"][asset]
        raw = gzip.decompress((root / source["original_gzip"]).read_bytes())
        digest = hashlib.sha256(raw).hexdigest()
        if digest != source["original_raw_sha256"]:
            raise ValueError("ORIGINAL_SOURCE_HASH_MISMATCH")
        payload = json.loads(raw)
        bins = {name: {"count": 0, "tick_histogram": Counter(),
                       "tick_size_steps_present": 0, "tick_0_0001": 0,
                       "tick_0_0005": 0}
                for name in ("before_change", "change_day_uncertain", "after_change")}
        for row in payload["result"]:
            if row.get("kind") != "option" or row.get("option_type") != "put":
                continue
            expiry = int(row["expiration_timestamp"])
            if not START <= expiry < END:
                continue
            if row["instrument_name"].split("-")[0] != asset:
                raise ValueError("ASSET_MISMATCH")
            bucket = ("before_change" if expiry < CHANGE_DAY
                      else "change_day_uncertain" if expiry < CHANGE_NEXT_DAY
                      else "after_change")
            target = bins[bucket]
            target["count"] += 1
            tick = normalize(row.get("tick_size"))
            target["tick_histogram"][tick] += 1
            target["tick_size_steps_present"] += int(
                bool(row.get("tick_size_steps")))
            target["tick_0_0001"] += int(tick == "0.0001")
            target["tick_0_0005"] += int(tick == "0.0005")
        report["original_sources"][asset] = {
            "sha256": digest, "original_rows": len(payload["result"])}
        report["assets"][asset] = {name: {
            **{k: v for k, v in item.items() if k != "tick_histogram"},
            "tick_histogram": dict(sorted(item["tick_histogram"].items()))}
            for name, item in bins.items()}
        if sum(x["count"] for x in report["assets"][asset].values()) != source["train_puts"]:
            raise ValueError("TRAIN_PUT_COUNT_MISMATCH")
    return report


def main(folder, output):
    report = aggregate(folder)
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["source_asof_classification"],
        "counts": {a: {k: v["count"] for k, v in x.items()}
                   for a, x in report["assets"].items()},
        "historical_tick_grid_certified": False,
        "economic_train_executed": False, "promotion": False}))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_asof_tick_metadata ROOT OUTPUT")
    main(sys.argv[1], sys.argv[2])
