"""Read-only bounded CoinAPI Flat Files historical object inventory (NO DOWNLOADS).

This probes actual S3 object listings on three sealed TRAIN dates, never claims
BTC/ETH lifecycle coverage, venue/local execution receipts, or profitability.
CoinAPI docs: https://www.coinapi.io/products/flat-files/docs/estimation-guide
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import date

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


if __name__ == "__main__":
    print(json.dumps(probe(), sort_keys=True))
