#!/usr/bin/env python3
"""WO separate arithmetic/tamper oracle; no WO signal or allocator import."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
from wl_independent_ledger_replay import check_rows

def run(outdir):
    out=Path(outdir)
    receipt=json.loads((out/"wo_exposed_physical.json").read_text())
    with (out/"wo_base_full_hourly_ledger.csv").open(newline="") as f:
        rows=list(csv.DictReader(f))
    audit=check_rows(rows)
    tamper=False
    if len(rows)>900:
        try:
            check_rows(rows,mutate=True)
        except ValueError as exc:
            tamper=str(exc).startswith("WL_ORACLE_LEDGER_MISMATCH_AT_")
        if not tamper:
            raise ValueError("WO_TAMPER_NOT_DETECTED")
    base=next(x for x in receipt["cells"] if x["book"]=="WO_full"
              and x["tier"]=="base" and x["order"]=="carried_before_fill")
    if base["passed"]:
        if not audit["complete_history"]:
            raise ValueError("WO_BASE_LEDGER_INCOMPLETE")
        for x,y in ((base["final_equity"],audit["terminal_cash"]),
                    (base["signed_funding"],audit["independent_signed_funding"]),
                    (base["fees_spread_impact"],audit["independent_fees"])):
            if not math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-6):
                raise ValueError("WO_INDEPENDENT_MISMATCH")
    elif audit["complete_history"]:
        raise ValueError("WO_REJECTED_LEDGER_WRONGLY_FULL")
    result={"decision":"PASS_WO_FULL_ARITHMETIC_ONLY_NOT_VALIDATION" if base["passed"]
            else "PARTIAL_WO_LEDGER_RECONCILED_NOT_SURVIVAL_APPROVAL",
            **audit,"tamper_detected":tamper,
            "base_full_physical_passed":base["passed"],
            "2026_accessed":False,"holdout_accessed":False,
            "exact_marks_authenticated":False,"account_costs_authenticated":False,
            "paper_live_authorized":False}
    (out/"wo_independent_audit.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("WO_AUDIT",json.dumps(result,sort_keys=True),flush=True)
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out-dir",required=True)
    run(p.parse_args().out_dir)
