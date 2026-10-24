"""Bounded first-party historical Deribit 6h PIT chain pagination, TRAIN only.

Pre-registered 2026-10-24. Ten fixed probes (first Monday per chronological
fold x BTC/ETH). No economics, no model selection and no future access.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from research.tools.v99_deribit_weekly_pit_1000_coverage import (
    BASE, DAY, MAX_RECENT_TRADES, decisions, expiry_and_strike,
)

HOUR = 3_600_000
WINDOW = 6 * HOUR
MAX_PAGES = 30
FLAGS = dict(economic_train_executed=False, validation_opened=False,
             holdout_opened=False, orders_enabled=False, promotion_authorized=False)


def fixed_slots():
    by_fold = {}
    for ts, fold in decisions():
        by_fold.setdefault(fold, ts)
    assert len(by_fold) == 5
    return [(by_fold[fold], fold, currency)
            for fold in range(1, 6) for currency in ("BTC", "ETH")]


def get_original(url):
    last = None
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers={
                "User-Agent": "CryptoAI-V99-complete6h-PIT/1.0",
                "Accept": "application/json",
            }), timeout=40) as response:
                if response.status != 200:
                    raise RuntimeError("HTTP_NON_200")
                raw = response.read(3_000_001)
                if len(raw) > 3_000_000:
                    raise RuntimeError("RESPONSE_TOO_LARGE")
                return raw
        except (HTTPError, URLError, TimeoutError) as exc:
            last = exc
            if isinstance(exc, HTTPError) and exc.code not in (408, 429, 500, 502, 503, 504):
                break
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"API_UNAVAILABLE: {last}")


def comparable(trades, currency, decision):
    groups = defaultdict(set)
    for v in trades:
        ts = int(v["timestamp"])
        if not (decision - WINDOW <= ts < decision):
            raise ValueError("OFF_WINDOW_TRADE")
        try:
            iv = float(v["iv"])
            index = float(v["index_price"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (math.isfinite(iv) and 0 < iv <= 1000 and
                math.isfinite(index) and index > 0):
            continue
        inst = expiry_and_strike(v.get("instrument_name"), currency)
        if inst is None:
            continue
        expiry, strike, side = inst
        if abs(math.log(strike / index)) > 0.15:
            continue
        days = (expiry - decision) / DAY
        band = "short" if 7 <= days <= 45 else ("long" if 46 <= days <= 120 else None)
        if band:
            groups[(band, side)].add(strike)
    counts = {band + "_" + side: len(groups[(band, side)])
              for band in ("short", "long") for side in ("C", "P")}
    return all(v >= 2 for v in counts.values()), counts


def collect_one(root, decision, fold, currency):
    start, cursor = decision - WINDOW, decision - 1
    seen = {}
    page_meta = []
    previous_boundary = None
    complete = False
    status = "SOURCE_INCOMPLETE"
    reason = ""
    for page in range(MAX_PAGES):
        query = dict(currency=currency, kind="option", start_timestamp=start,
                     end_timestamp=cursor, count=MAX_RECENT_TRADES,
                     include_old="true", sorting="desc")
        url = BASE + "?" + urlencode(query)
        raw = get_original(url)
        payload = json.loads(raw)
        if payload.get("error"):
            raise RuntimeError("EXCHANGE_ERROR: " + str(payload["error"]))
        result = payload.get("result")
        if not isinstance(result, dict) or not isinstance(result.get("trades"), list):
            raise ValueError("INVALID_SOURCE_SCHEMA")
        trades = result["trades"]
        if len(trades) > MAX_RECENT_TRADES:
            raise ValueError("OVER_LIMIT")
        if not trades:
            if result.get("has_more"):
                raise ValueError("EMPTY_PAGE_WITH_MORE")
            if previous_boundary is not None:
                raise ValueError("EMPTY_OVERLAP_PAGE")
            complete = True
            status = "SOURCE_COMPLETE"
            break
        stamps = [int(x["timestamp"]) for x in trades]
        if any(not (start <= t <= cursor) for t in stamps):
            raise ValueError("LOOKAHEAD_OR_OFF_WINDOW")
        if stamps != sorted(stamps, reverse=True):
            raise ValueError("NON_MONOTONIC_TIMESTAMP_PAGE")
        ids = [str(x["trade_id"]) for x in trades]
        if len(ids) != len(set(ids)):
            raise ValueError("DUPLICATE_IDS_WITHIN_PAGE")
        if previous_boundary is not None and not previous_boundary.intersection(ids):
            raise ValueError("TIMESTAMP_BOUNDARY_OVERLAP_UNPROVEN")
        new = 0
        for trade, tid in zip(trades, ids):
            if tid in seen:
                if seen[tid] != trade:
                    raise ValueError("SAME_TRADE_ID_DIFFERENT_PAYLOAD")
            else:
                seen[tid] = trade
                new += 1
        if new == 0:
            raise ValueError("PAGINATION_STALLED")
        filename = f"pit6h_f{fold}_{currency}_page{page:02d}.json"
        (root / filename).write_bytes(raw)
        oldest = min(stamps)
        boundary = {tid for tid, ts in zip(ids, stamps) if ts == oldest}
        page_meta.append(dict(page=page, query_start_ms=start, query_end_ms=cursor,
                              file=filename, sha256=hashlib.sha256(raw).hexdigest(),
                              source_count=len(trades), new_unique=new,
                              oldest_ms=oldest, newest_ms=max(stamps),
                              has_more=bool(result.get("has_more")),
                              boundary_ids=sorted(boundary)))
        if not result.get("has_more"):
            complete = True
            status = "SOURCE_COMPLETE"
            break
        if oldest >= cursor:
            raise ValueError("NON_PROGRESSING_TIMESTAMP_CURSOR")
        previous_boundary = boundary
        cursor = oldest  # inclusive overlap: do not drop same-ms trades
    if not complete:
        reason = "MAX_30_PAGES_WITH_HAS_MORE"
    trades = list(seen.values())
    covered, counts = comparable(trades, currency, decision)
    return dict(decision_ms=decision, fold=fold, currency=currency,
                status=status, reason=reason, pages=page_meta,
                unique_trades=len(trades), near_atm_2strike_4group=covered if complete else False,
                diagnostic_counts=counts, last_cursor_ms=cursor)


def main(directory):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for decision, fold, currency in fixed_slots():
        try:
            row = collect_one(root, decision, fold, currency)
        except Exception as exc:
            row = dict(decision_ms=decision, fold=fold, currency=currency,
                       status="SOURCE_ERROR", reason=f"{type(exc).__name__}: {exc}",
                       pages=[], unique_trades=0, near_atm_2strike_4group=False)
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != "pages"},
                         sort_keys=True), flush=True)
    report = dict(schema="V99_DERIBIT_COMPLETE_6H_PIT_PROBE_V1",
                  endpoint=BASE, page_count=MAX_RECENT_TRADES,
                  max_pages=MAX_PAGES, window_ms=WINDOW, rows=rows,
                  source_complete=sum(r["status"] == "SOURCE_COMPLETE" for r in rows),
                  near_atm_comparable=sum(r["near_atm_2strike_4group"] for r in rows),
                  sample_only=True, not_full_train=True, **FLAGS)
    (root / "probe_summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("COMPLETE", report["source_complete"], "/10; NEAR ATM",
          report["near_atm_comparable"], "/10; NO PNL, NO PROMOTION")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_deribit_complete_6h_pit_probe OUTPUT_DIR")
    main(sys.argv[1])
