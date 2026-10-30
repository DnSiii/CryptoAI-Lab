"""Independent original-byte Binance historical bid/ask oracle; never imports primary."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

START = int(datetime(2022, 1, 23, tzinfo=timezone.utc).timestamp() * 1000)
DAY = "2022-01-23"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
EXPECTED_SCHEMA = "V99_R106_BINANCE_BOOKTICKER_ORIGINAL_SAMPLE_SOURCE_ONLY_V1"
HEADERS = ("update_id", "best_bid_price", "best_bid_qty", "best_ask_price",
           "best_ask_qty", "transaction_time", "event_time")


def reconstruct(path: Path) -> dict:
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    check = path.with_name(path.name + ".CHECKSUM").read_bytes()
    expected = re.search(rb"\b([a-fA-F0-9]{64})\b", check)
    if expected is None or sha != expected.group(1).decode().lower():
        raise ValueError("ORACLE_PUBLISHER_SHA256")
    chosen = {}
    count = 0
    previous = -1
    first = last = None
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [m for m in z.infolist() if not m.is_dir()]
        if len(names) != 1 or not names[0].filename.endswith(".csv"):
            raise ValueError("ORACLE_ZIP_MEMBERS")
        with z.open(names[0]) as stream:
            rows = csv.reader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""))
            for row in rows:
                if count == 0 and tuple(x.strip().lower() for x in row) == HEADERS:
                    continue
                if len(row) != 7:
                    raise ValueError("ORACLE_COLUMNS")
                update_id = int(row[0])
                bid, bsize, ask, asize = map(float, row[1:5])
                trade, event = int(row[5]), int(row[6])
                if update_id < 0 or not all(math.isfinite(x) and x > 0 for x in
                                            (bid, bsize, ask, asize)):
                    raise ValueError("ORACLE_BAD_NATIVE_VALUES")
                if not (START <= trade <= event < START + 86_400_000
                        and ask > bid and event >= previous):
                    raise ValueError("ORACLE_NATIVE_CLOCK_OR_CROSSED")
                previous = event
                first = event if first is None else first
                last = event
                count += 1
                if count > 12_000_000:
                    raise ValueError("ORACLE_TOO_MANY_ROWS")
                # Independently associate a quote to a decision by ceiling to the
                # next UTC hour, then apply strict causal age and latest-row order.
                hour = (event - START + 3_599_999) // 3_600_000
                boundary = START + hour * 3_600_000
                if 1 <= hour <= 23 and event < boundary and boundary - event <= 300_000:
                    chosen[hour] = (event, bid, bsize, ask, asize, update_id)
    digest = hashlib.sha256()
    for hour in range(1, 24):
        decision = START + hour * 3_600_000
        q = chosen.get(hour)
        if q is None:
            digest.update(f"{decision},NONE\n".encode())
        else:
            digest.update((f"{decision},{q[0]},{q[1]:.17g},{q[2]:.17g},"
                           f"{q[3]:.17g},{q[4]:.17g},{q[5]}\n").encode())
    return dict(original_quote_rows=count, first_event_ms=first,
                last_event_ms=last, strict_hourly_asof_covered=len(chosen),
                strict_hourly_asof_required=23, hourly_asof_sha256=digest.hexdigest(),
                original_zip_sha256=sha)


def verify(root: Path) -> dict:
    root = Path(root)
    report = json.loads((root / "binance_bookticker_source_only.json").read_text())
    if report.get("schema") != EXPECTED_SCHEMA or report.get("day") != DAY:
        raise ValueError("ORACLE_SCOPE")
    for k, v in dict(economics_executed=False, historical_fills_certified=False,
                     account_funding_settlement_certified=False,
                     native_account_fee_tier_certified=False, okx_source=False,
                     i1_deribit_source=False, validation_opened=False,
                     final_holdout_opened=False, paper_changed=False,
                     frozen_changed=False, orders_enabled=False,
                     promotion=False).items():
        if report.get(k) != v:
            raise ValueError("ORACLE_FALSE_PERMISSION_" + k)
    if set(report.get("assets", {})) != set(SYMBOLS):
        raise ValueError("ORACLE_ASSETS")
    complete = True
    for symbol in SYMBOLS:
        item = report["assets"][symbol]
        path = root / "raw_ephemeral" / f"{symbol}-bookTicker-{DAY}.zip"
        if not path.exists():
            if item.get("publisher_sha256_verified") or item.get("status") != "SOURCE_HOLD":
                raise ValueError("ORACLE_MISSING_SOURCE_MISREPRESENTED")
            complete = False
            continue
        actual = reconstruct(path)
        if item.get("status") != "ORIGINAL_PUBLISHER_VERIFIED":
            raise ValueError("ORACLE_SOURCE_PRESENT_BUT_UNVERIFIED")
        for k, v in actual.items():
            if item.get(k) != v:
                raise ValueError("ORACLE_REPLAY_MISMATCH_" + symbol + "_" + k)
        if not item.get("publisher_sha256_verified"):
            raise ValueError("ORACLE_FALSE_PUBLISHER")
        complete &= actual["strict_hourly_asof_covered"] == 23
    expected_class = ("FIRST_PARTY_BEST_BID_ASK_SAMPLE_FEASIBLE_NOT_EXECUTION"
                      if complete else "SOURCE_HOLD")
    if report.get("classification") != expected_class:
        raise ValueError("ORACLE_FALSE_CLASSIFICATION")
    print(json.dumps(dict(oracle=("INDEPENDENT_NATIVE_QUOTE_REPLAY_PASS" if complete else
                                     "INDEPENDENT_SOURCE_HOLD_NOT_FULLY_REPLAYED"),
                          classification=expected_class, economics=False,
                          promotion=False), sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_binance_bookticker_native_quote_oracle OUT")
    verify(Path(sys.argv[1]))
