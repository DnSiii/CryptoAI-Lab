"""Independent recomputation of source/decision classifications, not source truth."""
from __future__ import annotations


def verify(books, journal, report):
    if report.get("schema") != "V99_I1_SOURCE_CASH_VETO_PROVENANCE_V1":
        raise AssertionError("ORACLE_SOURCE_VETO_SCHEMA")
    if any(report.get(k) is not False for k in (
            "original_archive_completeness_certified", "positive_cash_veto_economically_certified",
            "original_options_economic_train_certified", "promotion_authorized",
            "validation_opened", "holdout_opened", "orders_enabled")):
        raise AssertionError("ORACLE_SOURCE_VETO_FORGED_CERTIFICATION")
    raw = books.get("rows", [])
    if len(raw) != 180:
        raise AssertionError("ORACLE_SOURCE_VETO_MISSING_GRID")
    for scenario in ("severe", "supersevere"):
        proposed = journal["scenario_decisions"][scenario]
        if len(proposed) != 180:
            raise AssertionError("ORACLE_SOURCE_VETO_MISSING_DECISIONS")
        recomputed = {"observed_empty_tenor_cash": 0,
                      "positive_cash_unverified": 0,
                      "positive_opens_with_observed_book": 0,
                      "negative_signal_cash": 0}
        for i in range(180):
            b, d = raw[i], proposed[i]
            if tuple(b.get(k) for k in ("decision_ms", "asset", "fold", "signal")) != tuple(
                    d.get(k) for k in ("decision_ms", "asset", "fold", "signal")):
                raise AssertionError("ORACLE_SOURCE_VETO_GRID_DIVERGENCE")
            has_tenor_book = len(b["original_books"]) != 0
            if b["signal"] != "POSITIVE_EX_ANTE_PREMIUM":
                if d["action"] != "CASH" or d["reason"] != b["signal"]:
                    raise AssertionError("ORACLE_SOURCE_VETO_BAD_SIGNAL")
                recomputed["negative_signal_cash"] += 1
            elif d["action"] == "OPEN":
                if not has_tenor_book or d["reason"] != "FIXED_VERTICAL":
                    raise AssertionError("ORACLE_SOURCE_VETO_BAD_OPEN")
                recomputed["positive_opens_with_observed_book"] += 1
            elif d["action"] == "CASH":
                if not has_tenor_book:
                    if d["reason"] != "NO_ELIGIBLE_FIXED_VERTICAL":
                        raise AssertionError("ORACLE_SOURCE_VETO_BAD_EMPTY_CASH")
                    recomputed["observed_empty_tenor_cash"] += 1
                else:
                    if d["reason"] not in ("RISK_VETO", "NO_ELIGIBLE_FIXED_VERTICAL"):
                        raise AssertionError("ORACLE_SOURCE_VETO_BAD_CASH")
                    recomputed["positive_cash_unverified"] += 1
            else:
                raise AssertionError("ORACLE_SOURCE_VETO_INVALID_ACTION")
        if recomputed != report.get("scenarios", {}).get(scenario):
            raise AssertionError("ORACLE_SOURCE_VETO_CLASSIFICATION_MISMATCH")
    return {"independent_180_intents_per_scenario": True,
            "historical_economic_provenance_verified": False,
            "promotion_authorized": False}
