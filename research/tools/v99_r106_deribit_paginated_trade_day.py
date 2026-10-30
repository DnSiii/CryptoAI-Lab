"""One-shot bounded 2022-01-23 original Deribit option TRADE pagination; NOT BBO, fills or PnL."""
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

HOST = "https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time"
DAY = "2022-01-23"
COINS = ("BTC", "ETH")
COUNT = 1000
MAX_PAGES = 30
MAX_BYTES = 8_000_000
DAY_START = int(datetime(2022, 1, 23, tzinfo=timezone.utc).timestamp() * 1000)
DAY_END = DAY_START + 86_400_000
PATTERN = re.compile(r"^(BTC|ETH)-(\d{1,2}[A-Z]{3}\d{2})-(\d+(?:\.\d+)?)-([PC])$")
FORBIDDEN = dict(native_quotes_authenticated=False, historical_fills_authenticated=False,
    native_fee_tier_authenticated=False, full_lifecycle_authenticated=False,
    economic_trial_run=False, validation_opened=False, final_holdout_opened=False,
    promotion_authorized=False, paper_publication_authorized=False, orders_enabled=False)


def request(coin, cursor):
    args = dict(currency=coin, kind="option", include_old="true", sorting="asc",
                count=COUNT, start_timestamp=DAY_START if cursor is None else cursor,
                end_timestamp=DAY_END - 1)
    url = HOST + "?" + urlencode(args)
    last = "UNKNOWN"
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"Accept": "application/json",
                    "User-Agent": "CryptoAI-Lab-V99-Research-Source-Only/1.0"}), timeout=30) as r:
                if r.status != 200:
                    raise ValueError("NON_200")
                raw = r.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("OVERSIZE_RESPONSE")
            return raw
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            last = type(exc).__name__ + ":" + str(exc)[:70]
            if attempt < 2:
                time.sleep(2)
    raise ValueError("TRANSPORT_FAILED:" + last)


def parse(raw, coin):
    data = json.loads(raw)
    if not isinstance(data, dict) or "error" in data:
        raise ValueError("JSON_RPC_ERROR")
    result = data.get("result")
    if not isinstance(result, dict) or type(result.get("has_more")) is not bool:
        raise ValueError("MISSING_HAS_MORE")
    trades = result.get("trades")
    if not isinstance(trades, list) or len(trades) > COUNT or not trades:
        raise ValueError("EMPTY_OR_UNBOUNDED_TRADES")
    ids = set()
    times = []
    for tr in trades:
        if not isinstance(tr, dict):
            raise ValueError("BAD_TRADE")
        match = PATTERN.fullmatch(str(tr.get("instrument_name", "")))
        if match is None or match.group(1) != coin:
            raise ValueError("INVALID_OPTION_INSTRUMENT")
        datetime.strptime(match.group(2), "%d%b%y")
        ts = tr.get("timestamp")
        if type(ts) is not int or not DAY_START <= ts < DAY_END:
            raise ValueError("OUTSIDE_FIXED_TRAIN_DAY")
        if not all(math.isfinite(float(tr[k])) and float(tr[k]) > 0 for k in ("price", "amount")):
            raise ValueError("INVALID_PRICE_OR_AMOUNT")
        tid = tr.get("trade_id")
        if not isinstance(tid, str) or not tid or tid in ids:
            raise ValueError("MISSING_OR_DUPLICATE_TRADE_ID")
        ids.add(tid)
        times.append(ts)
    if times != sorted(times):
        raise ValueError("NONMONOTONE_PAGE")
    return trades, result["has_more"]


