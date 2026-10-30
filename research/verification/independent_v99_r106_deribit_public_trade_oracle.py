"""Independent original-byte verification for a bounded public trade probe (not quotes)."""
import hashlib
import json
import math
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

DAYS = ("2022-01-23", "2022-05-01")
COINS = ("BTC", "ETH")
FORBIDDEN = (
    "native_quotes_authenticated", "historical_fills_authenticated",
    "native_fee_tier_authenticated", "full_lifecycle_authenticated",
    "economic_trial_run", "validation_opened", "final_holdout_opened",
    "promotion_authorized", "paper_publication_authorized", "orders_enabled",
)


def replay(root):
    root = Path(root)
    result = json.loads((root / "trade_history_source_only.json").read_bytes())
    if result.get("schema") != "V99_R106_DERIBIT_PUBLIC_TRADE_HISTORY_SOURCE_ONLY_V1":
        raise ValueError("ORACLE_WRONG_SCHEMA")
    if any(result.get(k) is not False for k in FORBIDDEN):
        raise ValueError("ORACLE_UNAUTHORIZED_PERMISSION")
    if result.get("certified_option_lifecycles") != 0:
        raise ValueError("ORACLE_FAKE_LIFECYCLES")
    if result.get("original_661_day_quote_archive_delivered") is not False:
        raise ValueError("ORACLE_FAKE_QUOTE_ARCHIVE")
    if result.get("trade_prints_are_not_executable_quotes") is not True:
        raise ValueError("ORACLE_FAKE_EXECUTION")
    if result.get("original_trade_prints_do_not_certify_complete_day") is not True:
        raise ValueError("ORACLE_FAKE_COMPLETENESS")
    rows = result.get("rows")
    if not isinstance(rows, list) or len(rows) != 4 or result.get("query_count") != 4:
        raise ValueError("ORACLE_SCOPE_CHANGED")
    found = set()
    confirmed = {}
    for row in rows:
        coin, day = row.get("currency"), row.get("day")
        if coin not in COINS or day not in DAYS or (coin, day) in found:
            raise ValueError("ORACLE_WRONG_PAIR")
        found.add((coin, day))
        raw_path = root / "raw_ephemeral" / f"{coin}_{day}.json"
        state = row.get("status")
        if not raw_path.exists():
            if state not in ("UNKNOWN_TRANSPORT_OR_SCHEMA", "UNKNOWN_MALFORMED_SOURCE"):
                raise ValueError("ORACLE_MISSING_ORIGINAL_BYTES")
            if row.get("raw_sha256") is not None or row.get("returned_count") is not None:
                raise ValueError("ORACLE_INVENTED_ABSENT_SOURCE")
            confirmed[(coin, day)] = False
            continue
        original = raw_path.read_bytes()
        if hashlib.sha256(original).hexdigest() != row.get("raw_sha256"):
            raise ValueError("ORACLE_SOURCE_DIGEST_MISMATCH")
        payload = json.loads(original)
        if "error" in payload or not isinstance(payload.get("result"), dict):
            raise ValueError("ORACLE_JSONRPC_ERROR")
        trades = payload["result"].get("trades")
        if not isinstance(trades, list) or len(trades) > 100:
            raise ValueError("ORACLE_UNBOUNDED_SOURCE")
        left = int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp() * 1000)
        right = left + 86400000
        seen = set()
        times = []
        for trade in trades:
            if not isinstance(trade, dict):
                raise ValueError("ORACLE_NOT_TRADE")
            instrument = trade.get("instrument_name", "")
            if not re.fullmatch(coin + r"-\\d{1,2}[A-Z]{3}\\d{2}-\\d+-(P|C)", instrument):
                raise ValueError("ORACLE_NOT_OPTION")
            ts = trade.get("timestamp")
            if type(ts) is not int or ts < left or ts >= right:
                raise ValueError("ORACLE_TIME_LEAK")
            for key in ("price", "amount"):
                value = float(trade[key])
                if not math.isfinite(value) or value <= 0:
                    raise ValueError("ORACLE_BAD_TRADE")
            trade_id = trade.get("trade_id")
            if trade_id is not None:
                if trade_id in seen:
                    raise ValueError("ORACLE_DUPLICATE")
                seen.add(trade_id)
            times.append(ts)
        if times != sorted(times):
            raise ValueError("ORACLE_ORDER_CHANGED")
        values = dict(returned_count=len(trades), first_timestamp=min(times, default=None),
            last_timestamp=max(times, default=None), valid_option_contract_rows=len(trades),
            has_more=(payload["result"].get("has_more")
                if type(payload["result"].get("has_more")) is bool else None))
        if any(row.get(key) != value for key, value in values.items()):
            raise ValueError("ORACLE_REPORTED_COUNT_OR_TIME_MISMATCH")
        expected_status = "VERIFIED_FIRSTPARTY_PUBLIC_TRADE_PRINTS" if trades else "UNKNOWN_EMPTY"
        if state != expected_status:
            raise ValueError("ORACLE_WRONG_SOURCE_STATUS")
        confirmed[(coin, day)] = bool(trades)
    if found != {(coin, day) for coin in COINS for day in DAYS}:
        raise ValueError("ORACLE_INCOMPLETE_FIXED_SCOPE")
    target_ok = all(confirmed[(coin, "2022-01-23")] for coin in COINS)
    expected = ("PUBLIC_TRADE_HISTORY_AVAILABLE_NOT_EXECUTABLE" if target_ok
                else "PUBLIC_TRADE_HISTORY_UNCONFIRMED")
    if result.get("status") != expected:
        raise ValueError("ORACLE_FALSE_PROMOTION_OR_STATUS")
    print(json.dumps(dict(oracle="INDEPENDENT_ORIGINAL_BYTES_REPLAY_PASS",
        source_status=expected, verified_target_currencies=sum(
            confirmed[(coin, "2022-01-23")] for coin in COINS),
        certified_option_lifecycles=0, promotion_authorized=False), sort_keys=True))
    return expected


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_deribit_public_trade_oracle ROOT")
    replay(sys.argv[1])
