"""Pre-registered, weekly point-in-time option-trade information coverage; TRAIN ONLY.

This is a bounded availability test, not a strategy/backtest or an executable quote
surface. Each Monday 00:00 UTC uses only trades with timestamp < decision time.
1000 most recent option trades per 24h window are a LOWER-BOUND sample.
"""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from research.tools.v99_r106_d1_real_train_source_join import START, END, FOLD_EDGES

BASE = "https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time"
DAY = 86_400_000
WEEK = 7 * DAY
MAX_RECENT_TRADES = 1000
MAX_AGE_MS = 6 * 3_600_000
MIN_DISTINCT_STRIKES = 2
FOLD_MIN_COVERAGE = 0.70
MIN_GOOD_FOLDS = 4
FLAGS = dict(economic_train_executed=False, validation_opened=False,
             holdout_opened=False, orders_enabled=False, promotion_authorized=False)


def decisions():
    # Monday midnight UTC; fixed before looking at any option prices/IV.
    start = datetime.fromtimestamp(START / 1000, timezone.utc)
    monday = start + timedelta(days=(7 - start.weekday()) % 7)
    if monday <= start:
        monday += timedelta(days=7)
    while int(monday.timestamp() * 1000) < END:
        ts = int(monday.timestamp() * 1000)
        fold = next(i for i in range(1, 6) if FOLD_EDGES[i-1] <= ts < FOLD_EDGES[i])
        yield ts, fold
        monday += timedelta(days=7)


def request_original(url):
    last = None
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers={"User-Agent": "CryptoAI-V99-PIT-coverage/1.0",
                                                "Accept": "application/json"}), timeout=25) as resp:
                if resp.status != 200:
                    raise ValueError("HTTP_NON_200")
                data = resp.read(2_500_001)
                if len(data) > 2_500_000:
                    raise ValueError("SOURCE_RESPONSE_TOO_LARGE")
                return data
        except (HTTPError, URLError, TimeoutError) as exc:
            last = exc
            if isinstance(exc, HTTPError) and exc.code not in (408, 429, 500, 502, 503, 504):
                break
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{type(last).__name__}: {last}")


def expiry_and_strike(inst, currency):
    # The exchange's dated option symbol: BTC-25MAR22-50000-C.
    bits = str(inst).split("-")
    if len(bits) != 4 or bits[0] != currency or bits[3] not in ("C", "P"):
        return None
    try:
        expiry = datetime.strptime(bits[1].upper(), "%d%b%y").replace(tzinfo=timezone.utc)
        expiry_ms = int(expiry.timestamp() * 1000) + 8 * 3_600_000
        strike = float(bits[2])
        if strike <= 0:
            return None
    except (ValueError, OverflowError):
        return None
    return expiry_ms, strike, bits[3]


