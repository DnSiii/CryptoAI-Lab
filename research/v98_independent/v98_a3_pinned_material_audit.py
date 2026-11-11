#!/usr/bin/env python3
"""Verify the pinned V98 A3 replay against actual evidence bytes; never promote."""
import argparse
import hashlib
import json
from pathlib import Path
from research.v98_independent.v98_a3_material_evidence_gate import expected_hashes, verify_material

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def audit(root, lock_path, output):
    root=root.resolve()
    lock=json.loads(lock_path.read_text())
    expected=expected_hashes(lock)
    # Match each expected digest to one actual file, not to a claimed filename.
    # Only scan V98 evidence roots supplied by the caller.
    by_digest={}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink() and path != output:
            d=digest(path)
            by_digest.setdefault(d,[]).append(path)
    mapping={}
    used=set()
    for key,d in expected.items():
        candidates=[p for p in by_digest.get(d,[]) if p not in used]
        if len(candidates)!=1:
            raise ValueError(f"MISSING_OR_AMBIGUOUS_MATERIAL_EVIDENCE:{key}:{len(candidates)}")
        used.add(candidates[0])
        mapping[key]=str(candidates[0].relative_to(root))
    mapping_path=root/"v98_material_mapping.json"
    mapping_path.write_text(json.dumps(mapping,indent=2,sort_keys=True)+"\n")
    result=verify_material(lock_path,root,mapping_path)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--lock",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(audit(a.root,a.lock,a.output),sort_keys=True))
