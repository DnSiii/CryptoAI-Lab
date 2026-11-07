#!/usr/bin/env python3
"""V98-only composed seven-slot economic replay; no alpha selection or holdout."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from research.v98_independent.v98_sevenslot_weight_to_targets import convert
from research.v98_independent.v98_causal_target_execution_bridge import bridge
from research.v98_independent.phase243_strict_historical_accounting_run import run

def replay(slots, prices, price_manifest, funding, output, capital, fee_bps, slippage_bps,
           gross_cap=1.0, max_gross_leverage=2.0, multipliers=(1,2,4)):
    if any("v98_independent" not in Path(p).absolute().parts
           for p in (slots,prices,price_manifest,funding,output)):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    if len(multipliers)!=3 or any(not math.isfinite(x) or x<=0 for x in multipliers) or tuple(sorted(multipliers))!=tuple(multipliers):
        raise ValueError("INVALID_COST_SCENARIOS")
    if any(not math.isfinite(x) for x in (capital,fee_bps,slippage_bps,gross_cap,max_gross_leverage)) or capital<=0 or fee_bps<0 or slippage_bps<0 or not 0<gross_cap<=max_gross_leverage:
        raise ValueError("INVALID_ECONOMIC_INPUTS")
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    targets=output/"seven_slot_targets.csv"
    positions=output/"causal_positions.csv"
    count=convert(slots,targets,fixed_capital_usd=capital,gross_cap=gross_cap)
    if bridge(targets,prices,positions)!=count:
        raise ValueError("POSITION_COUNT_MISMATCH")
    digest=hashlib.sha256(positions.read_bytes()).hexdigest()
    receipts={}
    for label,multiplier in zip(("baseline","severe","supersevere"),multipliers):
        receipt=run(positions,Path(funding),output/(label+"_ledger.csv"),
                    initial_equity_usd=capital,taker_fee_bps=fee_bps,
                    slippage_bps=slippage_bps,cost_multiplier=multiplier,
                    max_gross_leverage=max_gross_leverage,price_root=Path(prices),
                    price_manifest_path=Path(price_manifest))
        if receipt["positions_sha256"]!=digest:
            raise ValueError("SCENARIO_POSITION_DRIFT")
        receipts[label]=receipt
    summary={"status":"ECONOMIC_REPLAY_ONLY_NOT_VALIDATED_ENGINE",
             "holdout_accessed":False,"positions_sha256":digest,
             "slots_sha256":hashlib.sha256(Path(slots).read_bytes()).hexdigest(),
             "multipliers":list(multipliers),"receipts":receipts}
    (output/"scenario_summary.json").write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
    return summary

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("slots","prices","price-manifest","funding","output"):
        p.add_argument("--"+name,type=Path,required=True)
    for name in ("capital","fee-bps","slippage-bps"):
        p.add_argument("--"+name,type=float,required=True)
    p.add_argument("--gross-cap",type=float,default=1.0)
    p.add_argument("--max-gross-leverage",type=float,default=2.0)
    a=p.parse_args()
    print(json.dumps(replay(a.slots,a.prices,a.price_manifest,a.funding,a.output,
        a.capital,a.fee_bps,a.slippage_bps,a.gross_cap,a.max_gross_leverage),sort_keys=True))
