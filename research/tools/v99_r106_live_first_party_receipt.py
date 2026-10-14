"""R106 live as-of market receipt capture, DATA_ONLY, no orders or economics.

Captures FIRST-HAND HTTPS response bytes at a known GitHub-run time. Historical
exchange listing dates are NOT discovery receipts; only this prospective
observation can establish "observed at or before" and it is not an
exchange-signed attestation. Never backfill or rewrite published paper.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://fapi.binance.com"
ENDPOINTS = ("/fapi/v1/time", "/fapi/v1/exchangeInfo")
CORE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT")
LIMIT_BYTES = 2_000_000
MAX_SKEW_MS = 60_000
MAX_REQUEST_SECONDS = 30

def utc(value):
    if not isinstance(value, str):
        raise ValueError("explicit timestamp required")
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError("UTC timezone required")
    return t.astimezone(timezone.utc)

def stamp():
    return datetime.now(timezone.utc)

def iso(t):
    return t.astimezone(timezone.utc).isoformat()

def first_safe_decision(received):
    """Observation during UTC hour h cannot inform that hour's decision."""
    time = utc(received) if isinstance(received, str) else received.astimezone(timezone.utc)
    return iso(time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=2))

def http_get(path):
    """No auth, no write API, bounded first-party TLS download."""
    if not (path in ENDPOINTS or path.startswith("/fapi/v1/klines?symbol=")):
        raise ValueError("endpoint not allowlisted")
    url = BASE + path
    started = stamp()
    req = Request(url, headers={"User-Agent": "CryptoAI-R106-source-receipts/1.0", "Accept": "application/json"})
    with urlopen(req, timeout=MAX_REQUEST_SECONDS) as response:
        if response.status != 200:
            raise RuntimeError("non-200 source response: " + str(response.status))
        raw = response.read(LIMIT_BYTES + 1)
        headers = {x.lower(): response.headers.get(x) for x in ("Date", "Content-Type", "X-MBX-USED-WEIGHT-1M")}
    received = stamp()
    if not raw or len(raw) > LIMIT_BYTES:
        raise ValueError("empty or oversized source response")
    return {"url": url, "requested_utc": iso(started), "received_utc": iso(received),
            "duration_ms": round((received-started).total_seconds()*1000),
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "response_headers": headers, "raw": raw}

def decode(receipt):
    def unique(pairs):
        obj = {}
        for key, val in pairs:
            if key in obj:
                raise ValueError("duplicate first-party JSON key: "+key)
            obj[key] = val
        return obj
    def bad_constant(value):
        raise ValueError("non-finite source number: "+value)
    return json.loads(receipt["raw"], object_pairs_hook=unique, parse_constant=bad_constant)

def corroborate_times(before, after, start, end):
    """Require Binance server-clock observations within the local request span."""
    values = []
    for resp in (before, after):
        value = decode(resp)
        if not isinstance(value, dict) or type(value.get("serverTime")) is not int:
            raise ValueError("invalid first-party serverTime")
        values.append(value["serverTime"])
        measured = int(utc(resp["received_utc"]).timestamp()*1000)
        if abs(value["serverTime"] - measured) > MAX_SKEW_MS:
            raise ValueError("server and acquisition clocks disagree >60s")
    if values[1] < values[0]:
        raise ValueError("first-party serverTime regressed")
    first, last = utc(start), utc(end)
    if first > last or (last-first).total_seconds() > 60:
        raise ValueError("source collection time window exceeds 60s")
    for resp in (before, after):
        if not first <= utc(resp["requested_utc"]) <= utc(resp["received_utc"]) <= last:
            raise ValueError("non-monotonic request/receipt timestamps")
    return values

def listed_symbols(ex, observed_utc):
    if not isinstance(ex, dict) or not isinstance(ex.get("symbols"), list):
        raise ValueError("exchangeInfo symbols missing")
    current, seen = {}, set()
    for row in ex["symbols"]:
        if not isinstance(row, dict):
            raise ValueError("malformed exchangeInfo symbol")
        sym = row.get("symbol")
        if not isinstance(sym, str) or not sym or sym in seen:
            raise ValueError("duplicate/malformed symbol")
        seen.add(sym)
        if row.get("contractType") != "PERPETUAL" or row.get("quoteAsset") != "USDT" or row.get("status") != "TRADING":
            continue
        listing = row.get("onboardDate")
        if type(listing) is not int:
            raise ValueError("onboardDate missing")
        current[sym] = {
            "symbol": sym, "exchange_status": "TRADING",
            "onboard_date_metadata_ms_NOT_a_discovery_receipt": listing,
            "first_directly_observed_in_this_snapshot_utc": observed_utc,
            "earliest_eligible_after_receipt_t_minus_1_utc": first_safe_decision(observed_utc),
        }
    if not current:
        raise ValueError("empty as-of universe")
    return current

