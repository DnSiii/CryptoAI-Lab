"""One-shot, READ-ONLY first-party OKX historical TRAIN availability attempt.

Never downloads or requests validation/holdout on purpose. Public GET only.
A successful HTTP response is NOT account-specific fee/fill provenance or PnL.
"""
from __future__ import annotations
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
HOST = "https://www.okx.com"
INSTRUMENTS = (
    ("BTC-USDT", "market/history-candles", "ts"),
    ("BTC-USDT-SWAP", "market/history-candles", "ts"),
    ("ETH-USDT", "market/history-candles", "ts"),
    ("ETH-USDT-SWAP", "market/history-candles", "ts"),
    ("BTC-USDT-SWAP", "public/funding-rate-history", "fundingTime"),
    ("ETH-USDT-SWAP", "public/funding-rate-history", "fundingTime"),
)


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_OKX_JSON_KEY")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("NONFINITE_OKX_JSON")


def fetch_public(inst, endpoint):
    if (inst, endpoint) not in {(x, y) for x, y, _ in INSTRUMENTS}:
        raise ValueError("UNAPPROVED_ENDPOINT")
    params = {"instId": inst, "after": str(END), "limit": "100"}
    if endpoint == "market/history-candles":
        params["bar"] = "1H"
    url = HOST + "/api/v5/" + endpoint + "?" + urlencode(params)
    request = Request(url, headers={
        "User-Agent": "CryptoAI-Lab-D1-TRAIN-only-source-probe/1.0",
        "Accept": "application/json",
    })
    for attempt in range(3):
        try:
            requested = datetime.now(timezone.utc).isoformat()
            with urlopen(request, timeout=25) as response:
                if response.status != 200 or response.geturl() != url:
                    raise ValueError("UNTRUSTED_HTTP_RESPONSE")
                raw = response.read(180001)
            received = datetime.now(timezone.utc).isoformat()
            if not raw or len(raw) > 180000:
                raise ValueError("INVALID_RESPONSE_LENGTH")
            return url, requested, received, raw
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == 2:
                raise ValueError("OKX_NETWORK_OR_HTTP_FAILURE:" + type(exc).__name__) from exc
            time.sleep(2 ** attempt)


def inspect_raw(raw, inst, endpoint, time_field):
    payload = json.loads(raw, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    if not isinstance(payload, dict) or payload.get("code") != "0" or not isinstance(payload.get("data"), list):
        raise ValueError("OKX_API_ERROR:" + str(payload.get("code") if isinstance(payload, dict) else "malformed"))
    rows = payload["data"]
    times = []
    actual_settlements = 0
    for row in rows:
        if endpoint == "market/history-candles":
            if not isinstance(row, list) or len(row) < 9 or row[8] != "1":
                raise ValueError("UNCONFIRMED_OR_MALFORMED_HISTORICAL_BAR")
            stamp = row[0]
        else:
            if not isinstance(row, dict) or row.get("instId") != inst:
                raise ValueError("FUNDING_INSTRUMENT_MISMATCH")
            stamp = row.get(time_field)
            if row.get("realizedRate") not in (None, ""):
                actual_settlements += 1
        if not isinstance(stamp, str) or not stamp.isdecimal():
            raise ValueError("INVALID_SOURCE_TIMESTAMP")
        ts = int(stamp)
        if ts >= END:
            raise ValueError("SEALED_PARTITION_RETURNED_BY_OKX")
        if ts < START:
            raise ValueError("OUTSIDE_PREREGISTERED_TRAIN")
        if endpoint == "market/history-candles" and ts % 3600000:
            raise ValueError("NONHOURLY_OKX_BAR")
        times.append(ts)
    if len(times) != len(set(times)):
        raise ValueError("DUPLICATE_HISTORICAL_SOURCE_TIMESTAMP")
    if times != sorted(times, reverse=True):
        raise ValueError("NONMONOTONIC_SOURCE_PAGE")
    return {
        "rows": len(rows),
        "oldest_ms": min(times) if times else None,
        "newest_ms": max(times) if times else None,
        "realized_rate_rows_not_account_cash": actual_settlements,
        "available_in_train": bool(times),
    }


def main():
    out = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("research_evidence/d1_train_probe")
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "D1_TRAIN_FIRST_PARTY_PUBLIC_AVAILABILITY_V1",
        "status": "DATA_ONLY_HOLD",
        "train_start_ms": START,
        "train_end_exclusive_ms": END,
        "validation_opened": False,
        "holdout_opened": False,
        "historical_economics_run": False,
        "promotion_authorized": False,
        "paper_publication_authorized": False,
        "orders_enabled": False,
        "account_native_fee_tier_authenticated": False,
        "account_settled_funding_cash_authenticated": False,
        "execution_fills_authenticated": False,
        "sources": {},
    }
    for idx, (inst, endpoint, time_field) in enumerate(INSTRUMENTS):
        key = ("candles_" if endpoint.startswith("market/") else "funding_") + inst
        try:
            url, requested, received, raw = fetch_public(inst, endpoint)
            # Inspect and reject sealed/out-of-range data before persisting raw.
            check = inspect_raw(raw, inst, endpoint, time_field)
            (out / (str(idx) + ".raw.json")).write_bytes(raw)
            result["sources"][key] = {
                "endpoint": url, "requested_utc": requested, "received_utc": received,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                **check,
            }
        except Exception as exc:
            result["sources"][key] = {"error": str(exc), "available_in_train": False}
        print(key, result["sources"][key], flush=True)
    available = sum(bool(v.get("available_in_train")) for v in result["sources"].values())
    result["first_party_train_sample_sources_available"] = available
    result["first_party_train_sample_sources_required"] = len(INSTRUMENTS)
    result["status"] = "TRAIN_SAMPLE_RETRIEVABLE_NOT_FULL_HISTORY" if available == 6 else "BLOCKED_NATIVE_HISTORICAL_SOURCE"
    (out / "manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("D1:", result["status"], available, "/6 first-party TRAIN sources; NO ECONOMICS", flush=True)
    # A blocked source attempt must not look like a green economic test.
    return 0 if available == 6 else 2


if __name__ == "__main__":
    sys.exit(main())
