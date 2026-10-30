"""Independent original-byte causal funding as-of oracle; no primary adapter imports."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
import zipfile
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

from research.verification.independent_v99_r106_binance_funding_original_train_oracle import verify as verify_publisher

A = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
B = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
HOUR = 3_600_000
EIGHT_HOURS = 8 * HOUR
EDGES = [A + n * HOUR for n in (0, 3172, 6345, 9518, 12691, 15864)]
MONTHS = [f"{y}-{m:02d}" for y in (2021, 2022, 2023) for m in range(1, 13)
          if (y, m) >= (2021, 12) and (y, m) <= (2023, 9)]
SCHEMA = "V99_R106_BINANCE_CAUSAL_FUNDING_ASOF_SOURCE_ONLY_V1"


def reconstruct(root: Path, symbol: str) -> dict:
    raw = []
    for month in MONTHS:
        path = root / "raw_ephemeral" / f"{symbol}-fundingRate-{month}.zip"
        with zipfile.ZipFile(path) as z:
            members = [m for m in z.infolist() if not m.is_dir()]
            if len(members) != 1:
                raise ValueError("ORACLE_ZIP_MEMBERS")
            data = z.read(members[0]).decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(data))
        if not {"calc_time", "funding_interval_hours", "last_funding_rate"}.issubset(reader.fieldnames or []):
            raise ValueError("ORACLE_HEADERS")
        for row in reader:
            ts = int(row["calc_time"])
            interval = float(row["funding_interval_hours"])
            rate = float(row["last_funding_rate"])
            if not math.isfinite(rate) or interval != 8:
                raise ValueError("ORACLE_NON_8H_OR_NONFINITE")
            raw.append((ts, rate))
    if any(x[0] >= y[0] for x, y in zip(raw, raw[1:])):
        raise ValueError("ORACLE_DUPLICATE_OR_UNSORTED")
    train = [(t, r) for t, r in raw if A <= t < B]
    expected = set(range(A, B, EIGHT_HOURS))
    slots = {}
    for ts, rate in train:
        offset = (ts - A) % EIGHT_HOURS
        if offset > 31:
            raise ValueError("ORACLE_OFFSET_OUT_OF_BOUNDS")
        slots.setdefault(ts - offset, []).append((ts, rate))
    if len(train) != 1983 or set(slots) != expected or any(len(v) != 1 for v in slots.values()):
        raise ValueError("ORACLE_INCOMPLETE_NATIVE_SLOTS")
    timestamps = [t for t, _ in raw]
    digest = hashlib.sha256()
    folds = []
    last_ts = None
    new_events = 0
    boundaries = 0
    for number, (start, stop) in enumerate(zip(EDGES, EDGES[1:]), 1):
        covered = 0
        stale = 0
        for decision in range(start, stop, HOUR):
            # bisect_right(decision-1) is strictly less than decision,
            # independent of the primary bisect_left implementation.
            index = bisect_right(timestamps, decision - 1) - 1
            if index < 0:
                digest.update(f"{decision},NONE,NONE\n".encode())
                continue
            source_time, rate = raw[index]
            if source_time >= decision:
                raise ValueError("ORACLE_LOOKAHEAD")
            if source_time != last_ts:
                new_events += 1
                last_ts = source_time
            if decision in expected:
                if source_time >= decision:
                    raise ValueError("ORACLE_BOUNDARY_LOOKAHEAD")
                boundaries += 1
            covered += 1
            stale += int(decision - source_time > EIGHT_HOURS)
            digest.update(f"{decision},{source_time},{rate:.17g}\n".encode())
        folds.append(dict(fold=number, decisions=(stop-start)//HOUR,
                          source_available=covered, stale_gt_8h=stale))
    return dict(source_train_events=len(train),
                original_exact_clock_events=sum(t in expected for t, _ in train),
                original_offgrid_events=sum(t not in expected for t, _ in train),
                source_hourly_decisions=sum(x["decisions"] for x in folds),
                nominal_boundary_decisions_current_event_forbidden=boundaries,
                first_seen_source_events_in_train_decisions=new_events,
                five_folds=folds, hourly_asof_sha256=digest.hexdigest())


def verify(root: Path) -> dict:
    root = Path(root)
    verify_publisher(root)
    report = json.loads((root / "binance_funding_causal_asof_source_only.json").read_bytes())
    if report.get("schema") != SCHEMA or report.get("scope") != "[2021-12-09,2023-10-01)_TRAIN_ONLY":
        raise ValueError("ORACLE_SCOPE")
    if report.get("asof_semantics") != "OPTIMISTIC_EARLIEST_POSSIBLE_CALC_TIME_STRICTLY_BEFORE_DECISION":
        raise ValueError("ORACLE_FALSE_SEMANTICS")
    for k, v in {"original_strict_exact_clock_gate_unchanged": True,
                 "original_strict_exact_clock_observed_per_asset": 821,
                 "api_451_unresolved": True, "public_release_time_certified": False,
                 "account_settlement_certified": False, "historical_fills_certified": False,
                 "native_fee_tier_certified": False, "economics_executed": False,
                 "roi_calculated": False, "validation_opened": False,
                 "final_holdout_opened": False, "frozen_changed": False,
                 "paper_changed": False, "orders_enabled": False,
                 "promotion": False}.items():
        if report.get(k) != v:
            raise ValueError("ORACLE_FALSE_PERMISSION_" + k)
    if set(report.get("assets", {})) != {"BTCUSDT", "ETHUSDT"}:
        raise ValueError("ORACLE_SYMBOL_SET")
    for symbol in ("BTCUSDT", "ETHUSDT"):
        expected = reconstruct(root, symbol)
        if expected != report["assets"][symbol]:
            raise ValueError("ORACLE_CAUSAL_TRACE_DISAGREEMENT_" + symbol)
        if expected["nominal_boundary_decisions_current_event_forbidden"] != 1983:
            raise ValueError("ORACLE_MISSING_BOUNDARY")
    print(json.dumps(dict(oracle="INDEPENDENT_ORIGINAL_BYTES_CAUSAL_ASOF_PASS",
                          decision_hours_per_asset=15864,
                          strict_original_clock_events=821,
                          source_publication_certified=False, economics=False,
                          promotion=False), sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_binance_funding_causal_asof_oracle OUT")
    verify(Path(sys.argv[1]))
