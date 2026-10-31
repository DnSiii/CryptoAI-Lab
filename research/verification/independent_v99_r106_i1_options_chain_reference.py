"""Independent raw-byte options-chain source oracle; never imports production scanner."""
import csv
import gzip
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

COLUMNS = {"exchange", "symbol", "timestamp", "local_timestamp",
           "type", "bid_price", "ask_price", "bid_amount", "ask_amount",
           "underlying_index", "underlying_price"}
LOW = int(datetime(2022, 6, 1, tzinfo=timezone.utc).timestamp() * 1_000_000)
HIGH = LOW + 24 * 60 * 60 * 1_000_000
VETO = ("native_spot_index_authenticated", "delivery_index_authenticated",
        "native_lot_size_authenticated", "native_fee_tier_authenticated",
        "full_661d_archive_authenticated", "economic_train_executed",
        "roi_calculated", "validation_opened", "final_holdout_opened",
        "freeze_authorized", "promotion_authorized",
        "paper_publication_authorized", "orders_enabled")


def verify(raw_path, report_path):
    path = Path(raw_path)
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if (report.get("schema") != "V99_I1_ORIGINAL_CHAIN_REFERENCE_SOURCE_V1"
            or report.get("status") != "SOURCE_ONLY_SAME_ROW_REFERENCE_NOT_SPOT_OR_SETTLEMENT"
            or report.get("day") != "2022-06-01"
            or report.get("source") != "TARDIS_DERIBIT_OPTIONS_CHAIN_PUBLIC_SAMPLE"
            or report.get("source_is_public_sample_not_complete_archive") is not True
            or report.get("index_may_be_synthetic_forward_not_spot") is not True
            or any(report.get(k) is not False for k in VETO)):
        raise ValueError("INDEPENDENT_CHAIN_UNTRUSTED_CERTIFICATION")
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            part = stream.read(1 << 20)
            if not part:
                break
            h.update(part)
    if (h.hexdigest() != report.get("original_compressed_sha256")
            or path.stat().st_size != report.get("original_compressed_bytes")):
        raise ValueError("INDEPENDENT_CHAIN_RAW_DIGEST_MISMATCH")
    tally = {coin: {"put_rows": 0, "valid_bbo_rows": 0,
                    "same_row_underlying_bbo_rows": 0,
                    "index_labels": {"SYN": 0, "OTHER": 0},
                    "hours": set()} for coin in ("BTC", "ETH")}
    n = 0
    last = -1
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not COLUMNS.issubset(reader.fieldnames or []):
            raise ValueError("INDEPENDENT_CHAIN_MISSING_COLUMNS")
        for item in reader:
            n += 1
            try:
                event = int(item["timestamp"])
                received = int(item["local_timestamp"])
            except (TypeError, ValueError) as exc:
                raise ValueError("INDEPENDENT_CHAIN_BAD_CLOCK") from exc
            if (item["exchange"] != "deribit" or event < 0
                    or not event <= received or not LOW <= received < HIGH
                    or received < last):
                raise ValueError("INDEPENDENT_CHAIN_NONCAUSAL")
            last = received
            bits = item["symbol"].split("-")
            if len(bits) != 4 or bits[0] not in tally or bits[-1] != "P" or item["type"] != "put":
                continue
            bucket = tally[bits[0]]
            bucket["put_rows"] += 1
            try:
                numbers = [float(item[k]) for k in
                           ("bid_price", "ask_price", "bid_amount", "ask_amount")]
                valid = (all(math.isfinite(x) for x in numbers)
                         and 0 < numbers[0] < numbers[1]
                         and numbers[2] > 0 and numbers[3] > 0)
            except (ValueError, TypeError):
                valid = False
            if not valid:
                continue
            bucket["valid_bbo_rows"] += 1
            label = item["underlying_index"].strip()
            try:
                underlying = float(item["underlying_price"])
            except (TypeError, ValueError):
                underlying = float("nan")
            if not label or not math.isfinite(underlying) or underlying <= 0:
                continue
            bucket["same_row_underlying_bbo_rows"] += 1
            bucket["index_labels"]["SYN" if label.startswith("SYN.") else "OTHER"] += 1
            bucket["hours"].add((received - LOW) // 3_600_000_000)
    if n == 0 or n != report.get("original_rows"):
        raise ValueError("INDEPENDENT_CHAIN_ROW_COUNT")
    for coin, observed in tally.items():
        expected = dict(observed)
        expected["same_row_arrival_hours"] = len(expected.pop("hours"))
        if expected != report.get("assets", {}).get(coin):
            raise ValueError("INDEPENDENT_CHAIN_METRIC_MISMATCH_" + coin)
    if set(report.get("assets", {})) != {"BTC", "ETH"}:
        raise ValueError("INDEPENDENT_CHAIN_ASSET_SCOPE")
    print(json.dumps({"status": "INDEPENDENT_ORIGINAL_CHAIN_BYTES_AND_REFERENCE_PASS",
                      "original_rows": n,
                      "same_row_bbo_index_rows": {k: v["same_row_underlying_bbo_rows"]
                                                  for k, v in tally.items()},
                      "spot_index_certified": False, "promotion_authorized": False},
                     sort_keys=True))
    return tally


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_options_chain_reference RAW REPORT")
    verify(sys.argv[1], sys.argv[2])
