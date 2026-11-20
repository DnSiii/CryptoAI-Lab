"""Independent C27 queue/clock audit; training only, no candidate selection."""
import argparse
import json
import math
from pathlib import Path

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
WARMUP=720  # overwritten by imported, frozen C26 warmup
from .v98_composed_c26 import WARMUP
from .v98_c27_two_clock_governor import execute_queued_units, queue_sell_fractions
from .v98_c27_authenticated_runner import ASSET_BUFFER, GROSS_BUFFER

def audit(path):
    summary=json.loads(path.read_text())
    assert summary["source"]=="AUTHENTICATED_CLEAN4" and summary["holdout_accessed"] is False
    report={}
    for scenario in ("1x","2x","4x"):
        ledger=path.with_name(path.stem+"_"+scenario+"_ledger.jsonl")
        queued={a:0. for a in ASSETS}
        checks=0
        strategic_count=0
        for line in ledger.open():
            e=json.loads(line)
            i=e["index"]
            before=e["weights_before_fill"]
            after=e["weights_after_fill"]
            prior_queue=queued
            post_queue=execute_queued_units(before,prior_queue)
            strategic=(i>=WARMUP+1 and (i-(WARMUP+1))%168==0)
            expected_type="strategic" if strategic else ("safety" if any(prior_queue.values()) else "hold")
            if e["order_type"]!=expected_type:
                raise ValueError(f"C27_CLOCK_VIOLATION_{scenario}_{i}")
            if not strategic:
                for a in ASSETS:
                    if not math.isclose(after[a],post_queue[a],rel_tol=1e-9,abs_tol=1e-9):
                        raise ValueError(f"C27_OFF_CALENDAR_BUY_OR_QUEUE_MISMATCH_{scenario}_{i}")
            else:
                strategic_count+=1
            if any(after[a]>.40+1e-9 or after[a]<-1e-9 for a in ASSETS) or sum(after.values())>.90+1e-9:
                raise ValueError(f"C27_POST_FILL_EXPOSURE_BREACH_{scenario}_{i}")
            queued=queue_sell_fractions(after)
            buffered={a:min(after[a],ASSET_BUFFER) for a in ASSETS}
            total=sum(buffered.values())
            if total>GROSS_BUFFER:
                buffered={a:v*GROSS_BUFFER/total for a,v in buffered.items()}
            queued={a:0. if after[a]<=1e-12 else max(queued[a],1-buffered[a]/after[a]) for a in ASSETS}
            for a in ASSETS:
                if not math.isclose(queued[a],e["queued_next_open_sell_fractions"][a],rel_tol=1e-9,abs_tol=1e-9):
                    raise ValueError(f"C27_QUEUE_RECONCILIATION_{scenario}_{i}")
            checks+=1
        if checks!=27047 or strategic_count==0:
            raise ValueError("C27_INCOMPLETE_CAUSAL_AUDIT")
        report[scenario]={"checked_hours":checks,"strategic_rebalances":strategic_count,"causal_queue_reconciled":True}
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--summary",type=Path,required=True)
    a=p.parse_args()
    if "v98_independent" not in a.summary.resolve().parts:
        raise ValueError("C27_NAMESPACE_REQUIRED")
    print(json.dumps(audit(a.summary),sort_keys=True))
