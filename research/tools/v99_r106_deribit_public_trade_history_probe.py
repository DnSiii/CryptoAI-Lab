"""Bounded first-party Deribit historical trade source probe, NOT options quotes or PnL."""
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

URL = "https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time"
DAYS = ("2022-01-23", "2022-05-01")
COINS = ("BTC", "ETH")
COUNT = 100
NO_PROMOTION = dict(
    native_quotes_authenticated=False, historical_fills_authenticated=False,
    native_fee_tier_authenticated=False, full_lifecycle_authenticated=False,
    economic_trial_run=False, validation_opened=False, final_holdout_opened=False,
    promotion_authorized=False, paper_publication_authorized=False, orders_enabled=False,
)


def day_bounds(day):
    t = int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
    return t, t + 86400000 - 1


def request_original(coin, day):
    start, end = day_bounds(day)
    params = dict(currency=coin, kind="option", start_timestamp=start,
                  end_timestamp=end, include_old="true", sorting="asc", count=COUNT)
    url = URL + "?" + urlencode(params)
    for attempt in range(1, 4):
        try:
            req = Request(url, headers={"Accept": "application/json",
                "User-Agent": "CryptoAI-Lab-V99-Research-Source-Only/1.0"})
            with urlopen(req, timeout=18) as response:
                if response.status != 200:
                    raise ValueError("HTTP_NON_200")
                raw = response.read(2000001)
            if len(raw) > 2000000:
                raise ValueError("RESPONSE_TOO_LARGE")
            return raw, attempt, None
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            err = type(exc).__name__
            if attempt < 3:
                time.sleep(2)
    return None, 3, err


def inspect(raw, coin, day):
    start, end = day_bounds(day)
    envelope = json.loads(raw)
    if not isinstance(envelope, dict) or "error" in envelope:
        raise ValueError("JSON_RPC_ERROR")
    result = envelope.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("trades"), list):
        raise ValueError("NOT_TRADE_LIST")
    trades = result["trades"]
    if len(trades) > COUNT:
        raise ValueError("UNBOUNDED_TRADE_RESPONSE")
    pattern = re.compile(r"^" + coin + r"-[0-9]{1,2}[A-Z]{3}[0-9]{2}-[0-9]+-(?:P|C)$")
    seen = set()
    stamps = []
    for tr in trades:
        if not isinstance(tr, dict) or not pattern.fullmatch(str(tr.get("instrument_name", ""))):
            raise ValueError("NOT_DATED_OPTION_CONTRACT")
        ts = tr.get("timestamp")
        if type(ts) is not int or not start <= ts <= end:
            raise ValueError("OUT_OF_TRAIN_DAY")
        if not all(math.isfinite(float(tr.get(k))) and float(tr[k]) > 0
                   for k in ("price", "amount")):
            raise ValueError("NONPOSITIVE_TRADE")
        trade_id = tr.get("trade_id")
        if trade_id is not None:
            if trade_id in seen:
                raise ValueError("DUPLICATE_TRADE_ID")
            seen.add(trade_id)
        stamps.append(ts)
    if stamps != sorted(stamps):
        raise ValueError("NOT_ASCENDING")
    return dict(returned_count=len(trades), first_timestamp=min(stamps, default=None),
                last_timestamp=max(stamps, default=None),
                valid_option_contract_rows=len(trades),
                has_more=result.get("has_more") if type(result.get("has_more")) is bool else None)


def run(output):
    output = Path(output)
    raw_dir = output / "raw_ephemeral"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for day in DAYS:
        for coin in COINS:
            raw, attempts, error = request_original(coin, day)
            row = dict(currency=coin, day=day, attempts=attempts, transport_error=error,
                       raw_sha256=None, returned_count=None, first_timestamp=None,
                       last_timestamp=None, valid_option_contract_rows=None, has_more=None,
                       status="UNKNOWN_TRANSPORT_OR_SCHEMA")
            if raw is not None:
                try:
                    values = inspect(raw, coin, day)
                    row.update(values)
                    row["raw_sha256"] = hashlib.sha256(raw).hexdigest()
                    row["status"] = ("VERIFIED_FIRSTPARTY_PUBLIC_TRADE_PRINTS"
                                     if values["returned_count"] > 0 else "UNKNOWN_EMPTY")
                    (raw_dir / f"{coin}_{day}.json").write_bytes(raw)
                except (ValueError, TypeError, KeyError, json.JSONDecodeError, OverflowError):
                    row["status"] = "UNKNOWN_MALFORMED_SOURCE"
            rows.append(row)
            print(f"DERIBIT_PUBLIC_HISTORY {day} {coin} {row['status']} "
                  f"count={row['returned_count']} attempts={attempts}", flush=True)
    target = [x for x in rows if x["day"] == "2022-01-23"]
    available = all(x["status"] == "VERIFIED_FIRSTPARTY_PUBLIC_TRADE_PRINTS" for x in target)
    report = dict(schema="V99_R106_DERIBIT_PUBLIC_TRADE_HISTORY_SOURCE_ONLY_V1",
        status=("PUBLIC_TRADE_HISTORY_AVAILABLE_NOT_EXECUTABLE" if available
                else "PUBLIC_TRADE_HISTORY_UNCONFIRMED"),
        preregistration="research/V99_R106_DERIBIT_HISTORY_PUBLIC_TRADE_SOURCE_PREREG_20261030.md",
        first_party_host="history.deribit.com", query_count=4, rows=rows,
        trade_prints_are_not_executable_quotes=True,
        original_trade_prints_do_not_certify_complete_day=True,
        original_661_day_quote_archive_delivered=False,
        certified_option_lifecycles=0, **NO_PROMOTION)
    (output / "trade_history_source_only.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(status=report["status"], target_counts={
        x["currency"]: x["returned_count"] for x in target}, promotion_authorized=False)))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_deribit_public_trade_history_probe OUT_DIR")
    run(sys.argv[1])
