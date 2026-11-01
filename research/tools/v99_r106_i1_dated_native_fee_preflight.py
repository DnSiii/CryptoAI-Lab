"""I1 dated native-option fee arithmetic over an independently signed event bundle.

TRAIN-only lower-bound check. Signatures bind bytes, NOT venue/account truth,
historical fills, margin, settlement, economics or permission to promote.
Prereg: research/V99_R106_I1_DATED_NATIVE_FEE_ARITHMETIC_PREREG_20261101.md
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from research.tools.v99_r106_i1_signed_event_source_gate import (
    _regular, _strict_json_bytes, verify_signed_event_attestation,
)
from research.tools.v99_r106_i1_cost_bound_execution import charge_floor

SCHEMA = "V99_I1_HISTORICAL_NATIVE_OPTION_FEE_SCHEDULE_V1"
TRAIN_START_MS = 1639008000000
TRAIN_END_MS = 1696118400000
SCENARIOS = ("severe", "supersevere")


def _decimal(value, *, positive=False):
    if isinstance(value, bool):
        raise ValueError("INVALID_NATIVE_FEE_NUMBER")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("INVALID_NATIVE_FEE_NUMBER") from exc
    if not result.is_finite() or result < 0 or (positive and result <= 0):
        raise ValueError("INVALID_NATIVE_FEE_NUMBER")
    return result


def _hex(value):
    return isinstance(value, str) and len(value) == 64 and all(
        char in "0123456789abcdefABCDEF" for char in value
    )


def parse_schedule(document):
    """Validate dated intervals and reject account-tier ambiguity, no defaults."""
    if (not isinstance(document, dict)
            or set(document) != {"schema", "fixture", "venue", "account_tier",
                                "account_tier_original_document_sha256", "rows"}
            or document["schema"] != SCHEMA or document["fixture"] is not False
            or document["venue"] != "deribit"
            or not isinstance(document["account_tier"], str)
            or not document["account_tier"].strip()
            or not _hex(document["account_tier_original_document_sha256"])
            or not isinstance(document["rows"], list)):
        raise ValueError("UNVERIFIED_DATED_NATIVE_FEE_SCHEDULE")
    intervals = {"BTC": [], "ETH": []}
    for row in document["rows"]:
        if (not isinstance(row, dict) or set(row) != {
                "asset", "effective_from_ms", "effective_to_ms", "account_tier",
                "entry_per_lot_coin", "delivery_per_lot_coin",
                "cap_fraction", "native_lot_quantity"}
                or row["asset"] not in intervals
                or row["account_tier"] != document["account_tier"]
                or type(row["effective_from_ms"]) is not int
                or type(row["effective_to_ms"]) is not int
                or not 0 < row["effective_from_ms"]
                    < row["effective_to_ms"] <= 4102444800000):
            raise ValueError("INVALID_DATED_NATIVE_FEE_INTERVAL")
        for key in ("entry_per_lot_coin", "delivery_per_lot_coin",
                    "cap_fraction", "native_lot_quantity"):
            _decimal(row[key], positive=True)
        if _decimal(row["cap_fraction"]) > 1:
            raise ValueError("INVALID_NATIVE_FEE_CAP")
        intervals[row["asset"]].append(row)
    for asset, entries in intervals.items():
        entries.sort(key=lambda row: row["effective_from_ms"])
        for previous, following in zip(entries, entries[1:]):
            if previous["effective_to_ms"] > following["effective_from_ms"]:
                raise ValueError("OVERLAPPING_HISTORICAL_ACCOUNT_FEE_TERMS")
    return intervals


def _terms(intervals, asset, at_ms):
    if (asset not in intervals or type(at_ms) is not int
            or not TRAIN_START_MS <= at_ms < TRAIN_END_MS):
        raise ValueError("INVALID_NATIVE_FEE_CLOCK_OR_ASSET")
    candidates = [row for row in intervals[asset]
                  if row["effective_from_ms"] <= at_ms < row["effective_to_ms"]]
    if len(candidates) != 1:
        raise ValueError("MISSING_OR_AMBIGUOUS_HISTORICAL_ACCOUNT_FEE_TERMS")
    return candidates[0]


def calculate_minimum_fee(document, *, event_type, asset, at_ms,
                          native_lots, premiums_coin=None,
                          strikes_usd=None, delivery_index_usd=None):
    """Two-leg option fee, independently dated, capped leg-by-leg.

    The supplied premium/index/contract identity MUST be source-bound upstream.
    No discounts or netting across legs are inferred.
    """
    terms = _terms(parse_schedule(document), asset, at_ms)
    quantity = _decimal(native_lots, positive=True)
    lot = _decimal(terms["native_lot_quantity"], positive=True)
    if quantity % lot != 0:
        raise ValueError("HISTORICAL_NATIVE_LOT_INCREMENT_MISMATCH")
    cap = _decimal(terms["cap_fraction"], positive=True)
    if event_type in ("OPEN", "MARK"):
        # MARK is an executable-side close-cost liability, never an actual fill.
        # The native account schedule applies to either two-leg trade direction.
        if (not isinstance(premiums_coin, (tuple, list))
                or len(premiums_coin) != 2
                or strikes_usd is not None or delivery_index_usd is not None):
            raise ValueError("INVALID_ORIGINAL_ENTRY_PREMIUMS")
        bases = [_decimal(value, positive=True) for value in premiums_coin]
        rate = _decimal(terms["entry_per_lot_coin"], positive=True)
    elif event_type == "SETTLE_BATCH":
        if (not isinstance(strikes_usd, (tuple, list))
                or len(strikes_usd) != 2
                or premiums_coin is not None):
            raise ValueError("INVALID_ORIGINAL_DELIVERY_TERMS")
        high, low = [_decimal(value, positive=True) for value in strikes_usd]
        index = _decimal(delivery_index_usd, positive=True)
        if high <= low:
            raise ValueError("INVALID_ORIGINAL_DELIVERY_STRIKES")
        bases = [max(Decimal(0), strike - index) / index for strike in (high, low)]
        rate = _decimal(terms["delivery_per_lot_coin"], positive=True)
    else:
        raise ValueError("UNSUPPORTED_NATIVE_FEE_EVENT")
    legs = [min(quantity * rate, cap * quantity * value) for value in bases]
    return {"native_fee_minimum_coin": str(sum(legs, Decimal(0))),
            "leg_native_fee_coin": [str(value) for value in legs],
            "historical_native_fee_certified": False,
            "original_options_economic_train_certified": False,
            "promotion_authorized": False}


def signed_fee_preflight(evidence_root, expected_event_sha256,
                         expected_archive_manifest_sha256, *, event_type,
                         asset, at_ms, native_lots, scenario, fee_coin,
                         slippage_coin, premiums_coin=None, strikes_usd=None,
                         delivery_index_usd=None, immediate_close_premiums_coin=None):
    """Signature and exact schedule-byte binding precede native fee comparison."""
    if (not _hex(expected_event_sha256)
            or not _hex(expected_archive_manifest_sha256)
            or scenario not in SCENARIOS):
        raise ValueError("INVALID_NATIVE_FEE_PROVENANCE_REQUEST")
    verified = verify_signed_event_attestation(
        evidence_root, expected_event_sha256,
        expected_archive_manifest_sha256=expected_archive_manifest_sha256)
    if verified.get("independent_signature_verified") is not True:
        raise ValueError("MISSING_INDEPENDENT_NATIVE_FEE_SIGNATURE")
    root = Path(evidence_root)
    # Reopening an attestation after signature verification without comparing
    # its exact bytes would allow a concurrent swap of BOTH the descriptor and
    # the fee schedule (TOCTOU). Only consume the signed payload digest.
    attestation_bytes = _regular(root, "attestation.json").read_bytes()
    if hashlib.sha256(attestation_bytes).hexdigest() != verified.get("verified_attestation_sha256"):
        raise ValueError("SIGNED_FEE_ATTESTATION_CHANGED_AFTER_VERIFICATION")
    attestation = _strict_json_bytes(attestation_bytes)
    descriptor = attestation["evidence"]["historical_account_fee_schedule"]
    raw = _regular(root, descriptor["file"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != descriptor["sha256"].lower():
        raise ValueError("HISTORICAL_FEE_SCHEDULE_CHANGED_AFTER_SIGNATURE")
    schedule = _strict_json_bytes(raw)
    fee_inputs = dict(
        event_type=event_type, asset=asset, at_ms=at_ms,
        native_lots=native_lots, premiums_coin=premiums_coin,
        strikes_usd=strikes_usd, delivery_index_usd=delivery_index_usd)
    expected = calculate_minimum_fee(schedule, **fee_inputs)
    # The independent implementation must reexecute the actual signed
    # nonfixture event, not merely pass standalone synthetic unit tests.
    from research.verification.independent_v99_r106_i1_dated_native_fee_oracle import (
        verify as independently_verify_fee,
    )
    try:
        independently_verify_fee(schedule, expected, **fee_inputs)
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("SIGNED_NATIVE_FEE_INDEPENDENT_ORACLE_MISMATCH") from exc
    close_reserve = {}
    if immediate_close_premiums_coin is not None:
        if event_type != "OPEN":
            raise ValueError("IMMEDIATE_CLOSE_RESERVE_ONLY_FOR_SIGNED_OPEN")
        # The signed OPEN event already binds BOTH executable book sides.
        # This is a hypothetical immediate close liability, NOT a fill.
        close_inputs = dict(
            event_type="MARK", asset=asset, at_ms=at_ms,
            native_lots=native_lots, premiums_coin=immediate_close_premiums_coin)
        close = calculate_minimum_fee(schedule, **close_inputs)
        try:
            independently_verify_fee(schedule, close, **close_inputs)
        except (AssertionError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("SIGNED_IMMEDIATE_CLOSE_FEE_ORACLE_MISMATCH") from exc
        close_reserve = {
            "immediate_close_fee_minimum_coin": close["native_fee_minimum_coin"],
            "immediate_close_fee_is_hypothetical": True,
        }
    actual_fee = _decimal(fee_coin)
    actual_slip = _decimal(slippage_coin)
    stress_fee, stress_slip = charge_floor(scenario, native_lots)
    # Contractual expiry settles at the delivery index, not at a BBO fill.
    # Do not invent a settlement slippage debit or use it to cover native fees.
    if event_type == "SETTLE_BATCH":
        if actual_slip != 0:
            raise ValueError("INVENTED_CONTRACTUAL_SETTLEMENT_SLIPPAGE")
        stress_slip = Decimal(0)
    if (actual_fee < max(_decimal(expected["native_fee_minimum_coin"]), stress_fee)
            or actual_slip < stress_slip):
        raise ValueError("NATIVE_OR_SCENARIO_FRICTION_UNDERPAYMENT")
    return {**expected, **close_reserve,
            "signed_fee_schedule_sha256": hashlib.sha256(raw).hexdigest(),
            "scenario": scenario, "scenario_fee_coin": str(actual_fee),
            "scenario_slippage_coin": str(actual_slip),
            "status": "SIGNED_NATIVE_FEE_LOWER_BOUND_ONLY_NOT_EXECUTION_CERTIFICATION"}
