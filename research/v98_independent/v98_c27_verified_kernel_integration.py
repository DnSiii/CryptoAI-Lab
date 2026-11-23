"""Research-only integration of verified prospective bars with explicit kernel state.

A SHA-256 match is byte integrity, NOT independent attestation. This function
does not promote C27, certify provenance, or authorize publication of PnL.
"""
import hashlib
import json
from pathlib import Path
from .v98_c27_prospective_replay_bridge import prepare
from .v98_c27_variable_horizon_kernel import continue_replay

def replay_verified_inputs(root, receipt_path, kernel_state_path, expected_state_sha256, scale=1.0):
    root = Path(root).resolve()
    state_path = Path(kernel_state_path).resolve()
    if "v98_independent" not in root.parts or root not in state_path.parents or not state_path.is_file():
        raise ValueError("C27_KERNEL_STATE_NAMESPACE")
    if not isinstance(expected_state_sha256, str) or len(expected_state_sha256) != 64:
        raise ValueError("C27_KERNEL_STATE_DIGEST_FORMAT")
    raw = state_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_state_sha256:
        raise ValueError("C27_KERNEL_STATE_DIGEST")
    package = prepare(root, receipt_path)
    state = json.loads(raw)
    # Kernel enforces complete exact state schema, causal history length, book
    # constraints and execution clock. No synthetic zero-state substitution.
    result = continue_replay(package["bars"], package["funding_by_hour"], scale, state)
    return {
        "status": "UNATTESTED_RESEARCH_REPLAY_NOT_VALIDATION",
        "source_gate": package["source_gate"],
        "state_sha256": expected_state_sha256,
        "kernel": result,
        "economic_replay_allowed": False,
        "missing": [
            "independent_exchange_source_attestation",
            "independently_reconciled_pre_window_kernel_checkpoint",
            "native_execution_cost_reconciliation",
            "independent_chronological_validation_and_holdout_gates",
        ],
    }
