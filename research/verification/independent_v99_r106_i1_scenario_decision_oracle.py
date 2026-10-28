"""Independent 90-week x two-asset x two-cost-path intent/event audit.

Checks only ledger fidelity and OPEN accounting. A caller's RISK_VETO is
NOT independently authenticated without original quote/margin evidence.
Does not import the production ledger, selector, or economic evaluator.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC = timezone.utc
EDGES = tuple(int(datetime.fromisoformat(x).replace(tzinfo=UTC).timestamp()*1000)
              for x in ("2021-12-09T00:00:00", "2022-04-20T04:00:00",
                        "2022-08-30T09:00:00", "2023-01-09T14:00:00",
                        "2023-05-21T19:00:00", "2023-10-01T00:00:00"))
SCENARIOS = ("severe", "supersevere")
ASSETS = ("BTC", "ETH")


def audit(document):
    if document.get("fixture") is not False or "decisions" in document:
        raise AssertionError("INDEPENDENT_NONFIXTURE_SCENARIO_LEDGER_REQUIRED")
    ledgers = document.get("scenario_decisions")
    if not isinstance(ledgers, dict) or set(ledgers) != set(SCENARIOS):
        raise AssertionError("INDEPENDENT_MISSING_SCENARIO_LEDGERS")
    first = datetime(2021, 12, 13, tzinfo=UTC)
    grid = [(int((first+timedelta(days=7*i)).timestamp()*1000), asset)
            for i in range(90) for asset in ASSETS]
    common = None
    counts = {}
    for scenario in SCENARIOS:
        rows = ledgers[scenario]
        if not isinstance(rows, list) or len(rows) != 180:
            raise AssertionError("INDEPENDENT_INCOMPLETE_180_GRID")
        signals, expected = [], set()
        for row, (at, asset) in zip(rows, grid):
            fold = next((i for i in range(1, 6)
                         if EDGES[i-1] <= at < EDGES[i]), None)
            if (not isinstance(row, dict)
                    or set(row) != {"decision_ms", "asset", "fold", "signal",
                                   "action", "reason"}
                    or type(row["decision_ms"]) is not int
                    or row["decision_ms"] != at or row["asset"] != asset
                    or type(row["fold"]) is not int or row["fold"] != fold):
                raise AssertionError("INDEPENDENT_FORGED_GRID")
            signal, action, reason = row["signal"], row["action"], row["reason"]
            signals.append((at, asset, fold, signal))
            if action == "OPEN":
                if signal != "POSITIVE_EX_ANTE_PREMIUM" or reason != "FIXED_VERTICAL":
                    raise AssertionError("INDEPENDENT_FORGED_OPEN_SIGNAL")
                expected.add((at, asset))
            elif action == "CASH":
                allowed = {
                    "POSITIVE_EX_ANTE_PREMIUM": {"RISK_VETO", "NO_ELIGIBLE_FIXED_VERTICAL"},
                    "NO_PREMIUM": {"NO_PREMIUM"},
                    "NO_30D_HISTORY": {"NO_30D_HISTORY"},
                }
                if reason not in allowed.get(signal, set()):
                    raise AssertionError("INDEPENDENT_UNVERIFIED_CASH_REASON")
            else:
                raise AssertionError("INDEPENDENT_INVALID_ACTION")
        if common is None:
            common = signals
        elif common != signals:
            raise AssertionError("INDEPENDENT_ORIGINAL_SIGNAL_DIVERGENCE")
        actual = set()
        for day in document["scenarios"][scenario]:
            for event in day["events"]:
                if event.get("kind") != "OPEN":
                    continue
                key = (event.get("at_ms"), event.get("asset"))
                if key in actual:
                    raise AssertionError("INDEPENDENT_DUPLICATE_OPEN")
                actual.add(key)
                signal = event.get("signal")
                expected_row = next((r for r in rows if
                    (r["decision_ms"], r["asset"]) == key), None)
                if (not isinstance(signal, dict) or expected_row is None
                        or any(signal.get(k) != expected_row[k]
                               for k in ("decision_ms", "asset", "fold", "signal"))):
                    raise AssertionError("INDEPENDENT_UNBOUND_OPEN_SIGNAL")
        if actual != expected:
            raise AssertionError("INDEPENDENT_MISSING_OR_EXTRA_OPEN")
        counts[scenario] = len(actual)
    return {"independent_fixed_grid": 180,
            "severe_opens": counts["severe"],
            "supersevere_opens": counts["supersevere"],
            "scenario_exposure_divergence_allowed": True,
            "risk_veto_authenticated": False,
            "source_certified": False, "economic_train_certified": False,
            "promotion_authorized": False}
