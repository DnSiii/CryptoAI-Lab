"""Independent fail-closed SHA256 verification of immutable predecessor and raw receipts.

Run: python scripts/verify_v99_epoch_raw_evidence.py manifest.json evidence_root
Never writes outputs, generates trades, or approves economics.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from validate_v99_forward_epoch_manifest import validate


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def confined_file(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or name.startswith("/") or "\\" in name:
        raise ValueError("unsafe evidence path")
    p = Path(name)
    if any(part in ("", ".", "..") for part in p.parts):
        raise ValueError("unsafe evidence traversal")
    candidate = root / p
    if candidate.is_symlink() or any(parent.is_symlink() for parent in candidate.parents if parent != root.parent):
        raise ValueError("symlink evidence forbidden")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root.resolve(strict=True)) or not resolved.is_file():
        raise ValueError("evidence outside root or not a file")
    return resolved


def verify(manifest: dict, root: Path) -> dict:
    structural = validate(manifest)
    predecessor = manifest["predecessor"]
    predecessor_file = confined_file(root, predecessor["raw_evidence_path"])
    if digest_file(predecessor_file) != predecessor["ledger_sha256"]:
        raise ValueError("predecessor original bytes SHA256 mismatch")
    receipts = manifest.get("receipts", [])
    if not receipts:
        raise ValueError("zero original receipts: economic provenance remains blocked")
    paths = set()
    for r in receipts:
        name = r["raw_evidence_path"]
        if name in paths:
            raise ValueError("duplicate raw evidence path")
        paths.add(name)
        if digest_file(confined_file(root, name)) != r["raw_sha256"]:
            raise ValueError("raw receipt original bytes SHA256 mismatch")
    return {
        **structural,
        "predecessor_original_bytes_verified": True,
        "original_receipts_independently_verified": True,
        "raw_receipts_verified": len(receipts),
        "economic_validation": False,
        "real_orders_enabled": False,
        "note": "Byte hashes only; authenticity, fills, funding, costs and PnL NOT certified.",
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: verify_v99_epoch_raw_evidence.py manifest.json evidence_root")
    manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(verify(manifest, Path(sys.argv[2])), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
