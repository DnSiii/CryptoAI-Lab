"""Fail-closed independent signed evidence gate for a SINGLE V99 I1 event.

A signature authenticates an auditor's claim over exact bytes, NOT fills,
archive completeness, strategy ROI, or permission to trade.
No trust anchor is embedded in the repository. Absent configuration -> HOLD.
Prereg: research/V99_R106_I1_SIGNED_EVENT_SOURCE_GATE_PREREG_20261031.md
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from pathlib import Path

SCHEMA = "V99_I1_INDEPENDENT_SIGNED_EVENT_SOURCE_V1"
REQUIRED = frozenset((
    "licensed_train_archive_manifest",
    "original_event_quote_or_delivery_receipt",
    "historical_account_fee_schedule",
    "historical_native_contract_lot_terms",
    "historical_margin_and_liquidation_terms",
    "independent_event_oracle_replay",
    "licensed_data_entitlement",
))


def _normalize(value):
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("NONFINITE_SIGNED_EVENT")
        return str(value)
    if isinstance(value, (tuple, list)):
        return [_normalize(x) for x in value]
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise ValueError("NONSTRING_SIGNED_EVENT_KEY")
        return {k: _normalize(v) for k, v in value.items()}
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("UNSUPPORTED_SIGNED_EVENT_TYPE")


def canonical(value):
    return json.dumps(_normalize(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def event_digest(event_type, wallet, **kwargs):
    if event_type not in ("OPEN", "MARK", "SETTLE_BATCH"):
        raise ValueError("UNKNOWN_SIGNED_EVENT_TYPE")
    return hashlib.sha256(canonical({
        "type": event_type, "wallet": wallet, "inputs": kwargs,
    })).hexdigest()


def _file_digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _regular(root, relative):
    if (not isinstance(relative, str) or not relative or
            Path(relative).is_absolute() or ".." in Path(relative).parts):
        raise ValueError("UNSAFE_SIGNED_EVIDENCE_PATH")
    path = root / relative
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("MISSING_OR_UNSAFE_SIGNED_EVIDENCE_FILE")
    return path


def verify_signed_event_attestation(evidence_root, expected_event_sha256):
    """Check externally anchored Ed25519 signature AND bound evidence bytes.

    The key path and its digest pin are provided by independently controlled
    deployment configuration, NEVER by the signed payload or the caller.
    """
    root = Path(evidence_root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("MISSING_SIGNED_EVIDENCE_ROOT")
    key = os.environ.get("V99_I1_TRUSTED_AUDITOR_PUBKEY")
    pin = os.environ.get("V99_I1_TRUSTED_AUDITOR_PUBKEY_SHA256")
    if not key or not pin or len(pin) != 64:
        raise ValueError("MISSING_INDEPENDENT_AUDITOR_TRUST_ANCHOR")
    key_path = Path(key)
    if not key_path.is_file() or key_path.is_symlink() or _file_digest(key_path) != pin.lower():
        raise ValueError("UNTRUSTED_INDEPENDENT_AUDITOR_KEY")
    payload = _regular(root, "attestation.json")
    signature = _regular(root, "attestation.sig")
    try:
        proc = subprocess.run(
            ["openssl", "pkeyutl", "-verify", "-pubin", "-inkey", str(key_path),
             "-rawin", "-in", str(payload), "-sigfile", str(signature)],
            capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("INDEPENDENT_AUDITOR_SIGNATURE_UNVERIFIABLE") from exc
    if proc.returncode != 0:
        raise ValueError("INDEPENDENT_AUDITOR_SIGNATURE_INVALID")
    try:
        document = json.loads(payload.read_bytes())
    except (ValueError, UnicodeError) as exc:
        raise ValueError("INVALID_SIGNED_ATTESTATION_JSON") from exc
    if (not isinstance(document, dict) or set(document) !=
            {"schema", "event_sha256", "evidence"} or
            document["schema"] != SCHEMA or
            document["event_sha256"] != expected_event_sha256 or
            not isinstance(document["evidence"], dict) or
            set(document["evidence"]) != REQUIRED):
        raise ValueError("SIGNED_ATTESTATION_NOT_BOUND_TO_EVENT")
    seen = set()
    for kind, item in document["evidence"].items():
        if (not isinstance(item, dict) or set(item) != {"file", "sha256"} or
                not isinstance(item["sha256"], str) or
                len(item["sha256"]) != 64):
            raise ValueError("INVALID_SIGNED_EVIDENCE_DESCRIPTOR")
        if item["file"] in seen:
            raise ValueError("REUSED_SIGNED_EVIDENCE_FILE")
        seen.add(item["file"])
        if _file_digest(_regular(root, item["file"])) != item["sha256"].lower():
            raise ValueError("SIGNED_ORIGINAL_EVIDENCE_SHA256_MISMATCH")
    # This only authenticates the independently signed evidence package.
    # Native execution, historical venue completeness and profitability remain
    # separate, mandatory, NEVER automatically certified by this function.
    return {"independent_signature_verified": True,
            "event_bound": True, "evidence_classes_bound": len(REQUIRED),
            "original_execution_fills_certified": False,
            "economic_train_executed": False, "promotion_authorized": False}