def fully_closed_klines(rows, receipt_utc, symbol):
    if not isinstance(rows, list):
        raise ValueError(symbol+": klines not list")
    seen, out = set(), []
    cutoff_ms = int(utc(receipt_utc).timestamp()*1000)
    for row in rows:
        if not isinstance(row, list) or len(row) < 12:
            raise ValueError(symbol+": malformed kline")
        start_ms, close_ms = row[0], row[6]
        if type(start_ms) is not int or type(close_ms) is not int:
            raise ValueError(symbol+": noninteger kline timestamps")
        if start_ms % 3_600_000 or close_ms != start_ms+3_600_000-1:
            raise ValueError(symbol+": non-hourly close interval")
        if start_ms in seen:
            raise ValueError(symbol+": duplicate kline")
        seen.add(start_ms)
        if close_ms >= cutoff_ms:
            continue  # unfinished candles are never admissible
        out.append({"open_utc": iso(datetime.fromtimestamp(start_ms/1000,timezone.utc)),
                    "close_utc": iso(datetime.fromtimestamp((close_ms+1)/1000,timezone.utc)),
                    "ohlcv_native": row[:6], "native_quote_volume": row[7]})
    if not out:
        raise ValueError(symbol+": no fully closed kline")
    out.sort(key=lambda p:p["open_utc"])
    return out

def envelope(resp):
    return {key:val for key,val in resp.items() if key != "raw"}

def acquire():
    started = stamp()
    before = http_get("/fapi/v1/time")
    exchange = http_get("/fapi/v1/exchangeInfo")
    ex = decode(exchange)
    symbols = listed_symbols(ex, exchange["received_utc"])
    observed = {}
    complete = {}
    for symbol in CORE:
        if symbol not in symbols:
            raise ValueError(symbol+" not in observed first-party active universe")
        r = http_get("/fapi/v1/klines?symbol="+symbol+"&interval=1h&limit=3")
        observed[symbol] = r
        complete[symbol] = fully_closed_klines(decode(r),r["received_utc"],symbol)
    after = http_get("/fapi/v1/time")
    completed = stamp()
    times=corroborate_times(before, after, iso(started), iso(completed))
    if utc(exchange["received_utc"]) > utc(after["received_utc"]):
        raise ValueError("out-of-order collection")
    manifest = {
        "schema": "v99-r106-live-receipt-v1", "mode": "DATA_ONLY",
        "capture_start_utc": iso(started), "capture_end_utc": iso(completed),
        "source": "first_party_binance_usdm_https",
        "server_clock_before_ms": times[0], "server_clock_after_ms": times[1],
        "universe_total_eligible_at_observation": len(symbols),
        "listing_discovery_is_prospective_only": True,
        "earliest_safe_decision_utc": first_safe_decision(exchange["received_utc"]),
        "universe_receipt": envelope(exchange),
        "server_time_receipts": [envelope(before),envelope(after)],
        "kline_receipts": {k:envelope(v) for k,v in observed.items()},
        "fully_closed_klines": complete,
        "discovery_receipts_current_only": symbols,
        "retrospective_first_seen_attested": False,
        "independently_exchange_signed": False,
        "github_artifact_not_an_exchange_signature": True,
        "full_paper_pnl_authenticated": False,
        "training_or_holdout_accessed": False,
        "economic_trials": 0,
        "paper_publication_authorized": False,
        "promotion_authorized": False,
    }
    return manifest, {"time_before":before,"exchange_info":exchange,
                      **{"klines_"+sym:observed[sym] for sym in CORE}, "time_after":after}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    manifest, receipts=acquire()
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    for name, receipt in receipts.items():
        (args.out/(name+".json")).write_bytes(receipt["raw"])
    print(json.dumps({"status":"PROSPECTIVE_DATA_ONLY_RECEIPT",
        "source":manifest["source"],"symbols":manifest["universe_total_eligible_at_observation"],
        "earliest_decision":manifest["earliest_safe_decision_utc"],
        "paper_publication_authorized":False}))

if __name__ == "__main__":
    main()
