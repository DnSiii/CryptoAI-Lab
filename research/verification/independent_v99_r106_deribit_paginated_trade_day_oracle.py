"""Independent original-JSON-byte replay of Deribit 2022 trade pagination; no quote/ROI claim."""
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

START = int(datetime(2022, 1, 23, tzinfo=timezone.utc).timestamp() * 1000)
STOP = START + 86400000
NAME = re.compile(r"^(BTC|ETH)-(\d{1,2}[A-Z]{3}\d{2})-(\d+(?:\.\d+)?)-([PC])$")
FALSE_FLAGS = ("native_quotes_authenticated", "historical_fills_authenticated",
    "native_fee_tier_authenticated", "full_lifecycle_authenticated",
    "economic_trial_run", "validation_opened", "final_holdout_opened",
    "promotion_authorized", "paper_publication_authorized", "orders_enabled")


def verify(root):
    root = Path(root)
    report = json.loads((root / "original_paginated_trade_day_source_only.json").read_text())
    if report.get("schema") != "V99_R106_DERIBIT_ORIGINAL_PAGINATED_TRADE_DAY_SOURCE_ONLY_V1":
        raise ValueError("ORACLE_SCHEMA")
    if any(report.get(k) is not False for k in FALSE_FLAGS):
        raise ValueError("ORACLE_FORGED_PERMISSION")
    if report.get("original_661_day_quote_archive_delivered") is not False:
        raise ValueError("ORACLE_FAKE_QUOTE_ARCHIVE")
    if report.get("certified_option_lifecycles") != 0:
        raise ValueError("ORACLE_FAKE_LIFECYCLES")
    if report.get("trade_prints_are_not_executable_quotes") is not True:
        raise ValueError("ORACLE_FAKE_EXECUTION")
    if report.get("api_reported_complete_is_not_market_quote_coverage") is not True:
        raise ValueError("ORACLE_FAKE_COMPLETENESS")
    rows = report.get("rows")
    if not isinstance(rows, list) or [r.get("currency") for r in rows] != ["BTC", "ETH"]:
        raise ValueError("ORACLE_WRONG_CURRENCIES")
    both = True
    for row in rows:
        coin = row["currency"]
        if row.get("day") != "2022-01-23":
            raise ValueError("ORACLE_SEALED_DAY")
        pages = row.get("pages")
        if not isinstance(pages, list) or len(pages) > 30 or len(pages) != row.get("page_count"):
            raise ValueError("ORACLE_PAGE_COUNT")
        seen = {}
        previous_boundary = {}
        cursor = None
        earliest = None
        latest = None
        strike_sets = {}
        last_more = None
        for i, meta in enumerate(pages):
            if meta.get("file") != f"{coin}_{i:03d}.json" or meta.get("cursor") != cursor:
                raise ValueError("ORACLE_PAGE_LINEAGE")
            original = (root / "raw_ephemeral" / meta["file"]).read_bytes()
            if len(original) > 8_000_000 or hashlib.sha256(original).hexdigest() != meta.get("sha256"):
                raise ValueError("ORACLE_ORIGINAL_BYTES_HASH")
            payload = json.loads(original)
            if not isinstance(payload, dict) or "error" in payload:
                raise ValueError("ORACLE_JSONRPC_ERROR")
            obj = payload.get("result")
            if not isinstance(obj, dict) or type(obj.get("has_more")) is not bool:
                raise ValueError("ORACLE_MISSING_MORE")
            trades = obj.get("trades")
            if not isinstance(trades, list) or not 0 < len(trades) <= 1000:
                raise ValueError("ORACLE_TRADE_COUNT")
            local_ids = set()
            times = []
            first = {}
            newly_seen = 0
            for tr in trades:
                if not isinstance(tr, dict):
                    raise ValueError("ORACLE_BAD_TRADE")
                m = NAME.fullmatch(str(tr.get("instrument_name", "")))
                if m is None or m.group(1) != coin:
                    raise ValueError("ORACLE_NOT_COIN_OPTION")
                expiry = datetime.strptime(m.group(2), "%d%b%y").date()
                t = tr.get("timestamp")
                if type(t) is not int or not START <= t < STOP:
                    raise ValueError("ORACLE_TIME_LEAK")
                if not all(math.isfinite(float(tr[k])) and float(tr[k]) > 0 for k in ("price", "amount")):
                    raise ValueError("ORACLE_BAD_PRICE_AMOUNT")
                tid = tr.get("trade_id")
                if not isinstance(tid, str) or not tid or tid in local_ids:
                    raise ValueError("ORACLE_MISSING_DUPLICATE_ID")
                local_ids.add(tid)
                times.append(t)
                if cursor is not None and t == cursor:
                    first[tid] = tr
                if tid in seen:
                    if cursor is None or t != cursor or seen[tid] != tr:
                        raise ValueError("ORACLE_CONFLICTING_DUPLICATE")
                else:
                    seen[tid] = tr
                    newly_seen += 1
                    if m.group(4) == "P" and 28 <= (expiry - datetime(2022, 1, 23).date()).days <= 35:
                        strike_sets.setdefault(expiry.isoformat(), set()).add(m.group(3))
                earliest = t if earliest is None else min(earliest, t)
                latest = t if latest is None else max(latest, t)
            if times != sorted(times):
                raise ValueError("ORACLE_NONMONOTONE")
            if cursor is not None:
                if times[0] != cursor or not previous_boundary or any(
                        first.get(k) != v for k, v in previous_boundary.items()):
                    raise ValueError("ORACLE_MISSING_BOUNDARY")
            if not newly_seen:
                raise ValueError("ORACLE_NO_PROGRESS")
            new_cursor = times[-1]
            if cursor is not None and new_cursor <= cursor:
                raise ValueError("ORACLE_STUCK_CURSOR")
            previous_boundary = {tr["trade_id"]: tr for tr in trades if tr["timestamp"] == new_cursor}
            if len(previous_boundary) >= 1000 and obj["has_more"]:
                raise ValueError("ORACLE_AMBIGUOUS_BOUNDARY")
            expected = dict(file=meta["file"], sha256=meta["sha256"], cursor=cursor,
                last_timestamp=new_cursor, returned=len(trades), unique_new=newly_seen,
                has_more=obj["has_more"])
            if any(meta.get(k) != v for k, v in expected.items()):
                raise ValueError("ORACLE_FORGED_PAGE_META")
            cursor = new_cursor
            last_more = obj["has_more"]
            if not last_more and i != len(pages)-1:
                raise ValueError("ORACLE_EXTRA_PAGES_AFTER_TERMINAL")
        complete = bool(pages) and last_more is False
        expected_status = ("COMPLETE_REPORTED_TRADE_PAGINATION" if complete
                           else "INCOMPLETE_OR_UNCONFIRMED_TRADE_ACTIVITY")
        if row.get("status") != expected_status:
            raise ValueError("ORACLE_FORGED_COMPLETE_STATUS")
        eligible = {k: len(v) for k,v in sorted(strike_sets.items())}
        has_pair = any(v >= 2 for v in eligible.values())
        if row.get("eligible_28_35d_put_strikes_by_expiry") != eligible:
            raise ValueError("ORACLE_FORGED_ELIGIBLE_EXPIRIES")
        if row.get("eligible_two_distinct_traded_put_strikes") is not has_pair:
            raise ValueError("ORACLE_FORGED_TWO_STRIKES")
        if row.get("unique_trade_prints") != len(seen) or row.get("first_timestamp") != earliest:
            raise ValueError("ORACLE_FORGED_TRADE_COUNTS")
        if row.get("last_timestamp") != latest:
            raise ValueError("ORACLE_FORGED_LAST_TIME")
        both = both and complete and has_pair
    expected = ("TRADE_ACTIVITY_FEASIBLE_QUOTES_STILL_MISSING" if both
                else "INCOMPLETE_OR_UNCONFIRMED_TRADE_ACTIVITY")
    if report.get("status") != expected:
        raise ValueError("ORACLE_FORGED_AGGREGATE_STATUS")
    result = dict(status="INDEPENDENT_ORIGINAL_PAGINATED_TRADE_BYTES_REPLAY_PASS",
        source_status=expected, pages_by_asset={r["currency"]:r["page_count"] for r in rows},
        unique_trades_by_asset={r["currency"]:r["unique_trade_prints"] for r in rows},
        certified_option_lifecycles=0, economic_trial_run=False, promotion_authorized=False)
    (root / "independent_original_paginated_trade_day_oracle.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_deribit_paginated_trade_day_oracle OUT")
    verify(sys.argv[1])
