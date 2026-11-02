#!/usr/bin/env python3
"""WM separate arithmetic oracle; imported WL oracle never imports WM strategy."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
from wl_independent_ledger_replay import check_rows
def run(outdir):
    out=Path(outdir)
    receipt=json.loads((out/"wm_exposed_physical.json").read_text())
    if receipt["decision"]=="REJECT_WM_PRE_PNL_INCIDENCE":
        if receipt["cells"] or receipt["pnl_computed"]:
            raise ValueError("WM_PRE_PNL_GATE_COMPUTED_PNL")
        result={"decision":"PASS_WM_PRE_PNL_REJECTION_NO_ECONOMIC_CLAIM",
                "independent_ledger_replay":False,"pnl_computed":False}
    else:
        with (out/"wm_base_full_hourly_ledger.csv").open(newline="") as f:
            rows=list(csv.DictReader(f))
        audit=check_rows(rows)
        if not audit["complete_history"]:raise ValueError("WM_INCOMPLETE_LEDGER")
        tamper=False
        try:check_rows(rows,mutate=True)
        except ValueError as e:tamper=str(e).startswith("WL_ORACLE_LEDGER_MISMATCH_AT_")
        if not tamper:raise ValueError("WM_TAMPER_NOT_DETECTED")
        base=next(r for r in receipt["cells"] if r["book"]=="WM_full"
                  and r["tier"]=="base" and r["order"]=="carried_before_fill")
        if not base["passed"]:raise ValueError("WM_BASE_FULL_PHYSICAL_FAILED")
        for x,y in ((base["final_equity"],audit["terminal_cash"]),
                    (base["signed_funding"],audit["independent_signed_funding"]),
                    (base["fees_spread_impact"],audit["independent_fees"])):
            if not math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-6):
                raise ValueError("WM_INDEPENDENT_TOTAL_MISMATCH")
        result={"decision":"PASS_WM_ARITHMETIC_ONLY_NOT_VALIDATION",
                **audit,"tamper_detected":tamper,
                "independent_ledger_replay":True}
    result.update({"2026_accessed":False,"holdout_accessed":False,
                   "exact_marks_authenticated":False,
                   "account_costs_authenticated":False,
                   "paper_live_authorized":False})
    (out/"wm_independent_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("WM_AUDIT",json.dumps(result,sort_keys=True),flush=True)
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out-dir",required=True)
    run(p.parse_args().out_dir)
