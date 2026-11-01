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
import tempfile
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
    if event_type not in ("OPEN", "MARK", "SETTLE_BATCH", "JOURNAL"):
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
    # A symlink in ANY intermediate component is unsafe even when it
    # resolves back inside the evidence root.
    path = root
    for component in Path(relative).parts:
        path = path / component
        if path.is_symlink():
            raise ValueError("MISSING_OR_UNSAFE_SIGNED_EVIDENCE_FILE")
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("MISSING_OR_UNSAFE_SIGNED_EVIDENCE_FILE")
    return path


ORACLE_SCHEMA = "V99_I1_ORIGINAL_EVENT_INDEPENDENT_ORACLE_V1"
ORACLE_SOURCE_CLASSES = REQUIRED - {"independent_event_oracle_replay"}


def _strict_json_bytes(raw):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_SIGNED_ORACLE_JSON_KEY")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=unique_pairs)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("INVALID_SIGNED_ORACLE_JSON") from exc


def _verify_oracle_event_binding(oracle_bytes, descriptors, expected_event_sha256):
    # Parse EXACTLY the byte snapshot whose hash was checked against the
    # independent signature. Reopening a mutable file here is a TOCTOU bypass.
    oracle = _strict_json_bytes(oracle_bytes)
    expected_keys = {
        "schema", "fixture", "event_sha256", "replay_status",
        "historical_economic_train_certified", "promotion_authorized",
        "bound_source_sha256",
    }
    expected_sources = {
        kind: descriptors[kind]["sha256"].lower()
        for kind in ORACLE_SOURCE_CLASSES
    }
    if (not isinstance(oracle, dict) or set(oracle) != expected_keys
            or oracle["schema"] != ORACLE_SCHEMA
            or oracle["fixture"] is not False
            or oracle["event_sha256"] != expected_event_sha256
            or oracle["replay_status"] != "PASS"
            or oracle["historical_economic_train_certified"] is not False
            or oracle["promotion_authorized"] is not False
            or not isinstance(oracle["bound_source_sha256"], dict)
            or oracle["bound_source_sha256"] != expected_sources):
        raise ValueError("SIGNED_ORACLE_NOT_BOUND_TO_ORIGINAL_EVENT_AND_SOURCES")


def verify_signed_event_attestation(evidence_root, expected_event_sha256,
                                    expected_archive_manifest_sha256=None):
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
    if not key_path.is_file() or key_path.is_symlink():
        raise ValueError("UNTRUSTED_INDEPENDENT_AUDITOR_KEY")
    # Snapshot all signed bytes once: a mutable file cannot be replaced between
    # verifying its signature and parsing the JSON used for event authorization.
    key_bytes = key_path.read_bytes()
    if hashlib.sha256(key_bytes).hexdigest() != pin.lower():
        raise ValueError("UNTRUSTED_INDEPENDENT_AUDITOR_KEY")
    payload_bytes = _regular(root, "attestation.json").read_bytes()
    signature_bytes = _regular(root, "attestation.sig").read_bytes()
    if not (0 < len(payload_bytes) <= 1_000_000 and len(signature_bytes) == 64
            and 0 < len(key_bytes) <= 8192):
        raise ValueError("INVALID_INDEPENDENT_SIGNATURE_BYTES")
    try:
        with tempfile.TemporaryDirectory(prefix="v99-i1-signed-") as temporary:
            trusted = Path(temporary)
            (trusted / "auditor.pem").write_bytes(key_bytes)
            (trusted / "payload.json").write_bytes(payload_bytes)
            (trusted / "signature.bin").write_bytes(signature_bytes)
            proc = subprocess.run(
                ["openssl", "pkeyutl", "-verify", "-pubin",
                 "-inkey", str(trusted / "auditor.pem"), "-rawin",
                 "-in", str(trusted / "payload.json"),
                 "-sigfile", str(trusted / "signature.bin")],
                capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("INDEPENDENT_AUDITOR_SIGNATURE_UNVERIFIABLE") from exc
    if proc.returncode != 0:
        raise ValueError("INDEPENDENT_AUDITOR_SIGNATURE_INVALID")
    try:
        document = _strict_json_bytes(payload_bytes)
    except ValueError as exc:
        raise ValueError("INVALID_SIGNED_ATTESTATION_JSON") from exc
    if (not isinstance(document, dict) or set(document) !=
            {"schema", "event_sha256", "evidence"} or
            document["schema"] != SCHEMA or
            document["event_sha256"] != expected_event_sha256 or
            not isinstance(document["evidence"], dict) or
            set(document["evidence"]) != REQUIRED):
        raise ValueError("SIGNED_ATTESTATION_NOT_BOUND_TO_EVENT")
    seen = set()
    oracle_bytes = None
    for kind, item in document["evidence"].items():
        if (not isinstance(item, dict) or set(item) != {"file", "sha256"} or
                not isinstance(item["sha256"], str) or
                len(item["sha256"]) != 64):
            raise ValueError("INVALID_SIGNED_EVIDENCE_DESCRIPTOR")
        if item["file"] in seen:
            raise ValueError("REUSED_SIGNED_EVIDENCE_FILE")
        seen.add(item["file"])
        path = _regular(root, item["file"])
        if kind == "independent_event_oracle_replay":
            if path.stat().st_size > 1_000_000:
                raise ValueError("INVALID_SIGNED_ORACLE_JSON")
            oracle_bytes = path.read_bytes()
            actual_sha256 = hashlib.sha256(oracle_bytes).hexdigest()
        else:
            actual_sha256 = _file_digest(path)
        if actual_sha256 != item["sha256"].lower():
            raise ValueError("SIGNED_ORIGINAL_EVIDENCE_SHA256_MISMATCH")
    _verify_oracle_event_binding(oracle_bytes, document["evidence"], expected_event_sha256)
    # An independently signed package is not enough if it authenticates a
    # DIFFERENT original archive from the one the source-byte oracle replayed.
    if expected_archive_manifest_sha256 is not None:
        if (not isinstance(expected_archive_manifest_sha256, str)
                or len(expected_archive_manifest_sha256) != 64
                or any(c not in "0123456789abcdefABCDEF"
                       for c in expected_archive_manifest_sha256)):
            raise ValueError("INVALID_EXPECTED_ORIGINAL_ARCHIVE_MANIFEST_SHA256")
        if (document["evidence"]["licensed_train_archive_manifest"]["sha256"].lower()
                != expected_archive_manifest_sha256.lower()):
            raise ValueError("SIGNED_EVENT_ORIGINAL_ARCHIVE_MANIFEST_MISMATCH")
    # This only authenticates the independently signed evidence package.
    # Native execution, historical venue completeness and profitability remain
    # separate, mandatory, NEVER automatically certified by this function.
    return {"independent_signature_verified": True,
            "verified_attestation_sha256": hashlib.sha256(payload_bytes).hexdigest(),
            "event_bound": True, "evidence_classes_bound": len(REQUIRED),
            "original_execution_fills_certified": False,
            "economic_train_executed": False, "promotion_authorized": False}
