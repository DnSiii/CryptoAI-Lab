#!/usr/bin/env python3
"""Build a V98-only evidence inventory for the Phase243 architecture reset.

Reads only V98 Independent namespaced research/report files in the current checkout.
It does not import or inspect V14/V15/V99 files and does not calculate strategy PnL.
"""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"v98_independent"/"phase243_evidence_inventory.json"
V98_DIRS=[ROOT/"research"/"v98_independent", ROOT/"reports"]

DECISION_PATTERNS=[
    ("reject", re.compile(r"REJECT(?:ED)?(?:_FAMILY)?(?:_NO_RESCUE|_FINAL_HOLDOUT)?", re.I)),
    ("fail_data", re.compile(r"FAIL_DATA_NO_ALPHA|FAIL_DATA", re.I)),
    ("pass_data", re.compile(r"PASS_DATA_ONLY", re.I)),
    ("pass_training", re.compile(r"PASS_TRAINING", re.I)),
    ("pass_validation", re.compile(r"PASS_VALIDATION", re.I)),
    ("promoted", re.compile(r"PROMOT(?:E|ED)|FROZEN CANDIDATE|CHAMPION", re.I)),
]

def phase_of(path: Path):
    m=re.search(r"phase[_-]?(\d{3})", path.name, re.I)
    return int(m.group(1)) if m else None

def classify(text: str):
    found=[]
    for name,rx in DECISION_PATTERNS:
        if rx.search(text):
            found.append(name)
    if "reject" in found:
        return "rejected"
    if "fail_data" in found:
        return "data_failed"
    if "pass_validation" in found:
        return "validation_pass"
    if "pass_training" in found:
        return "training_pass"
    if "promoted" in found:
        return "promoted_or_frozen"
    if "pass_data" in found:
        return "data_only_pass"
    return "unknown"

def main():
    rows={}
    for base in V98_DIRS:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if "v98" not in str(p).lower() and "phase" not in p.name.lower():
                continue
            ph=phase_of(p)
            if ph is None:
                continue
            try:
                text=p.read_text(errors="ignore")
            except Exception:
                continue
            rec=rows.setdefault(ph,{"phase":ph,"files":[],"signals":[]})
            rec["files"].append(str(p.relative_to(ROOT)))
            c=classify(text)
            if c!="unknown":
                rec["signals"].append(c)
    out=[]
    priority=["rejected","data_failed","validation_pass","training_pass","promoted_or_frozen","data_only_pass"]
    for ph in sorted(rows):
        r=rows[ph]
        sig=set(r["signals"])
        final="unknown"
        for x in priority:
            if x in sig:
                final=x
                break
        r["status"]=final
        r["files"]=sorted(set(r["files"]))
        r["signals"]=sorted(sig)
        r["architecture_eligibility"]=(
            "negative_evidence_only" if final in {"rejected","data_failed"}
            else "candidate_for_marginal_review" if final in {"validation_pass","training_pass","promoted_or_frozen"}
            else "data_capability_only" if final=="data_only_pass"
            else "unresolved"
        )
        out.append(r)
    payload={
        "engine":"V98 Independent",
        "phase":243,
        "mode":"EVIDENCE_INVENTORY_NO_PNL",
        "external_benchmarks_read":False,
        "v14_used":False,"v15_used":False,"v99_used":False,
        "phase_count":len(out),
        "phases":out,
    }
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"phase":243,"phase_count":len(out),"status_counts":{s:sum(r["status"]==s for r in out) for s in sorted(set(r["status"] for r in out))}},indent=2))

if __name__=="__main__":
    main()
