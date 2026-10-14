"""Read-only formal feasibility audit of immutable R106 legacy publication contract.

Shows whether any candidate could pass the CURRENT immutable-prefix guard,
holding the already-published ledger fixed. Does not fix, mutate or publish.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.v99_phase195bj_paper_publication_guard import (
    audit, strict_json, NAMES, MAX_OPERATIONS, utc
)

TRAIN_END=datetime(2024,1,18,tzinfo=timezone.utc)

def prove(raw: bytes):
    old=strict_json(raw)
    same=audit(old,old)  # The most favorable candidate, no change whatsoever.
    boundary=utc(old["paper_start_after_timestamp"])
    report={}
    for name in NAMES:
        var=old["variants"][name]
        original_ops=len(var["operations"])
        reference=old["backtest_reference"][name]["curve"]
        train_leak=sum(utc(p["timestamp"]) >= TRAIN_END for p in reference)
        paper_leak=sum(utc(p["timestamp"]) >= boundary for p in reference)
        intrinsic=[]
        if original_ops>=MAX_OPERATIONS:
            intrinsic.append("OLD_OPERATION_LEDGER_ALREADY_AT_CAP")
        if paper_leak:
            intrinsic.append("OLD_BACKTEST_REFERENCE_INCLUDES_PAPER_EPOCH")
        report[name]={
            "published_operations_count":original_ops,
            "old_ops_cap_guarantees_guard_failure":original_ops>=MAX_OPERATIONS,
            "historical_reference_points_after_train":train_leak,
            "historical_reference_points_after_paper":paper_leak,
            "backtest_paper_leak_guarantees_guard_failure":bool(paper_leak),
            "candidate_independent_rejection_reasons":intrinsic,
            "unchanged_candidate_guard_flags":same["variants"][name],
        }
    unavoidable=any(x["candidate_independent_rejection_reasons"] for x in report.values())
    if unavoidable and same["publication_authorized"]:
        raise AssertionError("guard contradiction")
    return {
        "phase":"V99_R106_LEGACY_PAPER_IMMUTABILITY_FEASIBILITY",
        "old_paper_raw_sha256":hashlib.sha256(raw).hexdigest(),
        "old_published_latest_utc":old["latest_data_timestamp"],
        "old_paper_boundary_utc":old["paper_start_after_timestamp"],
        "status":"NEW_VERSIONED_EPOCH_REQUIRED" if unavoidable else "OLD_PREFIX_NOT_STRUCTURALLY_IMPOSSIBLE",
        "current_epoch_guard_can_pass_any_candidate":False if unavoidable else None,
        "why":("Guard checks the immutable old capped operation lists and the"
               " old backtest reference crossing the paper boundary. Both are"
               " candidate-independent; none can be repaired by a new candidate.")
               if unavoidable else "No candidate-independent blocker found.",
        "variants":report,
        "old_epoch_can_be_mutated":False,
        "new_epoch_source_receipts_authenticated":False,
        "publication_authorized":False,
        "holdout_accessed":False,
        "economic_trials":0,
        "next_gate":"New epoch with separately verified as-of acquisition, uncapped journal and independent accounting.",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ledger",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    proof=prove(args.ledger.read_bytes())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(proof,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":proof["status"],
                      "old_paper_sha256":proof["old_paper_raw_sha256"],
                      "current_epoch_guard_can_pass_any_candidate":proof["current_epoch_guard_can_pass_any_candidate"]}))

if __name__=="__main__":
    main()
