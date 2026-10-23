#!/usr/bin/env python3
"""V98 Phase1010: cross-run O float64 target forensic; source-only, no PnL."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
from phase1008_o_frozen_paths import ROOT, PATHS, FROZEN_O, verify_o_source
from phase1006_o_sevenslot_source import pinned_o_bars, compose_o
from phase866_k_sevenslot_source import PINS


def capture(tag):
    verify_o_source()
    op, hi, lo, cl = pinned_o_bars(ROOT / "phase243_clean4_canonical")
    paths = compose_o(op, hi, lo, cl)
    arrays = {k:paths[k].to_numpy(float) for k in PATHS}
    hashes = {}
    for k, frame in paths.items():
        hashes[k] = {str(precision):hashlib.sha256(frame.to_csv(float_format=f"%.{precision}g").encode()).hexdigest()
                     for precision in (12,10,8,6)}
    np.savez_compressed(ROOT / f"phase1010_o_targets_{tag}.npz", **arrays)
    cpu = ""
    try:
        cpu = next((x.split(":",1)[1].strip() for x in Path("/proc/cpuinfo").read_text().splitlines() if x.startswith("model name")), "")
    except OSError:
        pass
    result = {"phase":1010,"tag":tag,"source_only":True,"historical_pnl_computed":False,
              "validation_2025_read":False,"holdout_accessed":False,
              "external_benchmarks_used":False,
              "python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,
              "cpu_model":cpu,"canonical_source_sha256":PINS,
              "frozen_target_sha256":FROZEN_O,"observed_display_hashes":hashes,
              "exact_12g_match_frozen":all(hashes[k]["12"]==FROZEN_O[k] for k in PATHS)}
    (ROOT / f"phase1010_o_{tag}.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"tag":tag,"cpu":cpu,"exact_12g_match_frozen":result["exact_12g_match_frozen"],
                      "full_hashes":hashes["O_full"]},sort_keys=True))


def compare(root):
    a = json.loads((root/"a"/"phase1010_o_a.json").read_text())
    b = json.loads((root/"b"/"phase1010_o_b.json").read_text())
    if a["canonical_source_sha256"] != b["canonical_source_sha256"] or a["frozen_target_sha256"] != b["frozen_target_sha256"]:
        raise PermissionError("CROSS_RUN_SOURCE_OR_FROZEN_PIN_DRIFT")
    stats = {}
    max_abs = 0.
    mask_changes = 0
    exact_equal = True
    with np.load(root/"a"/"phase1010_o_targets_a.npz") as x, np.load(root/"b"/"phase1010_o_targets_b.npz") as y:
        for path in PATHS:
            left,right=x[path],y[path]
            if left.shape!=(18288,4) or right.shape!=left.shape:
                raise ValueError("CROSS_RUN_TARGET_SHAPE_DRIFT")
            if not np.isfinite(left).all() or not np.isfinite(right).all():
                raise ValueError("CROSS_RUN_NONFINITE_TARGET")
            diff=np.abs(left-right)
            mx=float(diff.max())
            masks=int(np.count_nonzero((left>0)!=(right>0)))
            stats[path]={"max_abs":mx,"count_diff_exact":int(np.count_nonzero(diff)),
                         "count_diff_gt_1e12":int(np.count_nonzero(diff>1e-12)),
                         "count_diff_gt_1e10":int(np.count_nonzero(diff>1e-10)),
                         "count_diff_gt_1e8":int(np.count_nonzero(diff>1e-8)),
                         "active_mask_changes":masks,
                         "display_hash_equal":{str(p):a["observed_display_hashes"][path][str(p)]==b["observed_display_hashes"][path][str(p)]
                                               for p in (12,10,8,6)}}
            max_abs=max(max_abs,mx)
            mask_changes+=masks
            exact_equal &= mx==0
    decision = ("REPRODUCIBLE_EXACT" if exact_equal and a["exact_12g_match_frozen"] and b["exact_12g_match_frozen"] else
                "FLOAT_SERIALIZATION_DRIFT_QUARANTINE" if max_abs<=1e-10 and mask_changes==0 else
                "ECONOMIC_TARGET_DRIFT_UNRESOLVED")
    result={"phase":1010,"decision":decision,"source_only":True,"historical_pnl_computed":False,
            "economic_clearance":False,"cross_runner_max_abs":max_abs,"active_mask_changes":mask_changes,
            "process_a_cpu":a["cpu_model"],"process_b_cpu":b["cpu_model"],"paths":stats}
    (root/"phase1010_cross_runner_comparison.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"decision":decision,"max_abs":max_abs,"active_mask_changes":mask_changes,
                      "paths":stats},sort_keys=True))
    return 0


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--tag",choices=("a","b"))
    p.add_argument("--compare",type=Path)
    args=p.parse_args()
    if bool(args.tag)==bool(args.compare):
        p.error("exactly one of --tag or --compare required")
    raise SystemExit(compare(args.compare) if args.compare else capture(args.tag))
