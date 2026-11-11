#!/usr/bin/env python3
"""Fail-closed V98 A3 frozen-candidate boundary. No performance or promotion claim."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

FROZEN_COMMIT = "2b43253c485ef705cc7f4bcce50dad0a450cedbd"
TRAINING_END_MS = 1767222000000  # 2025-12-31 23:00 UTC
REQUIRED = {"source_sha256", "slots_sha256", "price_manifest_sha256",
            "funding_manifest_sha256", "ledger_sha256", "replay_summary_sha256"}

def verify(lock_path: Path, evaluation_start_ms: int | None = None):
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("candidate_commit") != FROZEN_COMMIT:
        raise ValueError("FROZEN_CANDIDATE_COMMIT_MISMATCH")
    if lock.get("status") != "A3_REPRODUCIBILITY_LOCK_ONLY_UNVALIDATED":
        raise ValueError("INVALID_FROZEN_STATUS")
    if any(lock.get(k) is not False for k in
           ("holdout_accessed", "independent_validation", "promotion_eligible")):
        raise ValueError("FALSE_VALIDATION_OR_HOLDOUT_CLAIM")
    if lock.get("training_end") != "2025-12-31T23:00:00Z":
        raise ValueError("TRAINING_END_MISMATCH")
    if not REQUIRED.issubset(lock):
        raise ValueError("MISSING_FROZEN_EVIDENCE")
    hashes = list(lock["source_sha256"].values()) + [
        lock["slots_sha256"], lock["price_manifest_sha256"],
        lock["funding_manifest_sha256"], lock["replay_summary_sha256"]
    ] + list(lock["ledger_sha256"].values())
    if not hashes or any(not isinstance(x, str) or len(x) != 64
                         or any(c not in "0123456789abcdef" for c in x) for x in hashes):
        raise ValueError("INVALID_FROZEN_HASH")
    if set(lock["ledger_sha256"]) != {"1.0", "2.0", "4.0"}:
        raise ValueError("COST_SCENARIOS_MISSING")
    if evaluation_start_ms is not None and evaluation_start_ms <= TRAINING_END_MS:
        raise ValueError("EVALUATION_OVERLAPS_TRAINING")
    return {"status": "FROZEN_BOUNDARY_CONTRACT_ONLY",
            "candidate_commit": FROZEN_COMMIT, "independent_validation": False,
            "evaluation_data_read": False}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--lock", type=Path, required=True)
    p.add_argument("--evaluation-start-ms", type=int)
    a = p.parse_args()
    print(json.dumps(verify(a.lock, a.evaluation_start_ms), sort_keys=True))
