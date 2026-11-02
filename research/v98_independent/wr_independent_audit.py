#!/usr/bin/env python3
"""WR independent hourly cash/funding arithmetic oracle; no WR strategy import."""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path
from wl_independent_ledger_replay import check_rows

def run(outdir):
    out = Path(outdir)
    receipt = json.loads((out/"wr_exposed_physical.json").read_text())
    if not receipt.get("pnl_computed", False):
        result = {"decision": "WR_PRE_ECONOMIC_REJECTION_NO_LEDGER_OR_PNL",
                  "audit_not_applicable": True, "paper_live_authorized": False}
    else:
        path = out/"wr_base_full_hourly_ledger.csv"
        if not path.exists():
            base = next(x for x in receipt["cells"]
                        if x["book"] == "WR_full" and x["tier"] == "base"
                        and x["order"] == "carried_before_fill")
            if base["passed"]:
                raise ValueError("WR_MISSING_COMPLETED_BASE_LEDGER")
            result = {"decision": "WR_PHYSICAL_FAILED_NO_FULL_BASE_LEDGER",
                      "base_failure": base, "audit_not_applicable": True,
                      "paper_live_authorized": False}
        else:
            with path.open(newline="") as f:
                rows = list(csv.DictReader(f))
            replay = check_rows(rows)
            tamper = False
            if len(rows) > 900:
                try:
                    check_rows(rows, mutate=True)
                except ValueError as exc:
                    tamper = str(exc).startswith("WL_ORACLE_LEDGER_MISMATCH_AT_")
                if not tamper:
                    raise ValueError("WR_TAMPER_NOT_DETECTED")
            base = next(x for x in receipt["cells"]
                        if x["book"] == "WR_full" and x["tier"] == "base"
                        and x["order"] == "carried_before_fill")
            if base["passed"]:
                if not replay["complete_history"]:
                    raise ValueError("WR_INCOMPLETE_BASE_LEDGER")
                for x, y in ((base["final_equity"], replay["terminal_cash"]),
                             (base["signed_funding"], replay["independent_signed_funding"]),
                             (base["fees_spread_impact"], replay["independent_fees"])):
                    if not math.isclose(x, y, rel_tol=1e-10, abs_tol=1e-6):
                        raise ValueError("WR_INDEPENDENT_REPLAY_MISMATCH")
            elif replay["complete_history"]:
                raise ValueError("WR_FAILED_PHYSICAL_BUT_COMPLETE_LEDGER")
            result = {
                "decision": "PASS_WR_ARITHMETIC_ONLY_NOT_ECONOMIC_VALIDATION"
                            if base["passed"] else "PARTIAL_WR_LEDGER_RECONCILED",
                **replay, "tamper_detected": tamper,
                "base_full_physical_passed": base["passed"],
                "2026_accessed": False, "holdout_accessed": False,
                "exact_marks_authenticated": False,
                "account_costs_authenticated": False,
                "paper_live_authorized": False
            }
    (out/"wr_independent_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True)+"\n")
    print("WR_AUDIT", json.dumps(result, sort_keys=True), flush=True)
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", required=True)
    run(p.parse_args().out_dir)
