"""Bounded December 2021 OKX first-party SOURCE probe; no economic data or orders."""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "V99_R106_DEC2021_FIRSTPARTY_SOURCE_PROBE_V1"
ASSETS = ("BTC-USDT-SWAP", "ETH-USDT-SWAP")
WINDOWS = (("2021-12-01", "2022-01-01"),
           ("2021-11-01", "2022-01-01"),
           ("2021-12-01", "2022-03-01"))
EARLIEST = 1639008000000  # 2021-12-09 00:00 UTC
LATEST = 1640995200000    # 2022-01-01 00:00 UTC
MAX_BYTES = 250_000


def ms(day):
    return int(datetime.strptime(day, "%Y-%m-%d").replace(
        tzinfo=timezone.utc).timestamp() * 1000)


def request(path, params):
    url = "https://www.okx.com/api/v5/" + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": "CryptoAI-Lab-V99-TRAIN-only/1.0",
                      "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read(MAX_BYTES + 1)
            http = response.status
        if len(raw) > MAX_BYTES:
            return {"status": "UNKNOWN_TRANSPORT", "error": "OVERSIZED_RESPONSE"}
        obj = json.loads(raw)
        if not isinstance(obj, dict) or obj.get("code") != "0" or not isinstance(obj.get("data"), list):
            return {"status": "UNKNOWN_TRANSPORT", "error": "NON_SUCCESS_API_RESPONSE",
                    "http_status": http, "api_code": str(obj.get("code")) if isinstance(obj, dict) else None}
        return {"status": "FIRST_PARTY_RESPONSE", "http_status": http,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_base64": base64.b64encode(raw).decode("ascii")}
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeError) as exc:
        return {"status": "UNKNOWN_TRANSPORT", "error": type(exc).__name__}


def filenames(obj, inst):
    names = set()
    for item in obj["data"]:
        if not isinstance(item, dict):
            continue
        for group in item.get("details", []):
            if not isinstance(group, dict):
                continue
            for leaf in group.get("groupDetails", []):
                if not isinstance(leaf, dict):
                    continue
                name = leaf.get("filename")
                if name == inst + "-fundingrates-2021-12.zip":
                    names.add(name)
    return sorted(names)


def probe():
    listing = []
    history = []
    for inst in ASSETS:
        for begin, end in WINDOWS:
            params = {"module": "3", "instType": "SWAP",
                      "instFamilyList": inst.removesuffix("-SWAP"),
                      "dateAggrType": "monthly",
                      "begin": str(ms(begin)), "end": str(ms(end))}
            response = request("public/market-data-history", params)
            row = {"inst_id": inst, "begin": begin, "end_exclusive": end,
                   "params": params, **response}
            if response["status"] == "FIRST_PARTY_RESPONSE":
                obj = json.loads(base64.b64decode(response["raw_base64"]))
                row["literal_december_archive_filenames"] = filenames(obj, inst)
            listing.append(row)
        # Both bounds are explicitly TRAIN-only. If the API ignores either
        # bound, discard its payload rather than recording sealed market data.
        params = {"instId": inst, "before": str(EARLIEST),
                  "after": str(LATEST), "limit": "100"}
        response = request("public/funding-rate-history", params)
        row = {"inst_id": inst, "params": params, **response}
        if response["status"] == "FIRST_PARTY_RESPONSE":
            obj = json.loads(base64.b64decode(response["raw_base64"]))
            valid_scope = True
            clocks = []
            for entry in obj["data"]:
                if not isinstance(entry, dict) or entry.get("instId") != inst:
                    valid_scope = False
                    break
                try:
                    t = int(entry["fundingTime"])
                except (KeyError, ValueError, TypeError):
                    valid_scope = False
                    break
                if not EARLIEST <= t < LATEST:
                    valid_scope = False
                    break
                clocks.append(t)
            if not valid_scope:
                row.pop("raw_base64")
                row["status"] = "API_IGNORED_TRAIN_BOUNDS_DISCARDED"
                row["december_original_api_rows"] = None
            else:
                row["december_original_api_rows"] = len(set(clocks))
        history.append(row)
    found = any(r.get("literal_december_archive_filenames") for r in listing) or any(
        isinstance(r.get("december_original_api_rows"), int)
        and r["december_original_api_rows"] > 0 for r in history)
    return {"schema": SCHEMA,
            "status": ("DECEMBER_ORIGINAL_RECEIPT_ROUTE_FOUND_UNVERIFIED"
                       if found else "DECEMBER_SOURCE_NOT_ESTABLISHED"),
            "listing_probes": listing, "bounded_history_probes": history,
            "archive_original_bytes_authenticated": False,
            "historical_account_settled_funding_authenticated": False,
            "native_execution_fees_authenticated": False,
            "original_five_fold_source_eligible": False,
            "economic_train_executed": False, "roi_calculated": False,
            "promotion_authorized": False, "validation_opened": False,
            "holdout_opened": False, "orders_enabled": False}


def main(output):
    result = probe()
    Path(output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "december_listing_found": sum(bool(r.get("literal_december_archive_filenames"))
                                                   for r in result["listing_probes"]),
                      "december_api_rows": [r.get("december_original_api_rows")
                                            for r in result["bounded_history_probes"]],
                      "probe_statuses": [r["status"] for r in
                                         result["listing_probes"] + result["bounded_history_probes"]],
                      "economic_train_executed": False, "promotion_authorized": False},
                     sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_dec2021_firstparty_source_probe OUT_JSON")
    main(sys.argv[1])
