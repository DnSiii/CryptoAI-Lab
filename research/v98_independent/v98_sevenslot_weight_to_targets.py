#!/usr/bin/env python3
"""V98 seven-slot causal weight aggregation, NOT an approved strategy or PnL claim.

Input: asset,hour_open_ms,growth_core,opportunity,relative_value,stress_recovery,
regime_router,dynamic_allocator,risk_governor.
All inputs are signed *weights* decided at the end of the named hour. The four
sleeves are additive; router and allocator are nonnegative multipliers, governor
is a nonnegative per-asset exposure ceiling. No implicit equity compounding.
This is a transport contract only; weights must come from separately frozen
V98-only causal models. No V14/V15/V99 input is permitted.
"""
import argparse
import csv
import math
from pathlib import Path
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS

SLEEVES=("growth_core","opportunity","relative_value","stress_recovery")
FIELDS=("asset","hour_open_ms",*SLEEVES,"regime_router","dynamic_allocator","risk_governor")
OUT=("asset","hour_open_ms","target_notional_usd")

def convert(source, destination, *, fixed_capital_usd, gross_cap=1.0):
    for p in (source,destination):
        if "v98_independent" not in Path(p).absolute().parts:
            raise ValueError("V98_NAMESPACE_REQUIRED")
    if not math.isfinite(fixed_capital_usd) or fixed_capital_usd<=0:
        raise ValueError("INVALID_FIXED_CAPITAL")
    if not math.isfinite(gross_cap) or not 0<gross_cap<=2:
        raise ValueError("INVALID_GROSS_CAP")
    with open(source,newline="") as f:
        reader=csv.DictReader(f)
        if set(reader.fieldnames or ()) != set(FIELDS):
            raise ValueError("SEVEN_SLOT_SCHEMA_REQUIRED")
        rows=list(reader)
    if not rows: raise ValueError("EMPTY_SEVEN_SLOT_GRID")
    grouped={}
    for r in rows:
        asset=r["asset"]
        t=int(r["hour_open_ms"])
        if asset not in ASSETS or t%HOUR_MS or t>=1767225600000 or t<1669852800000:
            raise ValueError("INVALID_ASSET_OR_TRAINING_HOUR")
        if (asset,t) in grouped: raise ValueError("DUPLICATE_ASSET_HOUR")
        values={k:float(r[k]) for k in FIELDS[2:]}
        if not all(math.isfinite(v) for v in values.values()):
            raise ValueError("NONFINITE_SLOT")
        if any(not 0<=values[k]<=1 for k in ("regime_router","dynamic_allocator","risk_governor")):
            raise ValueError("INVALID_ROUTER_ALLOCATOR_GOVERNOR")
        raw=sum(values[k] for k in SLEEVES)
        # Reject instead of silently clipping/renormalizing a proposed strategy.
        if abs(raw)>2+1e-12: raise ValueError("UNBOUNDED_SLEEVE_WEIGHT")
        weight=raw*values["regime_router"]*values["dynamic_allocator"]
        if abs(weight)>values["risk_governor"]+1e-12:
            raise ValueError("RISK_GOVERNOR_BREACH")
        grouped[asset,t]=weight
    hours=sorted({t for _,t in grouped})
    if any(b-a!=HOUR_MS for a,b in zip(hours,hours[1:])):
        raise ValueError("NONCONTIGUOUS_HOURS")
    if set(grouped)!={(a,t) for a in ASSETS for t in hours}:
        raise ValueError("INCOMPLETE_CLEAN4_GRID")
    output=[]
    for t in hours:
        if sum(abs(grouped[a,t]) for a in ASSETS)>gross_cap+1e-12:
            raise ValueError("GROSS_CAP_BREACH")
        for a in ASSETS:
            output.append({"asset":a,"hour_open_ms":t,
                           "target_notional_usd":format(grouped[a,t]*fixed_capital_usd,".12g")})
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=OUT)
        writer.writeheader();writer.writerows(output)
    return len(output)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--fixed-capital-usd",type=float,required=True)
    p.add_argument("--gross-cap",type=float,default=1.0)
    a=p.parse_args()
    print(convert(a.source,a.output,fixed_capital_usd=a.fixed_capital_usd,gross_cap=a.gross_cap))
