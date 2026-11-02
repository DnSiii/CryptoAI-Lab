#!/usr/bin/env python3
"""V98 VZ independent replay of physical ledger using separate frozen V98 cash oracle.
Imports no VZ physical simulator. Rejects cash tampering. Exposed training only.
"""
from __future__ import annotations
import argparse,csv,json,tempfile
from pathlib import Path
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_oracle import audit

def run(d,outdir):
    out=Path(outdir)
    original=json.loads((out/"vz_exposed_physical.json").read_text())
    if original.get("architecture")!="VZ" or len(original.get("cells",[]))!=30:
        raise ValueError("VZ_ORACLE_RECEIPT_SHAPE")
    if original.get("2026_accessed") or original.get("holdout_accessed") or original.get("paper_live_authorized"):
        raise ValueError("VZ_ORACLE_FORBIDDEN_ACCESS")
    adapted=dict(original)
    adapted["architecture"]="VY"
    adapted["cells"]=[dict(c,book="VY_full" if c["book"]=="VZ_full" else c["book"])
                      for c in original["cells"]]
    source=out/"vz_base_full_hourly_ledger.csv"
    with tempfile.TemporaryDirectory() as td:
        receipt=Path(td)/"receipt.json"
        receipt.write_text(json.dumps(adapted))
        result=audit(d,source,receipt)
        with source.open(newline="") as f:
            rows=list(csv.DictReader(f))
        rows[744]["cash_after"]=str(float(rows[744]["cash_after"])+1.)
        corrupt=Path(td)/"corrupt.csv"
        with corrupt.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=rows[0].keys())
            w.writeheader();w.writerows(rows)
        try:audit(d,corrupt,receipt)
        except ValueError as exc:
            if "VY_INDEPENDENT_MISMATCH" not in str(exc):raise
            result["tampered_cash_detected"]=True
        else:raise ValueError("VZ_ORACLE_TAMPER_NOT_DETECTED")
    result["decision"]="PASS_INDEPENDENT_VZ_EXPOSED_ACCOUNTING_NOT_VALIDATION"
    result["architecture"]="VZ"
    result["reused_generic_V98_oracle_not_VY_signals"]=True
    (out/"vz_independent_oracle.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("VZ_INDEPENDENT",json.dumps(result,sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
