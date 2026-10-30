#!/usr/bin/env python3
"""V98 Phase1017: frozen canonical O 90-cell authenticated training gate.

No economic ledger call until same-run official Clean-4 OHLC, mark, funding
and cross-CPU canonical O code/target hashes pass. No 2025+, holdout, benchmarks.
"""
from __future__ import annotations
import json
from pathlib import Path
from phase1016_o_canonical_freeze import (
    ROOT, FROZEN_CANONICAL_O, verify_canonical_source, frozen_canonical_o_paths,
)
from phase1009_o_90cell_training import (
    source_gate, isolated_source_arrays, complete_matrix_o, growth_gate_o,
)

OUT=ROOT/"phase1017_o_canonical_90cell_result.json"


def run():
    out={"phase":1017,"decision":"BLOCKED_BEFORE_PNL","historical_pnl_computed":False,
         "ledger_invocations":0,"promotion_eligible":False,
         "validation_2025_read":False,"holdout_accessed":False,
         "external_benchmarks_used":False,"frozen_source_modified":False,
         "transport":"8g_minus_one_decimal_quantum_no_exposure_increase"}
    try:
        verify_canonical_source()
        out["source_receipts"]=source_gate()
        paths,hashes,canonical_receipt=frozen_canonical_o_paths()
        if hashes!=FROZEN_CANONICAL_O:
            raise PermissionError("O_CANONICAL_TARGET_SHA_DRIFT")
        out["canonical_target_sha256"]=hashes
        out["canonical_source_only_diagnostics"]=canonical_receipt["diagnostics"]
        arrays,rate,mark,event,years=isolated_source_arrays()
        prices={k:arrays[k] for k in ("open","high","low","close")}
        matrix=complete_matrix_o({k:v.to_numpy(float) for k,v in paths.items()},
                                 prices,arrays["quote_volume"],rate,mark,event,years)
        out["historical_pnl_computed"]=True
        out["ledger_invocations"]=matrix["cells_attempted"]
        out["matrix"]=matrix
        out["growth_gate"]=growth_gate_o(matrix)
        out["decision"]="PASS_O_CANONICAL_TRAINING_ONLY_PENDING_SEPARATE_VALIDATION" if out["growth_gate"]["passed"] else "REJECT_O_CANONICAL_TRAINING_NO_RESCUE"
    except Exception as exc:
        out["decision"]="BLOCKED_AFTER_PNL_NO_PROMOTION" if out["historical_pnl_computed"] else "BLOCKED_BEFORE_PNL"
        out["reason"]=type(exc).__name__+": "+str(exc)[:350]
    OUT.write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"phase":1017,"decision":out["decision"],
                      "historical_pnl_computed":out["historical_pnl_computed"],
                      "ledger_invocations":out["ledger_invocations"],
                      "cells_survived":out.get("matrix",{}).get("cells_survived"),
                      "reason":out.get("reason")},sort_keys=True))
    return 0 if out["decision"].startswith("PASS_") else 2


if __name__=="__main__":
    raise SystemExit(run())
