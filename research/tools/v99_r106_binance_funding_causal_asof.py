"""TRAIN-only optimistic earliest-possible causal funding as-of adapter.

Original Binance calc_time is not authenticated public release time. No economics.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.tools import v99_r106_binance_funding_original_train_source as original

START, END, STEP = original.START, original.END, original.STEP
HOUR = 3_600_000
EDGES = [START + n * HOUR for n in (0, 3172, 6345, 9518, 12691, 15864)]
SCHEMA = "V99_R106_BINANCE_CAUSAL_FUNDING_ASOF_SOURCE_ONLY_V1"


def select_asof(events: list[tuple[int, float]], decision_ms: int) -> tuple[int, float] | None:
    """Strictly before decision, never at or after the decision."""
    stamps = [x[0] for x in events]
    index = bisect.bisect_left(stamps, decision_ms) - 1
    return events[index] if index >= 0 else None


def summarize(events: list[tuple[int, float]]) -> dict:
    times = [x[0] for x in events]
    if times != sorted(set(times)):
        raise ValueError("NON_UNIQUE_OR_UNSORTED_SOURCE_TIMES")
    in_train = [(ts, rate) for ts, rate in events if START <= ts < END]
    if len(in_train) != 1983:
        raise ValueError("TRAIN_EVENT_COUNT_NOT_1983")
    nominal = set(range(START, END, STEP))
    offsets = [(ts - START) % STEP for ts, _ in in_train]
    if any(offset > 31 for offset in offsets):
        raise ValueError("SOURCE_TIMESTAMP_OUTSIDE_PREREG_BOUND")
    if {ts - offset for (ts, _), offset in zip(in_train, offsets)} != nominal:
        raise ValueError("SOURCE_NOMINAL_SLOTS_INCOMPLETE")
    if len(events) != len(set(times)):
        raise ValueError("DUPLICATE_SOURCE_EVENTS")
    digest = hashlib.sha256()
    fold_counts = []
    first_seen = 0
    current_slot_suppressed = 0
    previous_source = None
    for i, (a, b) in enumerate(zip(EDGES, EDGES[1:])):
        available = 0
        stale_gt_8h = 0
        for t in range(a, b, HOUR):
            index = bisect.bisect_left(times, t) - 1
            if index < 0:
                digest.update(f"{t},NONE,NONE\n".encode())
                continue
            ts, rate = events[index]
            if not ts < t:
                raise ValueError("CAUSAL_EVENT_NOT_BEFORE_DECISION")
            if ts != previous_source:
                first_seen += 1
                previous_source = ts
            if t in nominal:
                # At the nominal boundary, the event at t or t+1..31ms
                # cannot be used yet; only a prior original event is valid.
                assert ts < t
                current_slot_suppressed += 1
            available += 1
            stale_gt_8h += int(t - ts > STEP)
            digest.update(f"{t},{ts},{rate:.17g}\n".encode())
        fold_counts.append(dict(fold=i + 1, decisions=(b - a) // HOUR,
                                source_available=available, stale_gt_8h=stale_gt_8h))
    return dict(source_train_events=len(in_train), original_exact_clock_events=sum(x == 0 for x in offsets),
                original_offgrid_events=sum(x != 0 for x in offsets),
                source_hourly_decisions=sum(f["decisions"] for f in fold_counts),
                nominal_boundary_decisions_current_event_forbidden=current_slot_suppressed,
                first_seen_source_events_in_train_decisions=first_seen,
                five_folds=fold_counts, hourly_asof_sha256=digest.hexdigest())


def run(root: Path) -> dict:
    root = Path(root)
    publisher = original.run(root)
    if len(publisher.get("files", [])) != 44 or not all(
        f.get("publisher_checksum_verified") for f in publisher["files"]
    ):
        raise ValueError("ORIGINAL_44_PUBLISHER_CHECKSUMS_REQUIRED")
    report = dict(schema=SCHEMA, scope="[2021-12-09,2023-10-01)_TRAIN_ONLY",
                  provenance="BINANCE_PUBLISHER_CHECKSUMMED_FUNDING_CALC_TIME",
                  asof_semantics="OPTIMISTIC_EARLIEST_POSSIBLE_CALC_TIME_STRICTLY_BEFORE_DECISION",
                  assets={}, original_strict_exact_clock_gate_unchanged=True,
                  original_strict_exact_clock_observed_per_asset=821,
                  api_451_unresolved=True, public_release_time_certified=False,
                  account_settlement_certified=False, historical_fills_certified=False,
                  native_fee_tier_certified=False, economics_executed=False,
                  roi_calculated=False, validation_opened=False,
                  final_holdout_opened=False, frozen_changed=False,
                  paper_changed=False, orders_enabled=False, promotion=False)
    for symbol in original.SYMBOLS:
        events = []
        for month in original.MONTHS:
            p = root / "raw_ephemeral" / f"{symbol}-fundingRate-{month}.zip"
            events.extend((ts, rate) for ts, interval, rate in original.parse_csv(
                p.read_bytes(), month) if interval == 8)
        report["assets"][symbol] = summarize(events)
    if any(d["original_exact_clock_events"] != 821 or
           d["nominal_boundary_decisions_current_event_forbidden"] != 1983 or
           d["source_hourly_decisions"] != 15864 for d in report["assets"].values()):
        raise ValueError("FIXED_CLOCK_OR_DECISION_COUNT_MISMATCH")
    (root / "binance_funding_causal_asof_source_only.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(status="CAUSAL_ASOF_SOURCE_ONLY_NOT_CERTIFIED",
                          assets=report["assets"], promotion=False), sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_binance_funding_causal_asof OUT")
    run(Path(sys.argv[1]))
