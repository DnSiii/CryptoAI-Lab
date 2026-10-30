"""Original first-party Deribit option trade tape, fixed TRAIN target day only; NOT quotes."""
from __future__ import annotations
import hashlib
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DAY = "2022-01-23"
START = int(datetime(2022, 1, 23, tzinfo=timezone.utc).timestamp() * 1000)
END = START + 86_400_000 - 1
DECISION = datetime(2022, 1, 24, tzinfo=timezone.utc)
COINS = ("BTC", "ETH")
URL = "https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time"
COUNT = 1000
MAX_PAGES = 64
MAX_BYTES = 4 * 1024 * 1024
NO_PROMOTION = {key: False for key in (
    "original_executable_quotes_authenticated", "native_fills_authenticated",
    "historical_native_fee_tier_authenticated", "full_lifecycle_authenticated",
    "economic_trial_run", "validation_opened", "final_holdout_opened",
    "promotion_authorized", "paper_publication_authorized", "orders_enabled")}


def fetch_page(coin, cursor):
    params = dict(currency=coin, kind="option", start_timestamp=cursor,
                  end_timestamp=END, include_old="true", sorting="asc", count=COUNT)
    url = URL + "?" + urlencode(params)
    for attempt in range(1, 4):
        try:
            req = Request(url, headers={"Accept": "application/json",
                "User-Agent": "CryptoAI-Lab-V99-SourceOnly/1.0"})
            with urlopen(req, timeout=24) as response:
                if response.status != 200:
                    raise ValueError("HTTP_NON_200")
                raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("SOURCE_PAGE_OVERSIZE")
            return raw, attempt, None
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            error = type(exc).__name__
            if attempt < 3:
                time.sleep(2)
    return None, 3, error


def validate_trade(tr, coin):
    if not isinstance(tr, dict):
        raise ValueError("NOT_TRADE")
    instrument = str(tr.get("instrument_name", ""))
    match = re.fullmatch(
        re.escape(coin) + r"-(\d{1,2}[A-Z]{3}\d{2})-(\d+)-(P|C)", instrument)
    if not match:
        raise ValueError("NOT_DATED_OPTION")
    ts = tr.get("timestamp")
    if type(ts) is not int or not START <= ts <= END:
        raise ValueError("OUT_OF_TARGET_TRAIN_DAY")
    for key in ("price", "amount"):
        value = float(tr[key])
        if not math.isfinite(value) or value <= 0:
            raise ValueError("BAD_ORIGINAL_TRADE")
    trade_id = tr.get("trade_id")
    if not isinstance(trade_id, str) or not trade_id:
        raise ValueError("MISSING_ORIGINAL_TRADE_ID")
    expiry = datetime.strptime(match.group(1), "%d%b%y").replace(tzinfo=timezone.utc)
    days = (expiry - DECISION).total_seconds() / 86400
    return trade_id, ts, instrument, match.group(2), match.group(3), 28 <= days <= 35


