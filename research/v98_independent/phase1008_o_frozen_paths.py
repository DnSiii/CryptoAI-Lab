#!/usr/bin/env python3
"""V98 Phase1008 immutable O target freeze, source-only; fail closed."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from phase1006_o_sevenslot_source import ROOT, PATHS, pinned_o_bars, compose_o

SOURCE_BLOB_SHA1 = "1ea28013a1c958187e00d45e822da417ec58d601"
FROZEN_O = {
    "O_core_only": "fc9bcdd3d8408619630b18796bae1410eeab28e06a9b359f738aab60bee08d5c",
    "O_full": "af8b997e80a13d2accedce76692ab5d7e78fc3bf490a5a75820658fcb31b8df8",
    "O_minus_opportunity": "46b4896efb8e8a86313ccc932fe368d582b5f8c8dce1f30102b37d3763a9c861",
    "O_minus_relative_value": "80cb7a89602c04c2fe223fa211f0fb0b3cc543aa7532bbec55a131d30d870134",
    "O_minus_recovery": "33cc8953e9e0f6677e061d2c16b4ceea129ceb6b2b76f90f0b42ec065c7fde77",
}


def verify_o_source(root=ROOT):
    raw = (Path(root) / "phase1006_o_sevenslot_source.py").read_bytes()
    git_blob = b"blob " + str(len(raw)).encode() + b"\x00" + raw
    if hashlib.sha1(git_blob).hexdigest() != SOURCE_BLOB_SHA1:
        raise PermissionError("FROZEN_O_SOURCE_CODE_DRIFT")
    if tuple(FROZEN_O) != PATHS:
        raise PermissionError("FROZEN_O_PATH_REGISTRY_DRIFT")
    return True


def frozen_o_paths(root=ROOT):
    verify_o_source(root)
    op, hi, lo, cl = pinned_o_bars(Path(root) / "phase243_clean4_canonical")
    paths, diag = compose_o(op, hi, lo, cl, diagnostics=True)
    hashes = {k: diag["paths"][k]["sha256"] for k in PATHS}
    if hashes != FROZEN_O:
        raise PermissionError("FROZEN_O_TARGET_HASH_DRIFT")
    return paths, hashes


if __name__ == "__main__":
    paths, hashes = frozen_o_paths()
    receipt = {"phase":1008, "decision":"PASS_O_FIVE_TARGET_PINS_SOURCE_ONLY",
               "historical_pnl_computed":False, "validation_2025_read":False,
               "holdout_accessed":False, "external_benchmarks_used":False,
               "source_git_blob_sha1":SOURCE_BLOB_SHA1, "paths_sha256":hashes}
    (ROOT / "phase1008_o_target_freeze_result.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print(json.dumps(receipt,sort_keys=True))
