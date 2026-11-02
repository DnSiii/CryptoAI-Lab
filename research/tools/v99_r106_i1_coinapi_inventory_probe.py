"""Read-only bounded CoinAPI Flat Files historical object inventory (NO DOWNLOADS).

This probes actual S3 object listings on three sealed TRAIN dates, never claims
BTC/ETH lifecycle coverage, venue/local execution receipts, or profitability.
CoinAPI docs: https://www.coinapi.io/products/flat-files/docs/estimation-guide
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import date, datetime, timedelta, timezone

DATES = ("2021-12-12", "2022-06-12", "2023-09-24")
ENDPOINT = "https://s3.flatfiles.coinapi.io"
BUCKET = "coinapi"


def probe(*, api_key=None, runner=subprocess.run):
    key = (os.getenv("COINAPI_API_KEY", "") if api_key is None else api_key).strip()
    report = {
        "schema": "V99_I1_COINAPI_READONLY_LISTING_V1",
        "status": "BLOCKED_NO_COINAPI_API_KEY",
        "provider": "CoinAPI", "dataset": "QUOTES", "venue": "DERIBIT",
        "dates": [], "full_2021_2023_coverage_certified": False,
        "btc_eth_lifecycle_certified": False,
        "quote_size_units_certified": False,
        "native_fee_margin_certified": False,
        "economic_train_executed": False, "promotion_authorized": False,
        "orders_enabled": False, "validation_opened": False,
        "holdout_opened": False,
    }
    if not key:
        return report
    env = os.environ.copy()
    env.update({
        "AWS_ACCESS_KEY_ID": key,
        "AWS_SECRET_ACCESS_KEY": "coinapi",  # CoinAPI public static S3 secret
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_EC2_METADATA_DISABLED": "true",
        "AWS_PAGER": "",
    })
    for day in DATES:
        assert date.fromisoformat(day) < date(2023, 10, 1)
        prefix = "T-QUOTES/D-" + day.replace("-", "") + "/E-DERIBIT/"
        args = [
            "aws", "s3api", "list-objects-v2", "--endpoint-url", ENDPOINT,
            "--bucket", BUCKET, "--prefix", prefix,
            "--max-keys", "10", "--no-paginate", "--output", "json",
        ]
        try:
            p = runner(args, env=env, capture_output=True, text=True, timeout=25,
                       check=False)
            if p.returncode:
                report["status"] = "BLOCKED_AUTH_OR_PROVIDER_LISTING_ERROR"
                report["dates"].append({"date": day, "status": "ERROR_REDACTED"})
                return report
            payload = json.loads(p.stdout)
            if not isinstance(payload, dict) or not isinstance(payload.get("IsTruncated"), bool):
                raise ValueError("INVALID_PROVIDER_LISTING")
            contents = payload.get("Contents", [])
            if not isinstance(contents, list) or len(contents) > 10:
                raise ValueError("INVALID_PROVIDER_CONTENTS")
            for obj in contents:
                if (not isinstance(obj, dict) or
                    not isinstance(obj.get("Key"), str) or
                    not obj["Key"].startswith(prefix) or
                    not isinstance(obj.get("Size"), int) or obj["Size"] < 0):
                    raise ValueError("UNBOUND_PROVIDER_OBJECT")
            report["dates"].append({
                "date": day, "status": "BOUNDED_LISTING_ONLY",
                "sample_objects": len(contents),
                "sample_bytes": sum(obj["Size"] for obj in contents),
                "more_objects_not_examined": payload["IsTruncated"],
            })
        except (OSError, ValueError, subprocess.TimeoutExpired, json.JSONDecodeError):
            report["status"] = "BLOCKED_UNVERIFIABLE_PROVIDER_RESPONSE"
            report["dates"].append({"date": day, "status": "ERROR_REDACTED"})
            return report
    report["status"] = "BOUNDED_LISTING_ONLY_NO_HISTORICAL_COVERAGE_PROOF"
    return report


# Fixed preregistered single-day source feasibility target, NOT an alpha grid.
TARGET_DAY = "2022-01-23"


def probe_target(*, api_key=None, runner=subprocess.run, max_pages=20):
    """Bounded S3 LIST of the exact ex-ante Sunday; never GET source bytes.

    Listing is a potentially billable provider operation. No key => no request.
    Even a complete object listing does not establish quote or economic coverage.
    """
    from research.tools.v99_r106_i1_coinapi_quote_intake import SOURCE_KEY, SYMBOL

    if type(max_pages) is not int or not 1 <= max_pages <= 20:
        raise ValueError("INVALID_BOUNDED_PAGE_LIMIT")
    key = (os.getenv("COINAPI_API_KEY", "") if api_key is None else api_key).strip()
    prefix = "T-QUOTES/D-20220123/E-DERIBIT/"
    report = {
        "schema": "V99_I1_FIXED_TARGET_COINAPI_LIST_ONLY_V1",
        "status": "BLOCKED_NO_COINAPI_API_KEY",
        "target_utc_day": TARGET_DAY,
        "next_original_decision_utc": "2022-01-24T00:00:00Z",
        "provider": "CoinAPI", "venue": "DERIBIT", "dataset": "QUOTES",
        "listing_complete": False, "pages_listed": 0,
        "objects_listed": 0, "compressed_bytes_listed": 0,
        "btc_put_files_listed": 0, "eth_put_files_listed": 0,
        "object_listing_not_quote_coverage": True,
        "original_24h_bbo_and_size_certified": False,
        "historical_license_and_fee_terms_certified": False,
        "economic_train_executed": False, "promotion_authorized": False,
        "orders_enabled": False, "validation_opened": False,
        "holdout_opened": False,
    }
    if not key:
        return report
    env = os.environ.copy()
    env.update({
        "AWS_ACCESS_KEY_ID": key,
        "AWS_SECRET_ACCESS_KEY": "coinapi",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_EC2_METADATA_DISABLED": "true",
        "AWS_PAGER": "",
    })
    seen_tokens, seen_keys = set(), set()
    # Predeclared Monday decision at 00:00 UTC, with Deribit 08:00 UTC expiry.
    # S3 object presence is a necessary inventory screen, NEVER a live BBO.
    entry = datetime(2022, 1, 24, tzinfo=timezone.utc)
    strikes_by_asset_expiry = {"BTC": {}, "ETH": {}}
    continuation = None
    for _ in range(max_pages):
        args = [
            "aws", "s3api", "list-objects-v2", "--endpoint-url", ENDPOINT,
            "--bucket", BUCKET, "--prefix", prefix, "--max-keys", "1000",
            "--no-paginate", "--output", "json",
        ]
        if continuation is not None:
            args += ["--continuation-token", continuation]
        try:
            process = runner(args, env=env, capture_output=True, text=True,
                             timeout=25, check=False)
            if process.returncode:
                report["status"] = "BLOCKED_AUTH_OR_PROVIDER_LISTING_ERROR"
                return report
            payload = json.loads(process.stdout)
            if (not isinstance(payload, dict)
                    or type(payload.get("IsTruncated")) is not bool):
                raise ValueError("MALFORMED_TARGET_LISTING")
            objects = payload.get("Contents", [])
            if not isinstance(objects, list) or len(objects) > 1000:
                raise ValueError("INVALID_TARGET_LISTING_OBJECTS")
            if payload["IsTruncated"] and not objects:
                raise ValueError("EMPTY_TRUNCATED_TARGET_LISTING")
            for item in objects:
                if not isinstance(item, dict):
                    raise ValueError("INVALID_TARGET_LISTING_OBJECT")
                name, size = item.get("Key"), item.get("Size")
                if (not isinstance(name, str) or not name.startswith(prefix)
                        or not name.endswith(".csv.gz")
                        or type(size) is not int or size < 0
                        or name in seen_keys):
                    raise ValueError("UNBOUND_DUPLICATE_OR_INVALID_TARGET_OBJECT")
                seen_keys.add(name)
                report["objects_listed"] += 1
                report["compressed_bytes_listed"] += size
                match = SOURCE_KEY.fullmatch(name)
                if match:
                    symbol = match.group(2).replace("__002D", "-")
                    if SYMBOL.fullmatch(symbol):
                        asset = symbol.split("-", 1)[0].lower()
                        report[asset + "_put_files_listed"] += 1
                        parts = symbol.split("-")
                        try:
                            expiry = datetime.strptime(parts[1], "%d%b%y").replace(
                                hour=8, tzinfo=timezone.utc)
                            strike = int(parts[2])
                        except (ValueError, OverflowError):
                            continue
                        if (strike > 0 and timedelta(days=28) <= expiry-entry
                                <= timedelta(days=35)):
                            asset_upper = asset.upper()
                            report["fixed_tenor_candidate_files_by_asset"][asset_upper] += 1
                            strikes_by_asset_expiry[asset_upper].setdefault(
                                expiry.isoformat(), set()).add(strike)
            report["pages_listed"] += 1
            if not payload["IsTruncated"]:
                report["listing_complete"] = True
                break
            next_token = payload.get("NextContinuationToken")
            if (not isinstance(next_token, str) or not next_token
                    or next_token in seen_tokens):
                raise ValueError("INVALID_TARGET_CONTINUATION_TOKEN")
            seen_tokens.add(next_token)
            continuation = next_token
        except (OSError, ValueError, TypeError, subprocess.TimeoutExpired):
            report["status"] = "BLOCKED_UNVERIFIABLE_TARGET_PROVIDER_LISTING"
            return report
    if not report["listing_complete"]:
        report["status"] = "BLOCKED_TARGET_LISTING_PAGE_CAP"
    else:
        for asset in ("BTC", "ETH"):
            report["fixed_tenor_two_strike_expiries_by_asset"][asset] = sum(
                len(strikes) >= 2 for strikes in strikes_by_asset_expiry[asset].values())
        report["fixed_tenor_pair_inventory_shown"] = all(
            report["fixed_tenor_two_strike_expiries_by_asset"][asset] > 0
            for asset in ("BTC", "ETH"))
        if report["fixed_tenor_pair_inventory_shown"]:
            report["status"] = "FIXED_TENOR_PAIR_OBJECTS_LISTED_NOT_QUOTES_OR_FILLS"
        elif report["btc_put_files_listed"] and report["eth_put_files_listed"]:
            report["status"] = "BTC_ETH_PUT_OBJECTS_BUT_NO_FIXED_TENOR_PAIR_PROOF"
        else:
            report["status"] = "TARGET_BTC_ETH_PUT_OBJECT_PRESENCE_NOT_SHOWN"
    return report


if __name__ == "__main__":
    print(json.dumps(probe(), sort_keys=True))
