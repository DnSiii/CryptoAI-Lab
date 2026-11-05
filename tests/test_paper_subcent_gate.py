"""Regression tests execute the production V13 subcent verification block verbatim."""
import math
import textwrap
from pathlib import Path
import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/verify_paper_cycle_v13.py"
text = SOURCE.read_text()
start = text.index("            displayed = float(adjustment.get(")
end = text.index('            if adjustment.get("result_scope")', start)
BLOCK = textwrap.dedent(text[start:end])

def check(displayed, raw, delta=0.0000002):
    adjustment = {"order_value_brl": displayed}
    if raw is not None:
        adjustment["order_value_brl_unrounded"] = raw
    exec(BLOCK, {"adjustment": adjustment, "delta": delta, "math": math})

def test_positive_subcent():
    check(0.0, 0.00223)

@pytest.mark.parametrize("displayed,raw,delta", [
    (0.0, None, 0.0000002),
    (0.0, 0.0, 0.0000002),
    (0.0, -0.002, 0.0000002),
    (0.0, 0.005, 0.0000002),
    (0.0, 0.01, 0.0000002),
    (0.0, float("nan"), 0.0000002),
    (0.0, float("inf"), 0.0000002),
    (0.0, 0.00223, 0.0),
    (-0.01, 0.00223, 0.0000002),
])
def test_fail_closed(displayed, raw, delta):
    with pytest.raises(RuntimeError, match="movimentação sem valor executado"):
        check(displayed, raw, delta)

def test_regular_positive_order():
    check(12.34, None)
