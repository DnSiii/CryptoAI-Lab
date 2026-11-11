#!/usr/bin/env python3
"""V98 A3 reproducibility lock, NOT an independent validation or promotion."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

SCENARIOS = ("1.0", "2.0", "4.0")
SOURCE_FILES = (
    "research/v98_independent/v98_sevenslot_preregistered_a3.py",
    "research/v98_independent/v98_authenticated_compound_integration.py",
    "research/v98_independent/v98_compound_scenario_replay.py",
    "research/v98_independent/v98_causal_compound_sizing.py",
    "research/v98_independent/v98_phase243_training_reader.py",
    "research/v98_independent/phase243_native_funding_cashflow.py",
    "research/v98_independent/v98_sevenslot_weight_to_targets.py",
)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def lock(replay, slots, root, output, expected_commit):
    for path in (replay, slots, output):
        if "v98_independent" not in path.absolute().parts:
            raise ValueError("V98_NAMESPACE_REQUIRED")
    if len(expected_commit) != 40 or any(c not in "0123456789abcdef" for c in expected_commit):
        raise ValueError("INVALID_COMMIT")
    actual = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if actual != expected_commit:
        raise ValueError("CHECKOUT_COMMIT_MISMATCH")
    if subprocess.check_output(["git", "-C", str(root), "status", "--porcelain", "--", "research/v98_independent"], text=True).strip():
        raise ValueError("DIRTY_V98_SOURCE")
    summary = json.loads((replay / "compound_summary.json").read_text())
    gate = json.loads((replay / "chronological_gate.json").read_text())
    audit = json.loads((replay / "independent_accounting_audit.json").read_text())
    if summary.get("status") != "ECONOMIC_REPLAY_ONLY_NOT_VALIDATED_ENGINE":
        raise ValueError("UNEXPECTED_REPLAY_STATUS")
    if summary.get("holdout_accessed") is not False or gate.get("holdout_accessed") is not False:
        raise ValueError("HOLDOUT_BOUNDARY_VIOLATION")
    if gate.get("promotion_eligible") is not False or gate.get("gates", {}).get("independent_validation") is not False:
        raise ValueError("FALSE_INDEPENDENT_VALIDATION")
    if audit.get("all_accounting_gates_passed") is not True:
        raise ValueError("ACCOUNTING_NOT_PASSED")
    if sha(slots) != summary.get("slots_sha256"):
        raise ValueError("SLOT_HASH_MISMATCH")
    if set(summary.get("scenarios", {})) != set(SCENARIOS):
        raise ValueError("SCENARIO_MISMATCH")
    for scenario in SCENARIOS:
        item = summary["scenarios"][scenario]
        ledger = replay / ("compound_ledger_" + scenario + ".json")
        if item.get("hours") != 27048 or sha(ledger) != item.get("ledger_sha256"):
            raise ValueError("LEDGER_INTEGRITY_" + scenario)
    source_hashes = {name: sha(root / name) for name in SOURCE_FILES}
    result = {
        "status": "A3_REPRODUCIBILITY_LOCK_ONLY_UNVALIDATED",
        "candidate_commit": actual,
        "source_sha256": source_hashes,
        "slots_sha256": sha(slots),
        "price_manifest_sha256": summary["price_manifest_sha256"],
        "funding_manifest_sha256": summary["funding_manifest_sha256"],
        "replay_summary_sha256": sha(replay / "compound_summary.json"),
        "chronological_gate_sha256": sha(replay / "chronological_gate.json"),
        "accounting_audit_sha256": sha(replay / "independent_accounting_audit.json"),
        "ledger_sha256": {scenario: summary["scenarios"][scenario]["ledger_sha256"] for scenario in SCENARIOS},
        "training_end": "2025-12-31T23:00:00Z",
        "holdout_accessed": False,
        "independent_validation": False,
        "promotion_eligible": False,
        "next_gate": "SEPARATE_PROSPECTIVE_CHRONOLOGICAL_EVALUATION_WITH_NO_RETUNING",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", required=True, type=Path)
    parser.add_argument("--slots", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-commit", required=True)
    args = parser.parse_args()
    print(json.dumps(lock(args.replay, args.slots, args.root, args.output, args.expected_commit), sort_keys=True))