def classify(trades, currency, decision):
    groups = defaultdict(set)
    invalid = 0
    future = 0
    for t in trades:
        stamp = int(t.get("timestamp", -1))
        if not (decision - DAY <= stamp < decision):
            future += 1
            continue
        inst = expiry_and_strike(t.get("instrument_name"), currency)
        try:
            iv = float(t.get("iv"))
        except (TypeError, ValueError):
            invalid += 1
            continue
        if inst is None or not (0 < iv <= 1000) or decision - stamp > MAX_AGE_MS:
            invalid += 1
            continue
        expiry, strike, side = inst
        days = (expiry - decision) / DAY
        band = "short" if 7 <= days <= 45 else ("long" if 46 <= days <= 120 else None)
        if band:
            groups[(band, side)].add((expiry, strike))
    available = all(len({strike for _, strike in groups[(band, side)]}) >= MIN_DISTINCT_STRIKES
                    for band in ("short", "long") for side in ("C", "P"))
    return available, {"short_calls": len(groups[("short", "C")]),
                       "short_puts": len(groups[("short", "P")]),
                       "long_calls": len(groups[("long", "C")]),
                       "long_puts": len(groups[("long", "P")]),
                       "invalid_or_stale": invalid, "off_window": future}


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    assert START == 1639008000000 and END == 1696118400000 and len(FOLD_EDGES) == 6
    rows = []
    for decision, fold in decisions():
        for currency in ("BTC", "ETH"):
            params = {"currency": currency, "kind": "option",
                      "start_timestamp": decision - DAY,
                      "end_timestamp": decision - 1,
                      "count": MAX_RECENT_TRADES,
                      "include_old": "true", "sorting": "desc"}
            record = {"decision_ms": decision, "fold": fold, "currency": currency,
                      "query_start_ms": decision - DAY, "query_end_ms": decision - 1}
            try:
                raw = request_original(BASE + "?" + urlencode(params))
                obj = json.loads(raw)
                if obj.get("error"):
                    raise ValueError("EXCHANGE_ERROR: " + str(obj["error"]))
                result = obj.get("result")
                if not isinstance(result, dict) or not isinstance(result.get("trades"), list):
                    raise ValueError("BAD_EXCHANGE_SCHEMA")
                trades = result["trades"]
                if len(trades) > MAX_RECENT_TRADES:
                    raise ValueError("UNEXPECTED_TRADE_COUNT")
                if any(not (decision-DAY <= int(t.get("timestamp", -1)) < decision)
                       for t in trades):
                    raise ValueError("LOOKAHEAD_OR_OFFWINDOW_SOURCE")
                eligible, counts = classify(trades, currency, decision)
                receipt = f"options_week_{decision}_{currency}.json"
                (out / receipt).write_bytes(raw)
                record.update(status="SOURCE_OK", source_count=len(trades),
                              has_more=bool(result.get("has_more")),
                              eligible_lower_bound=eligible, counts=counts,
                              sha256=hashlib.sha256(raw).hexdigest(),
                              receipt_file=receipt)
            except Exception as exc:
                record.update(status="SOURCE_ERROR", eligible_lower_bound=False,
                              error=f"{type(exc).__name__}: {exc}")
            rows.append(record)
            print(json.dumps({k:v for k,v in record.items()
                              if k not in ("sha256", "receipt_file")}, sort_keys=True), flush=True)
    fold_rows = []
    for fold in range(1, 6):
        for currency in ("BTC", "ETH"):
            subset = [r for r in rows if r["fold"] == fold and r["currency"] == currency]
            ok = sum(r["eligible_lower_bound"] for r in subset)
            source_errors = sum(r["status"] == "SOURCE_ERROR" for r in subset)
            fold_rows.append({"fold": fold, "currency": currency, "weekly_slots": len(subset),
                              "eligible_lower_bound": ok, "source_errors": source_errors,
                              "fraction": ok / len(subset) if subset else 0})
    good_folds = sum(all(next(x for x in fold_rows if x["fold"] == f and x["currency"] == c)["fraction"]
                             >= FOLD_MIN_COVERAGE for c in ("BTC", "ETH"))
                     for f in range(1, 6))
    report = {"schema": "V99_DERIBIT_OPTIONS_WEEKLY_PIT_TRAIN_COVERAGE_V2",
              "start_ms": START, "end_exclusive_ms": END, "fold_edges": FOLD_EDGES,
              "endpoint": BASE, "max_recent_trades": MAX_RECENT_TRADES,
              "lookback_ms": DAY, "max_trade_age_ms": MAX_AGE_MS,
              "min_distinct_strikes_per_band_side": MIN_DISTINCT_STRIKES,
              "fold_min_coverage": FOLD_MIN_COVERAGE, "min_good_folds": MIN_GOOD_FOLDS,
              "good_folds": good_folds,
              "coverage_gate": "PIT_SAMPLE_SUFFICIENT_FOR_NEXT_DESIGN"
                               if good_folds >= MIN_GOOD_FOLDS else "PIT_SAMPLE_INSUFFICIENT",
              "important_limit": "Most recent 1000 option trades are a lower-bound sample, "
                                 "not a full options chain or executable quotes. "
                                 "Failure cannot reject the entire options information family.",
              "rows": rows, "fold_summary": fold_rows, **FLAGS}
    (out / "pit_coverage.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print("PIT COVERAGE:", report["coverage_gate"], good_folds, "/5 folds; DATA_ONLY/HOLD")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_deribit_weekly_pit_1000_coverage OUT_DIR")
    main(sys.argv[1])