def add_page(state, raw, coin, cursor):
    trades, more = parse(raw, coin)
    if cursor is not None:
        if trades[0]["timestamp"] != cursor:
            raise ValueError("MISSING_INCLUSIVE_CURSOR_OVERLAP")
        boundary = {x["trade_id"]: x for x in trades if x["timestamp"] == cursor}
        if not state["boundary"] or not all(
                tid in boundary and boundary[tid] == old for tid, old in state["boundary"].items()):
            raise ValueError("AMBIGUOUS_TIMESTAMP_BOUNDARY")
    else:
        if state["ids"]:
            raise ValueError("RESTARTED_PAGINATION")
    new = 0
    for tr in trades:
        tid = tr["trade_id"]
        if tid in state["ids"]:
            if tr != state["ids"][tid] or cursor is None or tr["timestamp"] != cursor:
                raise ValueError("CONFLICTING_OR_NONBOUNDARY_DUPLICATE")
            continue
        state["ids"][tid] = tr
        new += 1
        m = PATTERN.fullmatch(tr["instrument_name"])
        expiry = datetime.strptime(m.group(2), "%d%b%y").date()
        tenor = (expiry - datetime(2022, 1, 23).date()).days
        if m.group(4) == "P" and 28 <= tenor <= 35:
            state["eligible"].setdefault(expiry.isoformat(), set()).add(m.group(3))
    if not new:
        raise ValueError("STUCK_CURSOR_NO_NEW_TRADES")
    last = trades[-1]["timestamp"]
    if cursor is not None and last <= cursor:
        raise ValueError("STUCK_TIMESTAMP")
    state["boundary"] = {x["trade_id"]: x for x in trades if x["timestamp"] == last}
    if len(state["boundary"]) >= COUNT and more:
        raise ValueError("AMBIGUOUS_FULL_TIMESTAMP_PAGE")
    return last, more, new, len(trades)


def run(out):
    out = Path(out)
    rawdir = out / "raw_ephemeral"
    rawdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for coin in COINS:
        state = dict(ids={}, boundary={}, eligible={})
        pages = []
        cursor = None
        complete = False
        error = None
        for index in range(MAX_PAGES):
            try:
                raw = request(coin, cursor)
                nxt, more, new, count = add_page(state, raw, coin, cursor)
                name = f"{coin}_{index:03d}.json"
                (rawdir / name).write_bytes(raw)
                pages.append(dict(file=name, sha256=hashlib.sha256(raw).hexdigest(),
                                  cursor=cursor, last_timestamp=nxt, returned=count,
                                  unique_new=new, has_more=more))
                cursor = nxt
                if not more:
                    complete = True
                    break
            except (ValueError, TypeError, KeyError, OverflowError, json.JSONDecodeError) as exc:
                error = type(exc).__name__ + ":" + str(exc)[:100]
                break
        if not complete and error is None:
            error = "MAX_PAGES_REACHED_WITH_HAS_MORE"
        eligible = {expiry: len(strikes) for expiry, strikes in sorted(state["eligible"].items())}
        rows.append(dict(currency=coin, day=DAY, status=("COMPLETE_REPORTED_TRADE_PAGINATION"
            if complete else "INCOMPLETE_OR_UNCONFIRMED_TRADE_ACTIVITY"),
            pages=pages, page_count=len(pages), unique_trade_prints=len(state["ids"]),
            first_timestamp=min((t["timestamp"] for t in state["ids"].values()), default=None),
            last_timestamp=max((t["timestamp"] for t in state["ids"].values()), default=None),
            eligible_28_35d_put_strikes_by_expiry=eligible,
            eligible_two_distinct_traded_put_strikes=any(n >= 2 for n in eligible.values()),
            error=error))
        print("DERIBIT_TRADE_DAY", coin, rows[-1]["status"], "pages", len(pages),
              "unique", len(state["ids"]), "error", error, flush=True)
    eligible = all(x["status"] == "COMPLETE_REPORTED_TRADE_PAGINATION"
                   and x["eligible_two_distinct_traded_put_strikes"] for x in rows)
    report = dict(schema="V99_R106_DERIBIT_ORIGINAL_PAGINATED_TRADE_DAY_SOURCE_ONLY_V1",
        preregistration="research/V99_R106_DERIBIT_TARGET_DAY_PAGINATED_TRADE_FEASIBILITY_PREREG_20261030.md",
        status=("TRADE_ACTIVITY_FEASIBLE_QUOTES_STILL_MISSING" if eligible
                else "INCOMPLETE_OR_UNCONFIRMED_TRADE_ACTIVITY"),
        original_source="history.deribit.com", original_day=DAY,
        api_reported_complete_is_not_market_quote_coverage=True,
        original_661_day_quote_archive_delivered=False, certified_option_lifecycles=0,
        trade_prints_are_not_executable_quotes=True, rows=rows, **FORBIDDEN)
    (out / "original_paginated_trade_day_source_only.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_deribit_paginated_trade_day OUT")
    run(sys.argv[1])
