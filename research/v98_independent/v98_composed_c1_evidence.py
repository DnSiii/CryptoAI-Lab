"""Independent C1 chronological and asset attribution from full native ledger.

Training-only diagnostics; no selection, benchmark, holdout or promotion.
"""
import argparse
import json
from pathlib import Path
from .v98_b0_chronological_evidence import audit as chronological_audit
from .v98_b0_regime_attribution import attribute as annual_attribution
from .v98_b0_independent_arithmetic_audit import reconcile

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",type=Path,required=True)
    args=p.parse_args()
    root=args.directory
    if "v98_independent" not in root.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    summary=json.loads((root/"c1_composed_summary.json").read_text())
    if summary.get("holdout_accessed") is not False or set(summary["results"]) != {"1x","2x","4x"}:
        raise ValueError("C1_INVALID_BOUNDARY")
    result={}
    for scale in ("1x","2x","4x"):
        with (root/f"c1_composed_summary_{scale}_ledger.jsonl").open() as stream:
            ledger=[json.loads(line) for line in stream]
        final=summary["results"][scale]["final_equity"]
        result[scale]={
            "arithmetic":reconcile(ledger,summary["results"][scale]),
            "chronology":chronological_audit(ledger,final),
            "attribution":annual_attribution(ledger,final)
        }
    target=root/"c1_composed_evidence.json"
    target.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({s:{
        "annual_returns":r["chronology"]["utc_annual_returns_including_warmup"],
        "negative_months":r["chronology"]["negative_months"],
        "months":r["chronology"]["months"]
    } for s,r in result.items()},sort_keys=True))
if __name__=="__main__":
    main()
