#!/usr/bin/env python3
"""V98 VZ independent signal + physical cash/funding replay, adversarial tamper.
No VZ target/simulator imports. Exposed training only; not future validation.
"""
from __future__ import annotations
import argparse,csv,json,tempfile
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_oracle import audit

def independent_target(p,t):
    r24=p[t]-p[t-24]
    r6=p[t]-p[t-6]
    r72=p[t]-p[t-72]
    r168=p[t]-p[t-168]
    order24=sorted(range(4),key=lambda j:(r24[j],j))
    order6=sorted(range(4),key=lambda j:(r6[j],j))
    raw=np.zeros((4,4),float)
    factor=.5 if np.mean(r168)<0 else 1.
    for j in order24[:2]:raw[0,j]=.14*factor
    for j in order24[2:]:raw[0,j]=-.14*factor
    hist=np.arange(t-504,t+1,24)
    if np.std(r24)>np.median(np.std(p[hist]-p[hist-24],axis=1)):
        raw[1,order24[0]]=.08
        raw[1,order24[-1]]=-.08
    if np.std(r6)>np.median(np.std(p[hist]-p[hist-6],axis=1)):
        raw[2,order6[0]]=.07
        raw[2,order6[-1]]=-.07
    if np.mean(r72)<=-.08:
        raw[3,0]=.07
        raw[3,3]=-.07
    remain=.90-np.abs(raw[0]).sum()
    for slot in (1,2,3):
        gross=np.abs(raw[slot]).sum()
        if gross>remain and gross>0:raw[slot]*=remain/gross
        remain=max(0.,remain-np.abs(raw[slot]).sum())
    return raw.sum(axis=0)

def verify_targets(d,path):
    p=np.log(np.asarray(d["c"],float))
    count=0;checked=0;previous=np.zeros(4)
    with Path(path).open(newline="") as handle:
        reader=csv.DictReader(handle)
        for row in reader:
            t=int(row["hour"])
            if t>=27048:raise ValueError("VZ_SIGNAL_HOUR")
            w=np.asarray(json.loads(row["target_weight"]),float)
            if t==27047:
                expected=np.zeros(4)
            elif t>=744 and (t-1-743)%24==0:
                expected=independent_target(p,t-1)
                count+=1
            else:
                expected=np.zeros(4)
            if w.shape!=(4,) or not np.allclose(w,expected,rtol=1e-12,atol=1e-12):
                raise ValueError("VZ_INDEPENDENT_SIGNAL_MISMATCH_"+str(t))
            checked+=1
    if count!=1096 or checked!=27048:raise ValueError("VZ_SIGNAL_INCOMPLETE")
    return {"independent_signal_checks":checked,"decisions_checked":count}

def run(d,outdir):
    out=Path(outdir)
    original=json.loads((out/"vz_exposed_physical.json").read_text())
    if original.get("architecture")!="VZ" or len(original.get("cells",[]))!=30:
        raise ValueError("VZ_ORACLE_RECEIPT_SHAPE")
    if original.get("2026_accessed") or original.get("holdout_accessed") or original.get("paper_live_authorized"):
        raise ValueError("VZ_ORACLE_FORBIDDEN_ACCESS")
    source=out/"vz_base_full_hourly_ledger.csv"
    signals=verify_targets(d,source)
    adapted=dict(original)
    adapted["architecture"]="VY"
    adapted["cells"]=[dict(c,book="VY_full" if c["book"]=="VZ_full" else c["book"])
                      for c in original["cells"]]
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
        rows[744]["cash_after"]=str(float(rows[744]["cash_after"])-1.)
        rows[744]["target_weight"]=json.dumps([.2,-.2,0.,0.])
        corrupt_signal=Path(td)/"corrupt_signal.csv"
        with corrupt_signal.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=rows[0].keys())
            w.writeheader();w.writerows(rows)
        try:verify_targets(d,corrupt_signal)
        except ValueError as exc:
            if "VZ_INDEPENDENT_SIGNAL_MISMATCH" not in str(exc):raise
            result["tampered_signal_detected"]=True
        else:raise ValueError("VZ_ORACLE_SIGNAL_TAMPER_NOT_DETECTED")
    result.update(signals)
    result["decision"]="PASS_INDEPENDENT_VZ_EXPOSED_SIGNAL_AND_ACCOUNTING_NOT_VALIDATION"
    result["architecture"]="VZ"
    result["reused_generic_V98_cash_oracle_not_VY_signals"]=True
    (out/"vz_independent_oracle.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("VZ_INDEPENDENT",json.dumps(result,sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
