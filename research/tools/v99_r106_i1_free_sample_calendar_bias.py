"""Calendar-only I1 source-evidence audit; NEVER economic or executable evidence.

Prereg: research/V99_R106_I1_FREE_SAMPLE_CALENDAR_BIAS_AUDIT_PREREG_20261029.md
Does not change I1 rules, trade schedule, cost model or source readiness.
"""
from __future__ import annotations

import calendar
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import eligible

UTC = timezone.utc
SCHEMA = "V99_I1_FREE_SAMPLE_MONTHLY_EXPIRY_CALENDAR_BIAS_V1"
SAMPLES = (("2022-05-01", "2022-05-02"), ("2023-01-01", "2023-01-02"))
MIN_DAYS, MAX_DAYS = 28, 35


def last_friday(year: int, month: int) -> datetime:
    if not (2021 <= year <= 2024 and 1 <= month <= 12):
        raise ValueError("INVALID_CALENDAR_MONTH")
    last = datetime(year, month, calendar.monthrange(year, month)[1], 8, tzinfo=UTC)
    return last - timedelta(days=(last.weekday() - 4) % 7)


def monthlies() -> tuple[datetime, ...]:
    return tuple(last_friday(year, month)
                 for year in range(2021, 2025) for month in range(1, 13))


def monthly_tenor(decision: datetime, expiries: tuple[datetime, ...]) -> dict:
    if (decision.tzinfo is None or decision.utcoffset() != timedelta(0)
            or decision.weekday() != 0 or decision.hour != 0
            or decision.minute != 0 or decision.second != 0):
        raise ValueError("NOT_FIXED_MONDAY_UTC_DECISION")
    candidates = [(expiry - decision).total_seconds() / 86400
                  for expiry in expiries if expiry > decision]
    eligible_days = [v for v in candidates if MIN_DAYS <= v <= MAX_DAYS]
    return {"decision_day": decision.date().isoformat(),
            "next_monthly_days": min(candidates),
            "monthly_tenor_days": eligible_days,
            "monthly_tenor_calendar_possible": bool(eligible_days)}


def audit() -> dict:
    grid = eligible(True)
    if (len(grid) != 90 or len(set(grid)) != 90
            or grid[0].isoformat() != "2021-12-13T00:00:00+00:00"
            or grid[-1].date().isoformat() != "2023-08-28"):
        raise ValueError("I1_FIXED_TRAIN_GRID_CHANGED")
    expiries = monthlies()
    rows = [monthly_tenor(decision, expiries) for decision in grid]
    by_day = {r["decision_day"]: r for r in rows}
    samples = []
    for source, monday in SAMPLES:
        if (datetime.fromisoformat(source).date()
                + timedelta(days=1) != datetime.fromisoformat(monday).date()
                or monday not in by_day):
            raise ValueError("SAMPLE_NOT_FIXED_MONDAY")
        samples.append({"source_day": source, **by_day[monday]})
    return {
        "schema": SCHEMA,
        "status": "SOURCE_SAMPLE_SELECTION_BIAS_AUDIT_ONLY",
        "fixed_monday_decisions": len(grid),
        "monthly_tenor_calendar_possible_mondays":
            sum(r["monthly_tenor_calendar_possible"] for r in rows),
        "monthly_tenor_calendar_impossible_mondays":
            sum(not r["monthly_tenor_calendar_possible"] for r in rows),
        "samples": samples,
        "both_negative_samples_calendar_ineligible":
            all(not r["monthly_tenor_calendar_possible"] for r in samples),
        "interpretation": "SAMPLED_ZERO_BOOKS_NOT_INDEPENDENT_LIQUIDITY_FAILURES"
            if all(not r["monthly_tenor_calendar_possible"] for r in samples)
            else "REQUIRES_INDEPENDENT_SOURCE_REVIEW",
        "monthly_only_not_complete_instrument_universe": True,
        "historical_listings_authenticated": False,
        "historical_executable_books_authenticated": False,
        "historical_option_lifecycles_certified": 0,
        "economic_train_executed": False,
        "roi_calculated": False,
        "strategy_rules_modified": False,
        "validation_opened": False,
        "holdout_opened": False,
        "orders_enabled": False,
        "promotion_authorized": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True, allow_nan=False))
