"""C11 seven-slot marginal-contribution diagnostics on authenticated Clean-4 training only.
These counterfactuals cannot rescue or promote the rejected C11 candidate.
No holdout, benchmark, 2026+ or alternative tuning is accessed.
"""
import argparse
import json
from pathlib import Path
from unittest.mock import patch
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import ASSETS, HOUR_MS
from .v98_composed_c11 import composed_c11_sleeves, breadth_router, c11_allocator
from .v98_b0_next_open_execution import replay_next_open
from . import v98_b0_next_open_execution as execution

def run(prices, manifest, funding):
    data = load(prices, manifest, funding)
    indexed = {a:{} for a in ASSETS}
    for a in ASSETS:
        for stamp, rate in data["funding"][a].items():
            offset = stamp-START_MS
            if offset % HOUR_MS or not 0 <= offset < data["hours"]*HOUR_MS:
                raise ValueError("INVALID_NATIVE_FUNDING_TIMESTAMP")
            indexed[a][offset//HOUR_MS] = rate
    results = {}
    # Exactly one predeclared counterfactual per slot. The 4th sleeve is
    # deliberately allowed to be inactive; report its actual activation.
    for slot in range(7):
        active = 0
        calls = 0
        original = composed_c11_sleeves()
        def sleeves(history):
            nonlocal active, calls
            raw = original(history)
            calls += 1
            if slot < 4:
                active += int(any(abs(raw[a][slot]) > 1e-14 for a in ASSETS))
                return {a:tuple(0. if j == slot else v for j,v in enumerate(raw[a]))
                        for a in ASSETS}
            return raw
        router = (lambda closes: 1.) if slot == 4 else breadth_router
        allocator = (lambda sleeves, routers, governor:
                     c11_allocator(sleeves, routers, 1.)) if slot == 6 else c11_allocator
        # Slot 5 disables the allocator's diversification cap by replacing
        # it with the identical composition interface and a full gross cap.
        if slot == 5:
            from .v98_b0_causal_overlay import compose_weights
            allocator = lambda sleeves,routers,governor: compose_weights(
                sleeves,routers,governor,gross_cap=1.,asset_cap=1.)
        with patch.object(execution,"regime_multiplier",router), patch.object(
                execution,"compose_weights",allocator):
            summary, ledger = replay_next_open(data["bars"],indexed,sleeves,cost_scale=4.)
        if summary["hours"] != data["hours"] or len(ledger) != data["hours"]-1:
            raise ValueError("INCOMPLETE_COUNTERFACTUAL")
        results[["without_growth","without_opportunity","without_relative_value",
                 "without_recovery","without_router","without_allocator_caps",
                 "without_governor"][slot]] = {
            "final_equity_4x":summary["final_equity"],
            "max_drawdown_4x":summary["max_drawdown"],
            "total_turnover_4x":summary["total_turnover"],
            "sleeve_active_calls":active if slot < 4 else None,
            "calls":calls}
    return {"status":"C11_REJECTED_DIAGNOSTICS_NO_PROMOTION",
            "source":"AUTHENTICATED_CLEAN4","holdout_accessed":False,
            "price_manifest_sha256":data["price_manifest_sha256"],
            "funding_manifest_sha256":data["funding_manifest_sha256"],
            "baseline_c11_4x_equity":11369.641556719436,
            "results":results}

def main():
    p=argparse.ArgumentParser()
    for name in ("prices","manifest","funding","output"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    if "v98_independent" not in a.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=run(a.prices,a.manifest,a.funding)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
