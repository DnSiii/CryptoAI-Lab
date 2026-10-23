"""Acquire exact preregistered D1 TRAIN-only OKX BTC/ETH spot+swap 1H opens.

PUBLIC GET only, no orders, no sealed validation or holdout requests.
Persist original response bytes, page hashes, exact grid; never claim ROI.
Funding/fees/fills remain separate evidence and are NOT inferred from OHLC.
"""
from __future__ import annotations
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
STEP = 3600000
EXPECTED = (END - START) // STEP
INSTS = ("BTC-USDT", "BTC-USDT-SWAP", "ETH-USDT", "ETH-USDT-SWAP")
HOST = "https://www.okx.com"
MAX_PAGES = 200


def unique(pairs):
    obj = {}
    for key, val in pairs:
        if key in obj:
            raise ValueError("DUPLICATE_OKX_KEY")
        obj[key] = val
    return obj


def decimal_positive(value):
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("BAD_OKX_DECIMAL") from exc
    if not n.is_finite() or n <= 0:
        raise ValueError("BAD_OKX_PRICE")
    return n


def request_page(inst, cursor):
    if inst not in INSTS or not START < cursor <= END:
        raise ValueError("UNAPPROVED_INSTRUMENT_OR_TIME")
    url = HOST + "/api/v5/market/history-candles?" + urlencode({
        "instId": inst, "bar": "1H", "after": str(cursor), "limit": "100",
    })
    req = Request(url, headers={"User-Agent": "CryptoAI-Lab-D1-TRAIN-backfill/1.0",
                                "Accept": "application/json"})
    for retry in range(3):
        try:
            requested = datetime.now(timezone.utc).isoformat()
            with urlopen(req, timeout=25) as response:
                if response.status != 200 or response.geturl() != url:
                    raise ValueError("UNTRUSTED_OKX_RESPONSE")
                raw = response.read(200001)
            received = datetime.now(timezone.utc).isoformat()
            if not raw or len(raw) > 200000:
                raise ValueError("BAD_OKX_RESPONSE_LENGTH")
            return raw, {"url": url, "requested_utc": requested,
                         "received_utc": received,
                         "sha256": hashlib.sha256(raw).hexdigest()}
        except (HTTPError, URLError, TimeoutError) as exc:
            if retry == 2:
                raise ValueError("OKX_HTTP_OR_NETWORK:" + type(exc).__name__) from exc
            time.sleep(2 ** retry)


def decode_page(raw, cursor):
    def nonfinite(value):
        raise ValueError("NONFINITE_OKX_JSON")
    body = json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    if not isinstance(body, dict) or body.get("code") != "0" or not isinstance(body.get("data"), list):
        raise ValueError("OKX_API_REJECTED_PAGE")
    rows = body["data"]
    times = []
    parsed = {}
    for row in rows:
        if not isinstance(row, list) or len(row) < 9 or row[8] != "1":
            raise ValueError("BAD_OR_UNCONFIRMED_BAR")
        stamp = row[0]
        if not isinstance(stamp, str) or not stamp.isdecimal():
            raise ValueError("BAD_OKX_TIMESTAMP")
        ts = int(stamp)
        if ts >= cursor or ts >= END or ts % STEP:
            raise ValueError("SEALED_OR_NONCAUSAL_BAR")
        o, hi, lo, close = (decimal_positive(row[k]) for k in (1, 2, 3, 4))
        if lo > min(o, close) or hi < max(o, close):
            raise ValueError("INVALID_OHLC")
        if ts in parsed:
            raise ValueError("DUPLICATE_BAR_IN_PAGE")
        parsed[ts] = str(o)
        times.append(ts)
    if times != sorted(times, reverse=True):
        raise ValueError("UNSORTED_OKX_PAGE")
    return parsed, min(times) if times else None


def collect(inst, out):
    folder = out / inst
    folder.mkdir(parents=True, exist_ok=True)
    cursor = END
    seen = {}
    pages = []
    issue = None
    try:
        for page in range(MAX_PAGES):
            raw, meta = request_page(inst, cursor)
            parsed, earliest = decode_page(raw, cursor)
            filename = f"page_{page:04d}.raw.json"
            (folder / filename).write_bytes(raw)
            pages.append({"file": filename, **meta, "rows": len(parsed)})
            if earliest is None:
                issue = "OKX_ARCHIVE_EMPTY_BEFORE_TRAIN_START"
                break
            for stamp, op in parsed.items():
                if stamp < START:
                    continue
                if stamp in seen:
                    raise ValueError("DUPLICATE_BAR_ACROSS_PAGES")
                seen[stamp] = op
            if earliest <= START:
                break
            if earliest >= cursor:
                raise ValueError("PAGINATION_CURSOR_STALLED")
            cursor = earliest
            time.sleep(0.13)
        else:
            issue = "MAX_PAGES_EXHAUSTED"
    except Exception as exc:
        issue = str(exc)
    missing = [START + STEP * i for i in range(EXPECTED)
               if START + STEP * i not in seen]
    complete = issue is None and not missing and len(seen) == EXPECTED
    # Only timestamp+open; no modeled fills, positions or PnL.
    (folder / "train_opens.json").write_text(json.dumps(
        [{"ts": ts, "open": seen[ts]} for ts in sorted(seen)],
        separators=(",", ":")) + "\n")
    return {
        "instrument": inst, "pages": pages,
        "observed_hours": len(seen), "expected_hours": EXPECTED,
        "missing_hours": len(missing), "first_missing_ms": missing[0] if missing else None,
        "first_ms": min(seen) if seen else None,
        "last_ms": max(seen) if seen else None,
        "complete": complete, "issue": issue,
    }


def main():
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("research_evidence/d1_train_four_legs")
    root.mkdir(parents=True, exist_ok=True)
    results = {}
    for inst in INSTS:
        results[inst] = collect(inst, root)
        info = results[inst]
        print(inst, "hours", info["observed_hours"], "/", EXPECTED,
              "pages", len(info["pages"]), "issue", info["issue"],
              "missing", info["missing_hours"], flush=True)
    all_complete = all(x["complete"] for x in results.values())
    report = {
        "schema": "D1_FIRST_PARTY_HISTORICAL_FOUR_LEG_TRAIN_V1",
        "status": "FOUR_LEG_TRAIN_PRICES_CAPTURED_NOT_ECONOMICS" if all_complete
                  else "BLOCKED_INCOMPLETE_FIRST_PARTY_FOUR_LEG_TRAIN",
        "train_start_ms": START, "train_end_exclusive_ms": END,
        "expected_hours_per_instrument": EXPECTED,
        "instruments": results,
        "first_party_http_observation_not_exchange_signed": True,
        "historical_funding_available": False,
        "historical_fee_tier_authenticated": False,
        "account_fills_authenticated": False,
        "economic_trial_run": False, "validation_opened": False,
        "holdout_opened": False, "paper_publication_authorized": False,
        "orders_enabled": False, "promotion_authorized": False,
    }
    (root / "manifest.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["status"], flush=True)
    return 0 if all_complete else 2


if __name__ == "__main__":
    sys.exit(main())
