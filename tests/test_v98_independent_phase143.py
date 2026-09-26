import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "v98_independent_phase143_sp500_data_only.py"
spec = importlib.util.spec_from_file_location("phase143", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def raw(rows):
    return ("observation_date,SP500\n" + "\n".join(rows) + "\n").encode()


def test_hash_is_value_sensitive_without_exposing_values():
    a = m.audit(raw(["2023-01-03,100", "2023-01-04,101"]))
    b = m.audit(raw(["2023-01-03,100", "2023-01-04,102"]))
    assert a["normalized_observations_sha256"] != b["normalized_observations_sha256"]
    serialized = __import__("json").dumps(a).lower()
    for forbidden in ("return", "correlation", "pnl", "profit", "drawdown", "sharpe", "payoff", "win_rate", "position", "signal"):
        assert forbidden not in serialized


def test_duplicate_and_order_gates_fail_closed():
    p = m.audit(raw(["2023-01-04,101", "2023-01-03,100", "2023-01-03,100"]))
    assert p["gates"]["unique_dates"] is False
    assert p["gates"]["strictly_increasing"] is False
    assert p["decision"] == "REJECT_DATA_QUALITY_NO_RESCUE"


def test_malformed_and_outside_window_fail_closed():
    p = m.audit(raw(["2022-12-30,99", "2023-01-03,not-a-number"]))
    assert p["counts"]["outside_window"] == 1
    assert p["counts"]["malformed"] == 1
    assert p["gates"]["all_inside_frozen_window"] is False
    assert p["gates"]["no_malformed"] is False
    assert p["decision"] == "REJECT_DATA_QUALITY_NO_RESCUE"


def test_schema_identity_fails_closed():
    bad = b"DATE,SP500\n2023-01-03,100\n"
    try:
        m.audit(bad)
    except RuntimeError as exc:
        assert "unexpected schema" in str(exc)
    else:
        raise AssertionError("schema mismatch must fail closed")
