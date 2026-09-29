from datetime import timedelta
import json
import pytest

from research.tools.v99_phase179_insurance_manifest import (
    TRAIN_START, FIREWALL, build_manifest,
)


def rows_daily(currency="XBt"):
    out = []
    t = TRAIN_START
    while t < FIREWALL:
        out.append({"timestamp": t.isoformat().replace("+00:00", "Z"), "currency": currency, "walletBalance": 1})
        t += timedelta(days=1)
    return out


def manifest(rows):
    raw = json.dumps(rows, sort_keys=True).encode()
    return build_manifest(rows, raw)


def test_complete_daily_train_passes_integrity_but_not_semantics():
    m = manifest(rows_daily())
    assert m["status"] == "INTEGRITY_PASS_DATA_ADMISSION_STILL_REQUIRES_SEMANTIC_AUDIT"
    assert m["by_currency"]["XBt"]["inferred_cadence_seconds"] == 86400
    assert not m["failures"]


def test_holdout_row_is_hard_failure():
    r = rows_daily()
    r.append({"timestamp": FIREWALL.isoformat(), "currency": "XBt", "walletBalance": 1})
    with pytest.raises(ValueError, match="firewall"):
        manifest(r)


def test_missing_month_fails_closed():
    r = [x for x in rows_daily() if not x["timestamp"].startswith("2022-06")]
    m = manifest(r)
    assert m["status"] == "FAIL"
    assert "XBt:missing_months" in m["failures"]
    assert "XBt:cadence_gaps" in m["failures"]


def test_late_start_fails_boundary_coverage():
    r = rows_daily()[10:]
    m = manifest(r)
    assert "XBt:boundary_coverage" in m["failures"]


def test_same_timestamp_different_currency_is_not_duplicate():
    r = rows_daily("XBt") + rows_daily("USDt")
    m = manifest(r)
    assert m["duplicate_keys"] == 0


def test_conflicting_same_key_fails():
    r = rows_daily()
    r.append({"timestamp": r[0]["timestamp"], "currency": "XBt", "walletBalance": 2})
    m = manifest(r)
    assert m["conflicting_duplicate_keys"] == 1
    assert "conflicting_duplicate_keys" in m["failures"]
