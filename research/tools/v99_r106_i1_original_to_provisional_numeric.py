"""V99 I1 nonfixture original-intent + original-BBO -> provisional numeric runner.

This closes the INTERNAL integration gap only. It does NOT authenticate
underlying indices, native lots, fee tier, margin, liquidation, delivery
index or hypothetical fills. It never certifies economic TRAIN or orders.
Preregistered: V99_R106_I1_NONFIXTURE_ORIGINAL_TO_NUMERIC_ORCHESTRATOR_PREREG_20261028.md
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from research.tools.v99_r106_i1_original_intent_binding import (
    bind, audit_proposed_decisions,
)
from research.verification.independent_v99_r106_i1_original_intent_oracle import (
    verify as independent_intents,
)
from research.verification.independent_v99_r106_i1_scenario_decision_oracle import (
    audit as independent_decisions,
)
from research.verification.independent_v99_r106_i1_market_path_oracle import (
    verify as independent_market_path,
)
from research.tools.v99_r106_i1_original_event_quote_identity import (
    audit as original_bbo,
)
from research.tools.v99_r106_i1_native_event_equity import (
    replay, SCHEMA as JOURNAL_SCHEMA,
)
from research.tools.v99_r106_i1_train_numeric_gate import evaluate_provisional
from research.verification.independent_v99_r106_i1_train_numeric_oracle import (
    verify as independent_numeric,
)

SCHEMA = "V99_I1_ORIGINAL_TO_PROVISIONAL_NUMERIC_ORCHESTRATION_V1"
FORBIDDEN = (
    "promotion_authorized", "freeze_authorized", "orders_enabled",
    "validation_opened", "holdout_opened", "paper_publication_authorized",
    "original_options_economic_train_certified",
    "original_source_receipts_independently_authenticated",
    "independent_original_trade_replay_verified",
    "historical_native_fee_certified",
    "original_historical_economic_train_executed",
)


def run(original_signal_path, original_quotes_root, journal_path):
    journal = json.loads(Path(journal_path).read_text(encoding="utf-8"))
    if (not isinstance(journal, dict)
            or journal.get("schema") != JOURNAL_SCHEMA
            or journal.get("fixture") is not False
            or set(journal.get("scenarios", {})) != {"severe", "supersevere"}
            or "decisions" in journal):
        raise ValueError("NONFIXTURE_TWO_SCENARIO_JOURNAL_REQUIRED")
    if any(journal.get(flag) is True for flag in FORBIDDEN):
        raise ValueError("SELF_DECLARED_SOURCE_CERTIFICATION_FORBIDDEN")

    original = bind(Path(original_signal_path))
    # Independent source-byte and canonical-intent verification, not
    # reliance on the production binding's self-reported counts.
    with tempfile.TemporaryDirectory() as temporary:
        manifest = Path(temporary) / "intents.json"
        manifest.write_text(json.dumps(original, sort_keys=True), encoding="utf-8")
        checked = independent_intents(original_signal_path, manifest)
    if (checked["original_intents_verified"] != 180
            or checked["positive_fixed_intents"] != original["positive_fixed_intents"]):
        raise ValueError("INDEPENDENT_ORIGINAL_SIGNAL_REPLAY_MISMATCH")

    ledgers = journal.get("scenario_decisions")
    if not isinstance(ledgers, dict) or set(ledgers) != {"severe", "supersevere"}:
        raise ValueError("SCENARIO_SPECIFIC_180_DECISIONS_REQUIRED")
    unverified_cash = {}
    for scenario in ("severe", "supersevere"):
        result = audit_proposed_decisions(original, ledgers[scenario])
        unverified_cash[scenario] = result["positive_cash_veto_unverified"]
    independent = independent_decisions(journal)
    if independent["independent_fixed_grid"] != 180:
        raise ValueError("INDEPENDENT_SCENARIO_LEDGER_MISMATCH")

    # Independent common-market path parity BEFORE original BBO and any NAV.
    market_path = independent_market_path(journal)
    if market_path["original_source_certified"] is not False:
        raise ValueError("INDEPENDENT_MARKET_ORACLE_FALSE_CERTIFICATION")

    # This must happen BEFORE any NAV, even provisional NAV, is calculated.
    # A missing original archive fails here, never falls back to fixtures.
    quote_identity = original_bbo(original_quotes_root, journal)
    if quote_identity["original_quote_events_checked"] <= 0:
        raise ValueError("ZERO_ORIGINAL_BBO_EVENT_IDENTITIES")
    if (quote_identity["original_underlying_index_bound"] is not False
            or quote_identity["source_size_unit_is_native_lot_certified"] is not False
            or quote_identity["promotion_authorized"] is not False):
        raise ValueError("UNTRUSTED_ORIGINAL_QUOTE_CERTIFICATION")

    equity = replay(journal)
    if equity["fixture"] is not False:
        raise ValueError("FIXTURE_EQUITY_FORBIDDEN")
    numeric = evaluate_provisional(equity)
    independent_numeric(equity, numeric)
    if any(numeric.get(flag) is True for flag in FORBIDDEN):
        raise ValueError("FORGED_PROVISIONAL_NUMERIC_CERTIFICATION")

    return {
        "schema": SCHEMA,
        "status": "PROVISIONAL_ORIGINAL_BBO_ONLY_NOT_NATIVE_ECONOMICS",
        "original_signal_intents_checked": 180,
        "original_positive_signal_intents": original["positive_fixed_intents"],
        "original_quote_event_identities_checked": quote_identity["original_quote_events_checked"],
        "original_quote_manifest_sha256": quote_identity["original_manifest_sha256"],
        "independent_common_market_observations": {
            "open_inventories": market_path["independent_common_open_inventories"],
            "mark_books": market_path["independent_common_mark_books"],
            "delivery_indices": market_path["independent_common_delivery_indices"],
        },
        "scenario_opens": {
            "severe": independent["severe_opens"],
            "supersevere": independent["supersevere_opens"],
        },
        "positive_signal_cash_decisions_without_authenticated_veto": unverified_cash,
        "numeric_descriptive_only": numeric,
        "original_underlying_index_authenticated": False,
        "native_contract_lots_authenticated": False,
        "historical_native_fee_tier_authenticated": False,
        "historical_margin_liquidation_authenticated": False,
        "original_delivery_index_authenticated": False,
        "vendor_capture_completeness_authenticated": False,
        "simulated_execution_certified": False,
        "original_complete_option_lifecycles_certified": 0,
        "original_options_economic_train_certified": False,
        "independent_original_trade_replay_verified": False,
        "freeze_authorized": False, "promotion_authorized": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False, "paper_publication_authorized": False,
    }


def main(original_signal_path, original_quotes_root, journal_path, output_path):
    report = run(original_signal_path, original_quotes_root, journal_path)
    Path(output_path).write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report["status"],
        "original_quote_event_identities_checked": report["original_quote_event_identities_checked"],
        "original_complete_option_lifecycles_certified": 0,
        "promotion_authorized": False,
    }, sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: python -m research.tools.v99_r106_i1_original_to_provisional_numeric "
            "ORIGINAL_SIGNAL_JSON ORIGINAL_661D_QUOTES_ROOT NONFIXTURE_NATIVE_JOURNAL_JSON OUT_JSON"
        )
    main(*sys.argv[1:])
