"""Independent source-response oracle; no import of primary December probe."""
from __future__ import annotations

import base64
import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ASSETS = ("BTC-USDT-SWAP", "ETH-USDT-SWAP")
WINDOWS = (("2021-12-01", "2022-01-01"),
           ("2021-11-01", "2022-01-01"),
           ("2021-12-01", "2022-03-01"))
START, END = 1639008000000, 1640995200000
FLAGS = ("archive_original_bytes_authenticated",
         "historical_account_settled_funding_authenticated",
         "native_execution_fees_authenticated", "original_five_fold_source_eligible",
         "economic_train_executed", "roi_calculated", "promotion_authorized",
         "validation_opened", "holdout_opened", "orders_enabled")


def decode(row):
    payload = base64.b64decode(row["raw_base64"], validate=True)
    if hashlib.sha256(payload).hexdigest() != row["raw_sha256"]:
        raise ValueError("FIRST_PARTY_RAW_RESPONSE_HASH_MISMATCH")
    obj = json.loads(payload)
    if not isinstance(obj, dict) or obj.get("code") != "0" or not isinstance(obj.get("data"), list):
        raise ValueError("FORGED_FIRST_PARTY_RESPONSE")
    return obj


def verify(path):
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("schema") != "V99_R106_DEC2021_FIRSTPARTY_SOURCE_PROBE_V1":
        raise ValueError("INVALID_SOURCE_SCHEMA")
    if any(document.get(k) is not False for k in FLAGS):
        raise ValueError("FORGED_NATIVE_ECONOMICS_OR_HOLDOUT_AUTHORIZATION")
    listing = document.get("listing_probes")
    history = document.get("bounded_history_probes")
    if not isinstance(listing, list) or len(listing) != 6 or not isinstance(history, list) or len(history) != 2:
        raise ValueError("INCOMPLETE_FIXED_SOURCE_PROBES")
    found = False
    for row, (asset, (begin, end)) in zip(listing, (
        (asset, window) for asset in ASSETS for window in WINDOWS)):
        if (row.get("inst_id") != asset or row.get("begin") != begin
                or row.get("end_exclusive") != end):
            raise ValueError("ALTERED_PREREGISTERED_ARCHIVE_SCOPE")
        p = row.get("params", {})
        ms = lambda x: str(int(datetime.strptime(x, "%Y-%m-%d").replace(
            tzinfo=timezone.utc).timestamp() * 1000))
        if (p.get("module") != "3" or p.get("instType") != "SWAP"
                or p.get("instFamilyList") != asset.removesuffix("-SWAP")
                or p.get("dateAggrType") != "monthly"
                or p.get("begin") != ms(begin) or p.get("end") != ms(end)):
            raise ValueError("ALTERED_ARCHIVE_REQUEST")
        if row["status"] == "FIRST_PARTY_RESPONSE":
            obj = decode(row)
            names = set()
            for entry in obj["data"]:
                if not isinstance(entry, dict):
                    continue
                for group in entry.get("details", []):
                    if not isinstance(group, dict):
                        continue
                    for leaf in group.get("groupDetails", []):
                        if isinstance(leaf, dict):
                            name = leaf.get("filename")
                            if name == asset + "-fundingrates-2021-12.zip":
                                names.add(name)
            if row.get("literal_december_archive_filenames") != sorted(names):
                raise ValueError("DECEMBER_LISTING_MISMATCH")
            found |= bool(names)
        elif row["status"] == "UNKNOWN_TRANSPORT":
            if "raw_base64" in row or "literal_december_archive_filenames" in row:
                raise ValueError("UNVERIFIED_LISTING_MASQUERADE")
        else:
            raise ValueError("UNEXPECTED_ARCHIVE_PROBE_STATUS")
    for row, asset in zip(history, ASSETS):
        p = row.get("params", {})
        if (row.get("inst_id") != asset or p.get("instId") != asset
                or p.get("before") != str(START)
                or p.get("after") != str(END) or p.get("limit") != "100"):
            raise ValueError("ALTERED_TRAIN_ONLY_HISTORY_SCOPE")
        if row["status"] == "FIRST_PARTY_RESPONSE":
            obj = decode(row)
            stamps = set()
            for entry in obj["data"]:
                if not isinstance(entry, dict) or entry.get("instId") != asset:
                    raise ValueError("WRONG_ASSET_FUNDING_ROW")
                t = int(entry["fundingTime"])
                if not START <= t < END:
                    raise ValueError("SEALED_HISTORY_LEAK")
                try:
                    rate = Decimal(str(entry["fundingRate"]))
                except (InvalidOperation, KeyError, TypeError) as exc:
                    raise ValueError("INVALID_ORIGINAL_FUNDING_RATE") from exc
                if not rate.is_finite():
                    raise ValueError("NONFINITE_ORIGINAL_FUNDING_RATE")
                stamps.add(t)
            if row.get("december_original_api_rows") != len(stamps):
                raise ValueError("FORGED_DECEMBER_FUNDING_COUNT")
            found |= bool(stamps)
        elif row["status"] == "API_IGNORED_TRAIN_BOUNDS_DISCARDED":
            if "raw_base64" in row or row.get("december_original_api_rows") is not None:
                raise ValueError("OUT_OF_SCOPE_API_PAYLOAD_NOT_DISCARDED")
        elif row["status"] == "UNKNOWN_TRANSPORT":
            if "raw_base64" in row:
                raise ValueError("UNVERIFIED_HISTORY_MASQUERADE")
        else:
            raise ValueError("UNEXPECTED_HISTORY_PROBE_STATUS")
    expected = ("DECEMBER_ORIGINAL_RECEIPT_ROUTE_FOUND_UNVERIFIED" if found
                else "DECEMBER_SOURCE_NOT_ESTABLISHED")
    if document["status"] != expected:
        raise ValueError("FORGED_SOURCE_DECISION")
    return {"status": "INDEPENDENT_FIRST_PARTY_RESPONSE_SCOPE_AND_HASH_VERIFIED",
            "source_decision": expected, "fixed_listing_probes": 6,
            "fixed_bounded_history_probes": 2,
            "native_economics_authorized": False, "promotion_authorized": False}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_dec2021_source_oracle OUT_JSON")
    print(json.dumps(verify(sys.argv[1]), sort_keys=True))
