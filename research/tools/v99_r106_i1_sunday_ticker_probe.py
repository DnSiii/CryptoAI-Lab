"""Bounded ORIGINAL Deribit ticker minute receipts on two free TRAIN Sundays.

Never read validation/holdout. Third-party capture, NOT native fills or PnL.
Protocol: research/V99_R106_I1_FREE_SUNDAY_TICKER_SOURCE_PREREG_20261025.md
"""
from __future__ import annotations
import gzip
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

DAYS = ("2022-05-01", "2023-01-01")
OFFSETS = range(1435, 1440)
MAX_COMPRESSED = 12 * 1024 * 1024
TRAIN_END = datetime(2023, 10, 1, tzinfo=timezone.utc)
FIELDS = ("best_bid_price", "best_ask_price", "best_bid_amount", "best_ask_amount")
OUT = Path("research_evidence/i1_free_sunday_ticker")
SYMBOL = re.compile(r"^(BTC|ETH)-(\d{1,2}[A-Z]{3}\d{2})-(\d+(?:\.\d+)?)-P$")


def parsed_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def literal_option(name, decision):
    if not isinstance(name, str):
        return None
    match = SYMBOL.fullmatch(name)
    if not match:
        return None
    try:
        expiry = datetime.strptime(match[2], "%d%b%y").replace(hour=8, tzinfo=timezone.utc)
        strike = Decimal(match[3])
    except (ValueError, InvalidOperation):
        return None
    if strike <= 0 or not timedelta(days=21) <= expiry-decision <= timedelta(days=45) or expiry >= TRAIN_END:
        return None
    return match[1], expiry.isoformat(), str(strike)


def extract_ticker(message):
    params = message.get("params")
    if not isinstance(params, dict) or not str(params.get("channel", "")).startswith("ticker."):
        return None
    data = params.get("data")
    if not isinstance(data, dict):
        return None
    return data


def positive_book(data):
    try:
        vals = [Decimal(str(data[k])) for k in FIELDS]
    except (KeyError, ValueError, TypeError, InvalidOperation):
        return None
    if not all(x.is_finite() and x > 0 for x in vals) or vals[0] >= vals[1]:
        return None
    return [str(v) for v in vals]


def run(out=OUT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    all_days = []
    for day in DAYS:
        decision = parsed_time(day + "T00:00:00Z") + timedelta(days=1)
        decision_us = int(decision.timestamp()*1_000_000)
        cutoff_us = decision_us - 300_000_000
        last = {}
        receipts = []
        rows = 0
        tickers = 0
        previous_us = None
        for offset in OFFSETS:
            query = urllib.parse.urlencode({"from": day, "offset": offset,
                "filters": json.dumps([{"channel": "ticker"}], separators=(",", ":"))})
            url = "https://api.tardis.dev/v1/data-feeds/deribit?" + query
            req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip",
                "User-Agent": "V99-original-train-source-only/1.0"})
            with urllib.request.urlopen(req, timeout=70) as response:
                if response.status != 200:
                    raise ValueError(f"NON_SUCCESSFUL_ORIGINAL_MINUTE_{day}_{offset}")
                raw = response.read(MAX_COMPRESSED+1)
            if len(raw) > MAX_COMPRESSED or not raw.startswith(b"\x1f\x8b"):
                raise ValueError(f"TRUNCATED_OR_NOT_GZIP_{day}_{offset}")
            decoded = gzip.decompress(raw).decode("utf-8")
            name = f"{day}_{offset}.ndjson.gz"
            (out/name).write_bytes(raw)
            receipts.append({"offset": offset, "file": name, "sha256": hashlib.sha256(raw).hexdigest(),
                "compressed_bytes": len(raw)})
            minute_start = int((parsed_time(day+"T00:00:00Z")+timedelta(minutes=offset)).timestamp()*1_000_000)
            for line in decoded.splitlines():
                if not line.strip():
                    continue
                arrival, sep, raw_message = line.partition(" ")
                if not sep:
                    raise ValueError("BAD_ORIGINAL_MESSAGE_LINE")
                local_us = int(parsed_time(arrival).timestamp()*1_000_000)
                if not minute_start <= local_us < minute_start+60_000_000:
                    raise ValueError("OUTSIDE_REQUESTED_ORIGINAL_MINUTE")
                if previous_us is not None and local_us < previous_us:
                    raise ValueError("OUT_OF_ORDER_ORIGINAL_CAPTURE")
                previous_us = local_us
                rows += 1
                message = json.loads(raw_message)
                data = extract_ticker(message)
                if data is None:
                    continue
                tickers += 1
                symbol = data.get("instrument_name")
                parsed = literal_option(symbol, decision)
                if parsed is None:
                    continue
                # Physical row order wins. Invalid last updates revoke older ones.
                book = positive_book(data)
                try:
                    exchange_us = int(Decimal(str(data["timestamp"])) * 1000)
                except (KeyError, ValueError, TypeError, InvalidOperation):
                    exchange_us = -1
                valid = bool(book and cutoff_us <= exchange_us <= local_us < decision_us)
                last[symbol] = ({"asset": parsed[0], "symbol": symbol, "expiry": parsed[1],
                    "strike": parsed[2], "arrival_us": local_us, "exchange_us": exchange_us,
                    "bid_coin": book[0], "ask_coin": book[1], "bid_size_source_units": book[2],
                    "ask_size_source_units": book[3]} if valid else None)
        books = sorted((v for v in last.values() if v is not None), key=lambda x:x["symbol"])
        grouped = {}
        for b in books:
            grouped.setdefault((b["asset"], b["expiry"]), set()).add(b["strike"])
        pairs = {asset: any(a == asset and len(s) >= 2 for (a,_),s in grouped.items())
                 for asset in ("BTC", "ETH")}
        all_days.append({"day": day, "decision_utc": decision.isoformat(),
            "minutes_complete": len(receipts), "raw_messages": rows, "ticker_messages": tickers,
            "original_receipts": receipts, "last_eligible_books": books, "two_strike_pairs": pairs})
    report = {"schema": "V99_I1_ORIGINAL_TARDIS_FREE_SUNDAY_TICKER_PILOT_V1",
        "source": "Tardis raw HTTP minute replay, original Deribit ticker capture (third party)",
        "status": "TRAIN_SAMPLE_ONLY_NOT_EXECUTION_CERTIFIED",
        "days": all_days, "real_source_asset_weeks_with_two_strikes": sum(
            sum(d["two_strike_pairs"].values()) for d in all_days),
        "max_possible_sample_asset_weeks": 4, "full_train_asset_weeks_required": 182,
        "historical_fee_margin_certified": False, "holding_period_quotes_certified": False,
        "historical_economic_train_executed": False, "validation_opened": False,
        "holdout_opened": False, "orders_enabled": False, "promotion_authorized": False}
    (out/"report.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "sample_pairs": report["real_source_asset_weeks_with_two_strikes"],
        "days": [{k:v for k,v in d.items() if k in ("day","raw_messages","ticker_messages","two_strike_pairs","minutes_complete")}
                 for d in all_days], "promotion": False}))
    return report


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv)>1 else OUT)
