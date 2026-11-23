"""Fail-closed linkage of C27 source receipt and carry state. No PnL authorization.

A matching digest proves byte-level linkage, NOT independent provenance or a
valid economic starting state. This deliberately never calls an economic engine.
"""
import hashlib
import json
from pathlib import Path
from .v98_c27_carry_state_gate import validate_carry
from .v98_c27_prospective_source_preflight import validate as validate_sources


def link_inputs(root, receipt_path, carry_path, expected_carry_sha256):
    root = Path(root).resolve()
    receipt_path = Path(receipt_path).resolve()
    carry_path = Path(carry_path).resolve()
    source = validate_sources(root, receipt_path)
    carry = validate_carry(root, carry_path, source["start_utc"], expected_carry_sha256)
    state = json.loads(carry_path.read_bytes())
    if state["source_receipt_sha256"] != source["receipt_sha256"]:
        raise ValueError("CARRY_SOURCE_RECEIPT_MISMATCH")
    if receipt_path == carry_path:
        raise ValueError("CARRY_SOURCE_PATH_ALIAS")
    # The warmup digest is currently only a claimed hash. No authenticated
    # warmup replay, independent signature, or exchange provenance is established.
    return {
        "status": "LINKED_INPUTS_ONLY_NOT_AUTHENTICATED_NOT_PNL",
        "source_receipt_sha256": source["receipt_sha256"],
        "carry_sha256": carry["snapshot_sha256"],
        "warmup_receipt_sha256_claim": state["warmup_receipt_sha256"],
        "start_utc": source["start_utc"],
        "end_utc": source["end_utc"],
        "economic_replay_allowed": False,
        "missing": [
            "independent_source_and_carry_attestation",
            "authenticated_warmup_replay_and_positions",
            "frozen_variable_horizon_economic_executor",
            "native_cost_and_funding_reconciliation",
        ],
    }
