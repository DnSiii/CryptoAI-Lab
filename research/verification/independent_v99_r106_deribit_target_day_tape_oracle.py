"""Independent original-byte replay of fixed-day Deribit trade tape; NEVER a quote oracle."""
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

START = int(datetime(2022, 1, 23, tzinfo=timezone.utc).timestamp() * 1000)
END = START + 86400000 - 1
DECISION = datetime(2022, 1, 24, tzinfo=timezone.utc)
FORBIDDEN = (
    "original_executable_quotes_authenticated", "native_fills_authenticated",
    "historical_native_fee_tier_authenticated", "full_lifecycle_authenticated",
    "economic_trial_run", "validation_opened", "final_holdout_opened",
    "promotion_authorized", "paper_publication_authorized", "orders_enabled",
)


def replay(root):
    root = Path(root)
    report = json.loads((root / "target_day_trade_tape_source_only.json").read_bytes())
    if report.get("schema") != "V99_R106_DERIBIT_TARGET_DAY_TAPE_SOURCE_V1":
        raise ValueError("ORACLE_SCHEMA")
    if report.get("day") != "2022-01-23" or report.get("count_per_page") != 1000:
        raise ValueError("ORACLE_TRAIN_SCOPE")
    if report.get("max_pages_per_coin") != 64:
        raise ValueError("ORACLE_UNBOUNDED_SOURCE")
    if any(report.get(k) is not False for k in FORBIDDEN):
        raise ValueError("ORACLE_FALSE_PERMISSION")
    if report.get("certified_option_lifecycles") != 0:
        raise ValueError("ORACLE_FAKE_LIFECYCLE")
    if report.get("original_661_day_quote_archive_delivered") is not False:
        raise ValueError("ORACLE_FAKE_ARCHIVE")
    for k in ("tape_is_not_executable_quotes",
              "api_pagination_does_not_certify_exchange_market_completeness",
              "elligible_put_trade_activity_is_not_synchronized_bbo"):
        if report.get(k) is not True:
            raise ValueError("ORACLE_FAKE_EXECUTABLE_BBO")
    rows = report.get("currencies")
    if not isinstance(rows, list) or [r.get("currency") for r in rows] != ["BTC", "ETH"]:
        raise ValueError("ORACLE_COINS")
    states = []
    for row in rows:
        coin = row["currency"]
        pages = row.get("pages")
        if not isinstance(pages, list) or len(pages) > 64:
            raise ValueError("ORACLE_PAGE_CAP")
        expected_files = {f"{coin}_{i:03d}.json" for i in range(len(pages))}
        actual_files = {p.name for p in (root / "raw_ephemeral").glob(f"{coin}_*.json")}
        if actual_files != expected_files:
            raise ValueError("ORACLE_RAW_PAGE_SET")
        seen = {}
        options = set()
        puts = set()
        calls = set()
        eligible_puts = set()
        cursor = START
        ended = False
        for i, metadata in enumerate(pages):
            if metadata.get("page") != i or metadata.get("requested_start_ms") != cursor:
                raise ValueError("ORACLE_PAGE_CURSOR")
            raw = (root / "raw_ephemeral" / f"{coin}_{i:03d}.json").read_bytes()
            if len(raw) > 4 * 1024 * 1024:
                raise ValueError("ORACLE_PAGE_BYTES")
            if hashlib.sha256(raw).hexdigest() != metadata.get("raw_sha256"):
                raise ValueError("ORACLE_ORIGINAL_DIGEST")
            envelope = json.loads(raw)
            if not isinstance(envelope, dict) or envelope.get("error"):
                raise ValueError("ORACLE_RPC_ERROR")
            result = envelope.get("result")
            if not isinstance(result, dict) or type(result.get("has_more")) is not bool:
                raise ValueError("ORACLE_HAS_MORE")
            trades = result.get("trades")
            if not isinstance(trades, list) or not 0 < len(trades) <= 1000:
                raise ValueError("ORACLE_PAGE_SIZE")
            times = []
            added = 0
            for trade in trades:
                if not isinstance(trade, dict):
                    raise ValueError("ORACLE_NOT_TRADE")
                name = trade.get("instrument_name")
                match = re.fullmatch(
                    re.escape(coin) + r"-(\d{1,2}[A-Z]{3}\d{2})-(\d+)-(P|C)",
                    name if isinstance(name, str) else "")
                if not match:
                    raise ValueError("ORACLE_NOT_OPTION")
                stamp = trade.get("timestamp")
                if type(stamp) is not int or stamp < cursor or stamp > END:
                    raise ValueError("ORACLE_TIME_LEAK")
                for key in ("price", "amount"):
                    val = float(trade[key])
                    if not math.isfinite(val) or val <= 0:
                        raise ValueError("ORACLE_BAD_TRADE")
                tid = trade.get("trade_id")
                if not isinstance(tid, str) or not tid:
                    raise ValueError("ORACLE_MISSING_ID")
                signature = hashlib.sha256(
                    json.dumps(trade, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
                if tid in seen:
                    if seen[tid] != signature:
                        raise ValueError("ORACLE_CONFLICTING_DUPLICATE")
                else:
                    seen[tid] = signature
                    added += 1
                    options.add(name)
                    if match.group(3) == "P":
                        puts.add(name)
                        expiry = datetime.strptime(match.group(1), "%d%b%y").replace(
                            tzinfo=timezone.utc)
                        if 28 <= (expiry - DECISION).total_seconds() / 86400 <= 35:
                            eligible_puts.add(name)
                    else:
                        calls.add(name)
                times.append(stamp)
            if times != sorted(times) or added <= 0:
                raise ValueError("ORACLE_NONADVANCING_OR_UNSORTED")
            for k, v in (("returned", len(trades)), ("added_unique", added),
                         ("first_ms", times[0]), ("last_ms", times[-1]),
                         ("has_more", result["has_more"])):
                if metadata.get(k) != v:
                    raise ValueError("ORACLE_PAGE_METADATA_MISMATCH_" + k)
            if result["has_more"] is False:
                if i != len(pages) - 1:
                    raise ValueError("ORACLE_PAGES_AFTER_END")
                ended = True
            cursor = times[-1]
        expected = "API_PAGINATION_ENDED_NOT_MARKET_COMPLETENESS" if ended else "INCOMPLETE_OR_UNKNOWN"
        if row.get("status") != expected:
            raise ValueError("ORACLE_FORGED_COMPLETENESS")
        values = dict(unique_trades=len(seen), unique_option_instruments=len(options),
            unique_put_instruments=len(puts), unique_call_instruments=len(calls),
            distinct_28_35d_put_instruments=len(eligible_puts),
            first_trade_ms=pages[0]["first_ms"] if pages else None,
            last_trade_ms=pages[-1]["last_ms"] if pages else None)
        for k, v in values.items():
            if row.get(k) != v:
                raise ValueError("ORACLE_AGGREGATE_MISMATCH_" + k)
        states.append(ended)
    expected = ("PUBLIC_TRADE_DAY_PAGINATION_COMPLETE_NOT_QUOTES" if all(states) else
                "PUBLIC_TRADE_DAY_PAGINATION_INCOMPLETE_OR_UNKNOWN")
    if report.get("status") != expected:
        raise ValueError("ORACLE_FALSE_SOURCE_STATUS")
    print(json.dumps(dict(oracle="INDEPENDENT_ORIGINAL_TRADE_PAGE_REPLAY_PASS",
        status=expected, coins_completed=sum(states),
        verified_original_trades=sum(r["unique_trades"] for r in rows),
        certified_option_lifecycles=0, promotion_authorized=False), sort_keys=True))
    return expected


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_deribit_target_day_tape_oracle OUT")
    replay(sys.argv[1])
