"""Prevent production V13 generator/verifier schema drift (2026-11-05 incident)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = (ROOT / "scripts/paper_once_v13_incremental.py").read_text()
VERIFY = (ROOT / "scripts/verify_paper_cycle_v13.py").read_text()

def test_generator_emits_unrounded_notional_from_same_source_as_display():
    assert '"order_value_brl_unrounded": to_brl(' in GEN
    assert GEN.count('result.asset_order_notional.loc[timestamp, symbol]') >= 2
    assert '"order_value_brl": round(' in GEN

def test_verifier_remains_fail_closed_for_missing_raw():
    assert 'raw = adjustment.get("order_value_brl_unrounded")' in VERIFY
    assert 'if raw is None:' in VERIFY
    assert '0.0 < precise < 0.005' in VERIFY
    assert 'round(precise, 2) == displayed' in VERIFY
