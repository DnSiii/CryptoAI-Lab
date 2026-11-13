"""Independent C3 training ledger evidence. No holdout, benchmark or promotion."""
import argparse
import json
import math
from pathlib import Path
from .v98_b0_chronological_evidence import audit as chronological_audit
from .v98_b0_regime_attribution import attribute as annual_attribution
from .v98_b0_independent_arithmetic_audit import reconcile

def audit(directory):
    root=Path(directory)
    summary=json.loads((root/"c3_composed_summary.json").read_text())
    if (summary.get("status")!="C3_PREREGISTERED_TRAINING_ONLY_NO_PROMOTION"
        or summary.get("holdout_accessed") is not False
        or summary.get("source")!="AUTHENTICATED_CLEAN4"
        or set(summary.get("results",{}))!={"1x","2x","4x"}):
        raise ValueError("C3_INVALID_TRAINING_BOUNDARY")
    if not all(isinstance(summary.get(k),str) and len(summary[k])==64
               for k in ("price_manifest_sha256","funding_manifest_sha256")):
        raise ValueError("C3_MISSING_SOURCE_HASH")
    results={}
    for scale in ("1x","2x","4x"):
        row=summary["results"][scale]
        if row["hours"]!=27048:
            raise ValueError("C3_INCOMPLETE_HISTORY")
        with (root/f"c3_composed_summary_{scale}_ledger.jsonl").open() as stream:
            ledger=[json.loads(line) for line in stream]
        if len(ledger)!=27047:
            raise ValueError("C3_INCOMPLETE_LEDGER")
        arithmetic=reconcile(ledger,row)
        if arithmetic["max_relative_residual"]>1e-9:
            raise ValueError("C3_ACCOUNTING_RESIDUAL")
        chronological=chronological_audit(ledger,row["final_equity"])
        attribution=annual_attribution(ledger,row["final_equity"])
        results[scale]={"arithmetic":arithmetic,"chronology":chronological,
                        "attribution":attribution}
    return {"status":"C3_TRAINING_AUDITED_NO_PROMOTION",
            "holdout_accessed":False,
            "price_manifest_sha256":summary["price_manifest_sha256"],
            "funding_manifest_sha256":summary["funding_manifest_sha256"],
            "results":results}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--directory",type=Path,required=True)
    args=parser.parse_args()
    if "v98_independent" not in args.directory.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=audit(args.directory)
    (args.directory/"c3_composed_evidence.json").write_text(
        json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:{"max_residual":v["arithmetic"]["max_relative_residual"],
                          "annual_returns":v["chronology"]["utc_annual_returns_including_warmup"]}
                      for k,v in result["results"].items()},sort_keys=True))
if __name__=="__main__":
    main()
