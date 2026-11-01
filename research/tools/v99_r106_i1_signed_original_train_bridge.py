"""Fail-closed 661-day ORIGINAL-source + independently SIGNED event bridge.

TRAIN only. Source-first independent original-byte oracles, then signed native
accounting, then numeric parity. No exchange-certified PnL, promotion or orders.
Prereg: V99_R106_I1_SIGNED_ORIGINAL_TRAIN_BRIDGE_PREREG_20261031.md
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from research.tools.v99_r106_i1_native_event_equity import (
    SCHEMA as JOURNAL_SCHEMA, replay, replay_signed,
)
from research.tools.v99_r106_i1_original_to_provisional_numeric import (
    run as source_bound_run,
)
from research.tools.v99_r106_i1_signed_event_source_gate import canonical
from research.tools.v99_r106_i1_train_numeric_gate import (
    DAYS, evaluate_provisional,
)
from research.verification.independent_v99_r106_i1_train_numeric_oracle import (
    verify as independent_numeric,
)

SCHEMA = "V99_I1_ORIGINAL_SOURCE_SIGNED_NATIVE_TRAIN_BRIDGE_V1"
FORBIDDEN = (
    "original_options_economic_train_certified",
    "original_source_receipts_independently_authenticated",
    "original_historical_economic_train_executed",
    "independent_original_trade_replay_verified",
    "historical_native_fee_certified",
    "freeze_authorized", "promotion_authorized", "validation_opened",
    "holdout_opened", "orders_enabled", "paper_publication_authorized",
)


def _unpromoted(result):
    if not isinstance(result, dict) or any(result.get(key, False) is not False
                                            for key in FORBIDDEN):
        raise ValueError("UNTRUSTED_CERTIFICATION_OR_PROMOTION")
    return result


def run(signal_path, original_quotes_root, journal_path):
    document = json.loads(Path(journal_path).read_text(encoding="utf-8"))
    if (not isinstance(document, dict)
            or document.get("schema") != JOURNAL_SCHEMA
            or document.get("fixture") is not False
            or set(document.get("scenarios", {})) != {"severe", "supersevere"}
            or not isinstance(document.get("journal_attestation"), str)
            or not document["journal_attestation"]
            or any(document.get(key) is True for key in FORBIDDEN)):
        raise ValueError("SIGNED_NONFIXTURE_ORIGINAL_JOURNAL_REQUIRED")

    # Must verify 661 ORIGINAL days, 180 decisions, complete held-option
    # source spine, independent market and numeric oracles BEFORE signed NAV.
    # Missing original archive aborts here. No fixture fallback.
    original = source_bound_run(signal_path, original_quotes_root, journal_path)
    _unpromoted(original)
    source_numeric = original.get("numeric_descriptive_only")
    if (original.get("original_signal_intents_checked") != 180
            or original.get("full_original_source_asset_week_books_independently_verified") != 180
            or original.get("original_complete_option_lifecycles_certified") != 0
            or not isinstance(source_numeric, dict)
            or source_numeric.get("days_per_scenario") != DAYS
            or source_numeric.get("status") !=
            "PROVISIONAL_NONFIXTURE_NUMERIC_DIAGNOSTIC_NOT_CERTIFIED"):
        raise ValueError("INCOMPLETE_ORIGINAL_SOURCE_DIAGNOSTIC")

    # Reproduce unsigned journal economics to detect changed event semantics
    # between the original-byte path and the signed native wallet path.
    unsigned = _unpromoted(replay(document))
    signed = _unpromoted(replay_signed(document))
    if (signed.get("signed_event_adapter_replayed") is not True
            or signed.get("fixture") is not False
            or signed.get("status") != "PROVISIONAL_UNCERTIFIED_NATIVE_EVENT_EQUITY"
            or any(signed.get(key) != unsigned.get(key) for key in (
                "initial_capital_usd", "scenarios", "fold_edge_snapshots",
                "exact_fold_edge_nav_available",
            ))):
        raise ValueError("SIGNED_ORIGINAL_NATIVE_WALLET_PARITY_MISMATCH")

    numeric = _unpromoted(evaluate_provisional(signed))
    independent_numeric(signed, numeric)
    if canonical(numeric) != canonical(source_numeric):
        raise ValueError("SIGNED_ORIGINAL_NUMERIC_SOURCE_PARITY_MISMATCH")
    if (numeric.get("source_fixture") is not False
            or numeric.get("numeric_screen_descriptive_only") is not True
            or numeric.get("days_per_scenario") != DAYS):
        raise ValueError("UNTRUSTED_SIGNED_NUMERIC_DIAGNOSTIC")

    return {
        "schema": SCHEMA,
        "status": "ORIGINAL_SOURCE_AND_SIGNED_EVENT_SOFTWARE_PARITY_ONLY",
        "original_signal_intents_checked": 180,
        "original_quote_event_identities_checked":
            original["original_quote_event_identities_checked"],
        "original_source_asset_week_books_checked": 180,
        "signed_661d_event_wallet_replayed": True,
        "signed_original_numeric_parity_sha256":
            hashlib.sha256(canonical(numeric)).hexdigest(),
        "numeric_descriptive_only": numeric,
        "original_complete_option_lifecycles_certified": 0,
        "native_fee_margin_lot_delivery_and_fills_still_require_external_proof": True,
        **{key: False for key in FORBIDDEN},
    }


def main(signal_path, original_quotes_root, journal_path, output_path):
    # Atomic publication: no result file is written on any source, signature,
    # parity or numeric failure. Do not overwrite an existing artifact.
    target = Path(output_path)
    if target.exists():
        raise ValueError("EXISTING_RESULT_IMMUTABLE")
    result = run(signal_path, original_quotes_root, journal_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({
        "status": result["status"], "days": DAYS,
        "signed_661d_event_wallet_replayed": True,
        "original_options_economic_train_certified": False,
        "promotion_authorized": False,
    }, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: python -m research.tools.v99_r106_i1_signed_original_train_bridge "
            "ORIGINAL_SIGNAL_JSON ORIGINAL_661D_QUOTES_ROOT "
            "SIGNED_NONFIXTURE_NATIVE_JOURNAL_JSON NEW_OUTPUT_JSON"
        )
    main(*sys.argv[1:])
