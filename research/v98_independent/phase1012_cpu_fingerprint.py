#!/usr/bin/env python3
"""V98 Phase1012: source-only O/M hash CPU fingerprint; no historical PnL."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
from phase1008_o_frozen_paths import ROOT, FROZEN_O, verify_o_source
from phase1006_o_sevenslot_source import pinned_o_bars, compose_o
from phase900_m_persistent_growth_source import compose_m
from phase903_m_frozen_paths import FULL_PIN
from phase866_k_sevenslot_source import PINS, ASSETS


def run(tag):
    verify_o_source()
    folder=ROOT/"phase243_clean4_canonical"
    op,hi,lo,cl=pinned_o_bars(folder)
    paths=compose_o(op,hi,lo,cl)
    m=compose_m(cl,hi)
    def dig(frame,p):
        return hashlib.sha256(frame.to_csv(float_format=f"%.{p}g").encode()).hexdigest()
    observed={k:{"12":dig(v,12),"8":dig(v,8)} for k,v in paths.items()}
    observed["M_full"]={"12":dig(m,12),"8":dig(m,8)}
    cpu=""
    try:
        cpu=next((x.split(":",1)[1].strip() for x in Path("/proc/cpuinfo").read_text().splitlines() if x.startswith("model name")),"")
    except OSError:
        pass
    receipt={"phase":1012,"tag":tag,"source_only":True,"historical_pnl_computed":False,
             "validation_2025_read":False,"holdout_accessed":False,
             "external_benchmarks_used":False,"cpu":cpu,
             "python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,
             "canonical_source_sha256":PINS,"frozen_o":FROZEN_O,"frozen_m":FULL_PIN,
             "observed":observed,"o_exact_matches":all(observed[k]["12"]==v for k,v in FROZEN_O.items()),
             "m_exact_matches":observed["M_full"]["12"]==FULL_PIN}
    (ROOT/f"phase1012_cpu_{tag}.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"tag":tag,"cpu":cpu,"o_exact_matches":receipt["o_exact_matches"],
                      "m_exact_matches":receipt["m_exact_matches"],
                      "o_full":observed["O_full"],"m_full":observed["M_full"]},sort_keys=True))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--tag",required=True,choices=("ubuntu22","ubuntu24"))
    args=parser.parse_args()
    run(args.tag)