def run(root):
    root = Path(root)
    raw_root = root / "raw_ephemeral"
    raw_root.mkdir(parents=True, exist_ok=True)
    summaries = []
    for coin in COINS:
        seen = {}
        instruments = set()
        eligible_put_strikes = set()
        put_strikes = set()
        call_strikes = set()
        pages = []
        cursor = START
        state = "INCOMPLETE_OR_UNKNOWN"
        error = None
        for page_index in range(MAX_PAGES):
            raw, attempts, error = fetch_page(coin, cursor)
            if raw is None:
                break
            try:
                envelope = json.loads(raw)
                if not isinstance(envelope, dict) or envelope.get("error"):
                    raise ValueError("JSONRPC_ERROR")
                result = envelope.get("result")
                if not isinstance(result, dict) or type(result.get("has_more")) is not bool:
                    raise ValueError("MISSING_HAS_MORE")
                trades = result.get("trades")
                if not isinstance(trades, list) or not 0 < len(trades) <= COUNT:
                    raise ValueError("EMPTY_OR_UNBOUNDED_PAGE")
                times = []
                added = 0
                for trade in trades:
                    tid, ts, instrument, strike, side, eligible = validate_trade(trade, coin)
                    times.append(ts)
                    signature = hashlib.sha256(
                        json.dumps(trade, sort_keys=True, separators=(",", ":")).encode()
                    ).hexdigest()
                    if tid in seen:
                        if seen[tid] != signature:
                            raise ValueError("CONFLICTING_DUPLICATE_TRADE")
                    else:
                        seen[tid] = signature
                        added += 1
                        instruments.add(instrument)
                        if side == "P":
                            put_strikes.add(instrument)
                            if eligible:
                                eligible_put_strikes.add(instrument)
                        else:
                            call_strikes.add(instrument)
                if times != sorted(times) or times[0] < cursor:
                    raise ValueError("NON_MONOTONE_PAGE")
                if not added:
                    raise ValueError("NONADVANCING_CURSOR_OR_TIMESTAMP_TIE")
                path = raw_root / f"{coin}_{page_index:03d}.json"
                path.write_bytes(raw)
                pages.append(dict(page=page_index, requested_start_ms=cursor,
                    raw_sha256=hashlib.sha256(raw).hexdigest(),
                    returned=len(trades), added_unique=added, first_ms=times[0],
                    last_ms=times[-1], has_more=result["has_more"], attempts=attempts))
                print(f"DERIBIT_TAPE {coin} page={page_index} unique={len(seen)} "
                      f"has_more={result['has_more']}", flush=True)
                if not result["has_more"]:
                    state = "API_PAGINATION_ENDED_NOT_MARKET_COMPLETENESS"
                    error = None
                    break
                cursor = times[-1]  # inclusive overlap; no silent skipped same-ms trades
            except (ValueError, KeyError, TypeError, OverflowError, json.JSONDecodeError) as exc:
                error = type(exc).__name__ + ":" + str(exc)[:120]
                break
        summaries.append(dict(currency=coin, day=DAY, status=state,
            error=error, pages=pages, unique_trades=len(seen),
            unique_option_instruments=len(instruments),
            unique_put_instruments=len(put_strikes),
            unique_call_instruments=len(call_strikes),
            distinct_28_35d_put_instruments=len(eligible_put_strikes),
            first_trade_ms=pages[0]["first_ms"] if pages else None,
            last_trade_ms=pages[-1]["last_ms"] if pages else None))
    complete = all(x["status"] == "API_PAGINATION_ENDED_NOT_MARKET_COMPLETENESS"
                   for x in summaries)
    report = dict(schema="V99_R106_DERIBIT_TARGET_DAY_TAPE_SOURCE_V1",
        preregistration="research/V99_R106_DERIBIT_TARGET_DAY_TAPE_PAGINATION_PREREG_20261030.md",
        status=("PUBLIC_TRADE_DAY_PAGINATION_COMPLETE_NOT_QUOTES" if complete else
                "PUBLIC_TRADE_DAY_PAGINATION_INCOMPLETE_OR_UNKNOWN"),
        source_host="history.deribit.com", day=DAY, count_per_page=COUNT,
        max_pages_per_coin=MAX_PAGES, currencies=summaries,
        tape_is_not_executable_quotes=True,
        api_pagination_does_not_certify_exchange_market_completeness=True,
        elligible_put_trade_activity_is_not_synchronized_bbo=True,
        certified_option_lifecycles=0, original_661_day_quote_archive_delivered=False,
        **NO_PROMOTION)
    (root / "target_day_trade_tape_source_only.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(status=report["status"],
        currencies=[{k: x[k] for k in ("currency", "status", "unique_trades",
            "distinct_28_35d_put_instruments", "error")} for x in summaries],
        certified_option_lifecycles=0, promotion_authorized=False), sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_deribit_target_day_tape OUT")
    run(sys.argv[1])
