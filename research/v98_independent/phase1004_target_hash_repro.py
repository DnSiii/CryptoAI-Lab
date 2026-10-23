#!/usr/bin/env python3
"""V98 Phase1004: source-only frozen M hash reproducibility, no economic PnL."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
from phase866_k_sevenslot_source import ASSETS, PINS, pinned_training_frames
from phase900_m_persistent_growth_source import compose_m
from phase903_m_frozen_paths import FULL_PIN

ROOT=Path(__file__).resolve().parent
T=2683


def run(tag):
    close,high=pinned_training_frames(ROOT/"phase243_clean4_canonical")
    hashes=[]
    row=None
    for _ in range(3):
        frame=compose_m(close,high,excluded=frozenset())
        digest=hashlib.sha256(frame.to_csv(float_format="%.12g").encode()).hexdigest()
        hashes.append(digest)
        row={a:float(frame.iloc[T-1,j]) for j,a in enumerate(ASSETS)}
    result={
        "phase":1004,"tag":tag,"source_only":True,"historical_pnl_computed":False,
        "validation_2025_read":False,"holdout_accessed":False,
        "external_benchmarks_used":False,"frozen_source_modified":False,
        "python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,
        "canonical_source_sha256":PINS,"frozen_m_full_sha256":FULL_PIN,
        "observed_m_full_sha256":hashes,
        "all_in_process_equal":len(set(hashes))==1,
        "all_match_frozen":all(x==FULL_PIN for x in hashes),
        "tminus1_timestamp":str(close.index[T-1]),
        "untrusted_target_weights_tminus1":row,
        "decision":"PIN_MATCH" if all(x==FULL_PIN for x in hashes) else "HASH_DRIFT_UNRESOLVED",
    }
    path=ROOT/f"phase1004_target_hash_repro_{tag}.json"
    path.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"tag":tag,"decision":result["decision"],"hashes":hashes},sort_keys=True))
    return 0


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--tag",choices=("a","b"),required=True)
    raise SystemExit(run(p.parse_args().tag))
