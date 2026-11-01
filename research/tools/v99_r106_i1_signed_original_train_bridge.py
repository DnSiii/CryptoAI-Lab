"""Fail-closed 661-day ORIGINAL-source + independently SIGNED event bridge.

TRAIN only. Source-first independent original-byte oracles, then signed native
accounting, then numeric parity. No exchange-certified PnL, promotion or orders.
Prereg: V99_R106_I1_SIGNED_ORIGINAL_TRAIN_BRIDGE_PREREG_20261031.md
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

from research.tools.v99_r106_i1_local_tape_import import FIRST, DAYS, SCHEMA as TAPE_SCHEMA

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



def verify_original_day_bytes(root, manifest_digest):
    """Rehash all 661 original compressed days AFTER signed replay, fail closed.

    The source-first oracle has already independently verified the original
    manifest and its compressed bytes. This final pass closes the gap between
    the source oracle and signed NAV publication if a concurrent writer
    mutates a day while signed accounting is executing.
    """
    root = Path(root)
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("ORIGINAL_SOURCE_DAY_CHANGED_DURING_SIGNED_REPLAY")
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest_digest:
        raise ValueError("ORIGINAL_SOURCE_INPUT_CHANGED_DURING_SIGNED_REPLAY")
    try:
        manifest = json.loads(raw)
        entries = manifest["days"]
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError("INVALID_SIGNED_ORIGINAL_DAY_MANIFEST") from exc
    if (manifest.get("schema") != TAPE_SCHEMA
            or manifest.get("train_start") != FIRST.isoformat()
            or len(entries) != DAYS
            or not isinstance(entries, list)):
        raise ValueError("INVALID_SIGNED_ORIGINAL_DAY_MANIFEST")
    for i, entry in enumerate(entries):
        expected_day = (FIRST + timedelta(days=i)).isoformat()
        expected_file = expected_day + ".csv.gz"
        if (not isinstance(entry, dict)
                or entry.get("date") != expected_day
                or entry.get("file") != expected_file
                or type(entry.get("rows")) is not int or entry["rows"] <= 0
                or not isinstance(entry.get("sha256"), str)
                or len(entry["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in entry["sha256"])):
            raise ValueError("INVALID_SIGNED_ORIGINAL_DAY_MANIFEST")
        path = root / expected_file
        if not path.is_file() or path.is_symlink():
            raise ValueError("ORIGINAL_SOURCE_DAY_CHANGED_DURING_SIGNED_REPLAY")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != entry["sha256"]:
            raise ValueError("ORIGINAL_SOURCE_DAY_CHANGED_DURING_SIGNED_REPLAY")
    return DAYS


def run(signal_path, original_quotes_root, journal_path):
    # The source and signed wallet must refer to the SAME original input bytes.
    # Missing files still reach the preexisting source-first archive veto.
    signal_file = Path(signal_path)
    manifest_file = Path(original_quotes_root) / "manifest.json"
    signal_entry = (hashlib.sha256(signal_file.read_bytes()).hexdigest()
                    if signal_file.is_file() else None)
    manifest_entry = (hashlib.sha256(manifest_file.read_bytes()).hexdigest()
                      if manifest_file.is_file() else None)

    def verify_source_stability(source_result):
        if signal_entry is None or manifest_entry is None:
            raise ValueError("MISSING_ORIGINAL_SOURCE_PROVENANCE_INPUTS")
        if (not signal_file.is_file() or not manifest_file.is_file()
                or hashlib.sha256(signal_file.read_bytes()).hexdigest() != signal_entry
                or hashlib.sha256(manifest_file.read_bytes()).hexdigest() != manifest_entry):
            raise ValueError("ORIGINAL_SOURCE_INPUT_CHANGED_DURING_SIGNED_REPLAY")
        if source_result.get("original_quote_manifest_sha256") != manifest_entry:
            raise ValueError("ORIGINAL_MANIFEST_SOURCE_ORACLE_DIGEST_MISMATCH")

    # Snapshot once: source oracle and signed wallet must consume identical
    # journal bytes even if the caller mutates its original file mid-run.
    journal_bytes = Path(journal_path).read_bytes()
    document = json.loads(journal_bytes)
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
    with tempfile.TemporaryDirectory(prefix="v99-i1-original-signed-") as temporary:
        snapshot = Path(temporary) / "immutable_journal.json"
        snapshot.write_bytes(journal_bytes)
        original = source_bound_run(signal_path, original_quotes_root, snapshot)
    _unpromoted(original)
    verify_source_stability(original)
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
    signed = _unpromoted(replay_signed(
        document, expected_archive_manifest_sha256=manifest_entry))
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

    verify_source_stability(original)
    verify_original_day_bytes(original_quotes_root, manifest_entry)
    return {
        "schema": SCHEMA,
        "original_causal_signal_input_sha256": signal_entry,
        "original_quote_manifest_input_sha256": manifest_entry,
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
    # A complete signed result becomes visible ONLY after successful serialization,
    # durable temporary write, and exclusive publication. An existing output or
    # symlink is immutable, including if another writer races with this process.
    target = Path(output_path)
    if target.exists() or target.is_symlink():
        raise ValueError("EXISTING_RESULT_IMMUTABLE")
    result = run(signal_path, original_quotes_root, journal_path)
    payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent,
            prefix=".v99-i1-signed-", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as exc:
            raise ValueError("EXISTING_RESULT_IMMUTABLE") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
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
