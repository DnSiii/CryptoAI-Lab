#!/usr/bin/env python3
"""WQ independent arithmetic oracle; no WQ strategy import."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
from wl_independent_ledger_replay import check_rows

def run(outdir):
    out=Path(outdir)
    receipt=json.loads((out/"wq_exposed_physical.json").read_text())
    if not receipt.get("pnl_computed",False):
        result={"decision":"WQ_PRE_ECONOMIC_REJECTION_NO_LEDGER_OR_PNL",
                "audit_not_applicable":True,"paper_live_authorized":False}
    else:
        with (out/"wq_base_full_hourly_ledger.csv").open(newline="") as f:
            rows=list(csv.DictReader(f))
        replay=check_rows(rows)
        tamper=False
        if len(rows)>900:
            try:check_rows(rows,mutate=True)
            except ValueError as exc:
                tamper=str(exc).startswith("WL_ORACLE_LEDGER_MISMATCH_AT_")
            if not tamper:raise ValueError("WQ_TAMPER_NOT_DETECTED")
        base=next(x for x in receipt["cells"] if x["book"]=="WQ_full"
                  and x["tier"]=="base" and x["order"]=="carried_before_fill")
        if base["passed"]:
            if not replay["complete_history"]:raise ValueError("WQ_LEDGER_INCOMPLETE")
            for a,b in ((base["final_equity"],replay["terminal_cash"]),
                        (base["signed_funding"],replay["independent_signed_funding"]),
                        (base["fees_spread_impact"],replay["independent_fees"])):
                if not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-6):
                    raise ValueError("WQ_INDEPENDENT_REPLAY_MISMATCH")
        elif replay["complete_history"]:
            raise ValueError("WQ_FAILED_PHYSICAL_BUT_FULL_LEDGER")
        result={"decision":"PASS_WQ_ARITHMETIC_ONLY_NOT_ECONOMIC_VALIDATION" if base["passed"]
                else "PARTIAL_WQ_LEDGER_RECONCILED_NOT_SURVIVAL_APPROVAL",
                **replay,"tamper_detected":tamper,"base_full_physical_passed":base["passed"],
                "2026_accessed":False,"holdout_accessed":False,
                "exact_marks_authenticated":False,"account_costs_authenticated":False,
                "paper_live_authorized":False}
    (out/"wq_independent_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("WQ_AUDIT",json.dumps(result,sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out-dir",required=True)
    run(p.parse_args().out_dir)
