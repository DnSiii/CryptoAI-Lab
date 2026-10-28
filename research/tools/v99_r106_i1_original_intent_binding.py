"""Bind independently replayed ORIGINAL 182 I1 signals to 180 fixed TRAIN intents.

SOURCE ONLY. Never emit trades, cash decisions, option fills or PnL.
Preregistered in research/V99_R106_I1_ORIGINAL_180_INTENT_BINDING_PREREG_20261028.md.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_i1_train_numeric_gate import _fold

SCHEMA = "V99_I1_ORIGINAL_180_CAUSAL_INTENTS_V1"
SIGNALS = {"POSITIVE_EX_ANTE_PREMIUM", "NO_PREMIUM", "NO_30D_HISTORY"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def bind(original_path: Path) -> dict:
    original_path = Path(original_path)
    source_bytes = original_path.read_bytes()
    source = json.loads(source_bytes)
    if (source.get("schema") != "V99_I1_ORIGINAL_TRAIN_CAUSAL_30D_SIGNAL_V1"
            or source.get("source_original") is not True
            or source.get("structural_only") is not True
            or source.get("observations") != 182
            or source.get("eligible_weeks") != 91
            or source.get("right_censored_weeks") != 3
            or source.get("source_okx_run") != 40019588739
            or source.get("source_dvol_run") != 40072202459
            or source.get("economic_train_executed") is not False
            or source.get("promotion_authorized") is not False):
        raise ValueError("UNTRUSTED_OR_NONORIGINAL_SIGNAL_REPORT")
    full_grid = [(int(day.timestamp() * 1000), asset)
                 for day in eligible() for asset in ("BTC", "ETH")]
    fixed_grid = [(int(day.timestamp() * 1000), asset)
                  for day in eligible(True) for asset in ("BTC", "ETH")]
    if len(full_grid) != 182 or len(fixed_grid) != 180 or full_grid[:180] != fixed_grid:
        raise ValueError("ORIGINAL_FIXED_TRAIN_SCHEDULE_CHANGED")
    rows = source.get("rows")
    if not isinstance(rows, list) or len(rows) != 182:
        raise ValueError("INCOMPLETE_ORIGINAL_182_SIGNAL_ROWS")
    intents = []
    for i, (row, (clock, asset)) in enumerate(zip(rows, full_grid)):
        if (not isinstance(row, dict)
                or type(row.get("decision_ms")) is not int
                or row["decision_ms"] != clock or row.get("asset") != asset
                or type(row.get("fold")) is not int
                or row["fold"] != _fold(clock)
                or row.get("signal") not in SIGNALS):
            raise ValueError("FORGED_ORIGINAL_CAUSAL_SIGNAL_GRID")
        if i < 180:
            intents.append({"decision_ms": clock, "asset": asset,
                            "fold": _fold(clock), "signal": row["signal"]})
    assert len(intents) == 180
    return {
        "schema": SCHEMA,
        "status": "ORIGINAL_SIGNALS_BOUND_NO_EXECUTABLE_OPTIONS_PROVENANCE",
        "source_original_signal_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "canonical_intents_sha256": hashlib.sha256(canonical(intents)).hexdigest(),
        "original_signal_observations": 182,
        "fixed_asset_week_intents": 180,
        "right_censored_excluded_asset_weeks": 2,
        "positive_fixed_intents": sum(r["signal"] == "POSITIVE_EX_ANTE_PREMIUM" for r in intents),
        "intents": intents,
        "actions_or_cash_veto_certified": False,
        "options_source_authenticated": False,
        "historical_native_fees_authenticated": False,
        "original_historical_economic_train_executed": False,
        "validation_opened": False,
        "holdout_opened": False,
        "orders_enabled": False,
        "promotion_authorized": False,
    }


def audit_proposed_decisions(manifest: dict, decisions: list) -> dict:
    """Only signal fidelity, NEVER authenticity of self-declared OPEN/CASH/veto."""
    intents = manifest["intents"]
    if not isinstance(decisions, list) or len(decisions) != 180:
        raise ValueError("MISSING_COMPLETE_FIXED_180_DECISION_LEDGER")
    positive_cash = 0
    for original, proposed in zip(intents, decisions):
        if not isinstance(proposed, dict) or any(proposed.get(k) != v for k, v in original.items()):
            raise ValueError("PROPOSED_DECISION_CONTRADICTS_ORIGINAL_SIGNAL")
        if proposed.get("action") not in ("OPEN", "CASH"):
            raise ValueError("INVALID_PROPOSED_DECISION_ACTION")
        if proposed["action"] == "OPEN" and original["signal"] != "POSITIVE_EX_ANTE_PREMIUM":
            raise ValueError("OPEN_WITHOUT_ORIGINAL_POSITIVE_SIGNAL")
        if proposed["action"] == "CASH" and original["signal"] == "POSITIVE_EX_ANTE_PREMIUM":
            positive_cash += 1
    return {"original_signals_match": True, "positive_cash_veto_unverified": positive_cash,
            "execution_certified": False, "promotion_authorized": False}


def main(source_path, output_path):
    result = bind(Path(source_path))
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "intents": 180,
                      "positive": result["positive_fixed_intents"],
                      "economic_train_executed": False, "promotion_authorized": False},
                     sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_original_intent_binding SIGNAL_JSON OUT_JSON")
    main(*sys.argv[1:])
