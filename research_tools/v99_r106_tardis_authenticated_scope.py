#!/usr/bin/env python3
"""Bounded authenticated Tardis Deribit OPTIONS entitlement probe.

A 200 HTML/login page or ignored Range is NOT an authenticated archive receipt.

No full historical download, trading, economics, validation, or holdout.
Do not mistake 200 responses for complete BTC+ETH or executable fills.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCOPE_URL = "https://api.tardis.dev/v1/api-key-info"
DATES = ("2021-12-12", "2022-06-12", "2023-09-24")
SCHEMA = "V99_I1_AUTHENTICATED_HISTORICAL_OPTIONS_ACCESS_PROBE_V1"


TRAIN_START = datetime(2021, 12, 9, tzinfo=timezone.utc)
TRAIN_END = datetime(2023, 10, 1, tzinfo=timezone.utc)


def _scope_covers_train(raw):
    """Check documented Tardis grant array, not a bare HTTP 200.

    A valid scope response is only a vendor entitlement claim, NOT original
    bytes, written licensing, executable BTC/ETH quote coverage or economics.
    """
    try:
        grants = json.loads(raw)
        if not isinstance(grants, list):
            return False
        for grant in grants:
            if not isinstance(grant, dict) or grant.get("exchange") != "deribit":
                continue
            start = datetime.fromisoformat(grant["from"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(grant["to"].replace("Z", "+00:00"))
            if start.tzinfo is None or end.tzinfo is None:
                continue
            if not (start <= TRAIN_START and end >= TRAIN_END):
                continue
            # A Deribit perpetuals-only grant may also have symbols=[].
            # Scope dates + symbol wildcard are insufficient to certify
            # options entitlement; the vendor's plan dimension is mandatory.
            plan = grant.get("dataPlan")
            if not isinstance(plan, str) or plan.strip().lower() not in {
                "options", "derivatives", "all-exchanges",
                "all_exchanges", "unlimited",
            }:
                continue
            symbols = grant.get("symbols")
            if not isinstance(symbols, list) or not all(isinstance(s, str) for s in symbols):
                continue
            # Empty means all symbols WITHIN the option-inclusive plan.
            # OPTIONS is the group covering all BTC/ETH option instruments.
            # A finite list with even one BTC and one ETH put DOES NOT cover
            # all expiry/strike combinations needed for 90 TRAIN weeks.
            if not symbols or "OPTIONS" in symbols:
                return True
    except (ValueError, TypeError, KeyError, OverflowError):
        return False
    return False


def _call(opener, key, url, method, ranged=False):
    headers = {"Authorization": "Bearer " + key,
               "User-Agent": "V99-I1-readonly-entitlement-probe/1.0"}
    if ranged:
        headers["Range"] = "bytes=0-1"
    request = urllib.request.Request(url, headers=headers, method=method)
    try:
        with opener(request, timeout=20) as response:
            status = int(response.status)
            if method == "GET" and ranged:
                # At most TWO bytes, never the full licensed archive.
                prefix = response.read(2)
                content_range = response.headers.get("Content-Range", "")
                import re
                match = re.fullmatch(r"bytes 0-1/([0-9]+)", content_range)
                bounded = status == 206 and match is not None and int(match[1]) >= 2
                gzip_magic = prefix == b"\x1f\x8b"
                return {"http": status, "nonempty": bool(prefix),
                        "bounded_206": bounded, "gzip_magic": gzip_magic}
            if method == "GET":
                if url == SCOPE_URL:
                    # Bounded scope metadata, never print response or API key.
                    scope_bytes = response.read(16_385)
                    return {"http": status,
                            "scope_claims_train_coverage": (
                                status == 200 and len(scope_bytes) <= 16_384
                                and _scope_covers_train(scope_bytes))}
                return {"http": status, "nonempty": bool(response.read(2))}
            return {"http": status, "nonempty": True}
    except urllib.error.HTTPError as exc:
        return {"http": int(exc.code), "nonempty": False}
    except (OSError, TimeoutError, ValueError) as exc:
        # Never include exception text: URLs/headers must not leak credentials.
        return {"http": None, "error_type": type(exc).__name__, "nonempty": False}


def check(key=None, opener=None):
    if key is None:
        key = os.environ.get("TARDIS_API_KEY", "")
    key = key.strip()
    opener = opener or urllib.request.urlopen
    result = {
        "schema": SCHEMA, "venue": "deribit", "data_type": "quotes",
        "symbol_group": "OPTIONS", "non_sample_dates": list(DATES),
        "source_entitlement_verified": False,
        "complete_2021_2023_archive_verified": False,
        "btc_eth_quote_coverage_verified": False,
        "entry_exit_lifecycle_verified": False,
        "native_fees_margin_verified": False,
        "economic_train_executed": False,
        "roi_calculated": False, "validation_opened": False,
        "holdout_opened": False, "orders_enabled": False,
        "promotion_authorized": False,
        "scope_endpoint_http": None, "scope_claims_train_coverage": False,
        "probes": [],
    }
    if not key:
        result["status"] = "BLOCKED_NO_AUTHENTICATED_ARCHIVE_KEY_CONFIGURED"
        result["next_dependency"] = (
            "Licensed 2021-12 through 2023-09 BTC+ETH options source "
            "and GitHub secret TARDIS_API_KEY, or verified alternative vendor"
        )
        return result
    scope = _call(opener, key, SCOPE_URL, "GET")
    result["scope_endpoint_http"] = scope["http"]
    result["scope_claims_train_coverage"] = scope.get(
        "scope_claims_train_coverage", False)
    if not result["scope_claims_train_coverage"]:
        result["status"] = "BLOCKED_UNVERIFIED_2021_2023_DERIBIT_OPTIONS_ENTITLEMENT"
        result["next_dependency"] = (
            "Documented Deribit BTC+ETH OPTIONS grant covering entire TRAIN "
            "2021-12-09..2023-09-30, plus authorized original archive bytes"
        )
        return result
    for day in DATES:
        year, month, dd = day.split("-")
        url = (f"https://datasets.tardis.dev/v1/deribit/quotes/"
               f"{year}/{month}/{dd}/OPTIONS.csv.gz")
        head = _call(opener, key, url, "HEAD")
        ranged = _call(opener, key, url, "GET", ranged=True)
        result["probes"].append({
            "date": day, "head_http": head["http"],
            "bounded_get_http": ranged["http"],
            "bounded_get_nonempty": ranged["nonempty"],
            "bounded_206": ranged.get("bounded_206", False),
            "gzip_magic": ranged.get("gzip_magic", False),
            "bounded_source_access_only": ranged.get("bounded_206", False)
                and ranged.get("gzip_magic", False),
        })
    all_access = (result["scope_claims_train_coverage"] and
                  all(p["bounded_source_access_only"] for p in result["probes"]))
    result["status"] = ("ACCESS_PROBE_ONLY_NOT_ARCHIVE_CERTIFIED" if all_access
                        else "BLOCKED_ENTITLEMENT_OR_HISTORICAL_SOURCE")
    result["next_dependency"] = (
        "Independently attributable complete BTC+ETH 2021-2023 BBO+sizes "
        "and both timestamps through 21-45d exits, gap manifest, historical "
        "account fees, native margin/liquidation and independent economic replay"
    )
    return result


def main():
    out = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(
        "tardis_quote_probe/authenticated_scope_probe.json")
    result = check()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    # The result intentionally contains no key, Authorization header or
    # unredacted api-key-info response.
    print(json.dumps(result, sort_keys=True))
    assert not result["promotion_authorized"]
    assert not result["economic_train_executed"]


if __name__ == "__main__":
    main()
