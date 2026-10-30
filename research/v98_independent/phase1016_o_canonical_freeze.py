#!/usr/bin/env python3
"""V98 Phase1016 immutable cross-CPU O canonical target freeze; no PnL."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from phase1008_o_frozen_paths import ROOT, verify_o_source
from phase1015_canonical_transport import canonical_o_paths

ADAPTER_BLOB_SHA1 = "450f33d2147f8975d8dc34c06264104fa785058d"
FROZEN_CANONICAL_O = {
    "O_core_only": "7509cf79f55cb77c8af94d432333b27a40c7564a7fb475e9a258f62701f01d40",
    "O_full": "f92d9b8eb4712a4e0bdfd2eb40cfadd59f0242a7c3e7766189e031137792a267",
    "O_minus_opportunity": "1bd5d359289d56bf0a1e56eca7d831b2fdbe6755df5f5bac68690370b6f7d929",
    "O_minus_relative_value": "53cf2da5705f4142b2687b7d814cc02b858bcbdaadbccafbae51cfddb892994a",
    "O_minus_recovery": "42ed539ddfd8b2d141cfb8c2c0fa49f53463d7c1ec4e74cf7b5fd8cb48e37152",
}


def verify_canonical_source(root=ROOT):
    verify_o_source(root)
    raw=(Path(root)/"phase1015_canonical_transport.py").read_bytes()
    blob=b"blob "+str(len(raw)).encode()+b"\x00"+raw
    if hashlib.sha1(blob).hexdigest()!=ADAPTER_BLOB_SHA1:
        raise PermissionError("O_CANONICAL_TRANSPORT_SOURCE_DRIFT")
    return True


def frozen_canonical_o_paths(root=ROOT):
    verify_canonical_source(root)
    paths, receipt=canonical_o_paths(root)
    hashes=receipt["paths_sha256"]
    if tuple(hashes)!=tuple(FROZEN_CANONICAL_O) or hashes!=FROZEN_CANONICAL_O:
        raise PermissionError("O_CANONICAL_FIVE_TARGET_HASH_DRIFT")
    return paths,hashes,receipt


if __name__=="__main__":
    paths,hashes,receipt=frozen_canonical_o_paths()
    out={"phase":1016,"decision":"PASS_O_CANONICAL_FIVE_TARGETS_SOURCE_ONLY",
         "historical_pnl_computed":False,"validation_2025_read":False,
         "holdout_accessed":False,"external_benchmarks_used":False,
         "adapter_blob_sha1":ADAPTER_BLOB_SHA1,"paths_sha256":hashes,
         "canonical_diagnostics":receipt["diagnostics"]}
    (ROOT/"phase1016_o_canonical_freeze_result.json").write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"phase":1016,"decision":out["decision"],"paths_sha256":hashes},sort_keys=True))
