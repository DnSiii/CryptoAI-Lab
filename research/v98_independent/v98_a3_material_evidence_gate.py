#!/usr/bin/env python3
"""Material verification of V98 A3 lock against actual immutable evidence bytes.

No evaluation data are opened and no independent-validation claim is made.
"""
import argparse
import hashlib
import json
from pathlib import Path
from research.v98_independent.v98_a3_frozen_boundary_gate import verify

def expected_hashes(lock):
    hashes = {}
    for key in ("slots_sha256", "price_manifest_sha256", "funding_manifest_sha256", "replay_summary_sha256"):
        hashes[key] = lock[key]
    for key in ("source_sha256", "ledger_sha256"):
        for name, digest in lock[key].items():
            hashes[f"{key}/{name}"] = digest
    return hashes

def verify_material(lock_path: Path, evidence_root: Path, mapping_path: Path):
    boundary = verify(lock_path)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    expected = expected_hashes(lock)
    if not isinstance(mapping, dict) or set(mapping) != set(expected):
        raise ValueError("EVIDENCE_MAPPING_INCOMPLETE_OR_EXTRA")
    root = evidence_root.resolve(strict=True)
    seen = set()
    for key, rel in mapping.items():
        if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
            raise ValueError("INVALID_EVIDENCE_PATH")
        path = (root / rel).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file() or path in seen:
            raise ValueError("EVIDENCE_PATH_ESCAPE_OR_REUSE")
        seen.add(path)
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected[key]:
            raise ValueError(f"EVIDENCE_SHA256_MISMATCH:{key}")
    return {**boundary, "material_hashes_verified": len(expected),
            "independent_validation": False, "evaluation_data_read": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--mapping", required=True, type=Path,
                        help="JSON object mapping each hash key to a relative artifact path")
    args = parser.parse_args()
    print(json.dumps(verify_material(args.lock, args.evidence_root, args.mapping), sort_keys=True))
