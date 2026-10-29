"""Independent original I1 held-contract daily-event schedule oracle.

Does NOT import the source-spine compiler or its verifier. Native quote/source
identity is checked separately. This oracle checks complete event clocks and
lifecycle membership, not historical fills, native fees, margin, or profit.
"""
from __future__ import annotations

from datetime import datetime, timezone

from research.tools.v99_r106_i1_train_numeric_gate import DAYS, _expected_clock

SCHEMA = "V99_I1_INDEPENDENT_NATIVE_LIFECYCLE_SCHEDULE_ORACLE_V1"


def _expiry(symbol):
    if not isinstance(symbol, str):
        raise AssertionError("INVALID_HELD_OPTION_SYMBOL")
    fields = symbol.split("-")
    if len(fields) != 4 or fields[3] != "P":
        raise AssertionError("INVALID_HELD_OPTION_SYMBOL")
    try:
        d = datetime.strptime(fields[1].upper(), "%d%b%y").replace(
            hour=8, tzinfo=timezone.utc)
    except ValueError as exc:
        raise AssertionError("INVALID_HELD_OPTION_EXPIRY") from exc
    return int(d.timestamp() * 1000)


def verify(journal, report):
    if (journal.get("fixture") is not False
            or report.get("schema") != "V99_I1_ORIGINAL_SPINE_NATIVE_JOURNAL_PARITY_V1"
            or report.get("promotion_authorized") is not False):
        raise AssertionError("INDEPENDENT_SPINE_INPUT_NOT_QUARANTINED")
    # Independently pin the four immutable intraday TRAIN fold clocks.
    # Do not import the production spine's clock helper or trust its report.
    intraday_edges = tuple(int(datetime(y, m, d, h, tzinfo=timezone.utc)
                               .timestamp() * 1000) for y, m, d, h in (
        (2022, 4, 20, 4), (2022, 8, 30, 9),
        (2023, 1, 9, 14), (2023, 5, 21, 19),
    ))
    expected_clocks = tuple(sorted({*(_expected_clock(i) for i in range(DAYS)),
                                    *intraday_edges}))
    out = {}
    for scenario in ("severe", "supersevere"):
        opens = {}
        marks = {}
        due = {}
        for day in journal["scenarios"][scenario]:
            for event in day["events"]:
                kind, at, asset = event["kind"], event["at_ms"], event["asset"]
                if kind == "OPEN":
                    key = (asset, event["position_id"])
                    if key in opens:
                        raise AssertionError("INDEPENDENT_DUPLICATE_OPEN")
                    opens[key] = at
                elif kind == "MARK":
                    key = (asset, event["position_id"])
                    marks.setdefault(key, []).append(event)
                elif kind == "SETTLE_BATCH":
                    for name in event["position_ids"]:
                        key = (asset, name)
                        due.setdefault(key, []).append(at)
                else:
                    raise AssertionError("INDEPENDENT_UNKNOWN_NATIVE_EVENT")
        if set(marks) != set(opens) or set(due) != set(opens):
            raise AssertionError("INDEPENDENT_MISSING_OR_EXTRA_POSITION_LIFECYCLE")
        checked_marks = 0
        for key, at in opens.items():
            rows = marks[key]
            first = rows[0]
            short, long = first["short"]["symbol"], first["long"]["symbol"]
            if (first["short"]["asset"] != key[0]
                    or first["long"]["asset"] != key[0]
                    or short == long or _expiry(short) != _expiry(long)):
                raise AssertionError("INDEPENDENT_INVALID_HELD_CONTRACT_PAIR")
            expiry = _expiry(short)
            expected = [clock for clock in expected_clocks if at <= clock < expiry]
            actual = [row["at_ms"] for row in rows]
            if actual != expected:
                raise AssertionError("INDEPENDENT_HELD_MARK_GRID_MISMATCH")
            if due[key] != [expiry]:
                raise AssertionError("INDEPENDENT_EXPIRY_DUE_GRID_MISMATCH")
            for row in rows:
                if (row["short"]["symbol"] != short
                        or row["long"]["symbol"] != long):
                    raise AssertionError("INDEPENDENT_HELD_CONTRACT_CHANGED")
            checked_marks += len(rows)
        claimed = report["scenarios"][scenario]
        if (claimed["positions"] != len(opens)
                or claimed["source_mark_events"] != checked_marks
                or claimed["source_expiry_due_events"] != len(due)
                or claimed["native_event_schedule_matched"] is not True):
            raise AssertionError("INDEPENDENT_SPINE_REPORT_MISMATCH")
        out[scenario] = {"positions": len(opens), "verified_daily_marks": checked_marks}
    return {
        "schema": SCHEMA, "scenarios": out,
        "historical_native_economics_certified": False,
        "promotion_authorized": False,
    }
