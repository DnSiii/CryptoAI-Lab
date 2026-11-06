#!/usr/bin/env python3
"""V98-only causal target-to-ledger input bridge. Does not select or validate alpha.

Input targets: asset,hour_open_ms,target_notional_usd. Each target is a signal
computed only after that hour's close; it is executed at the NEXT hour's open.
Target amounts are USD, not weights. This bridge cannot convert weights to USD
without an independently specified causal equity/allocation policy.
"""
import csv
from pathlib import Path
from datetime import datetime
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS

FIELDS = ("asset","hour_open_ms","decision_time_ms","pre_trade_notional_usd",
          "target_notional_usd","close_price","fill_price")

def bridge(targets_path, prices_root, output_path):
    for p in (targets_path,prices_root,output_path):
        if "v98_independent" not in Path(p).absolute().parts:
            raise ValueError("V98_NAMESPACE_REQUIRED")
    with open(targets_path,newline="") as f:
        data=list(csv.DictReader(f))
    targets={}
    for r in data:
        key=(r["asset"],int(r["hour_open_ms"]))
        if key[0] not in ASSETS or key in targets:
            raise ValueError("INVALID_OR_DUPLICATE_TARGET")
        targets[key]=float(r["target_notional_usd"])
        import math
        if not math.isfinite(targets[key]):raise ValueError("NONFINITE_TARGET")
    prices={}
    for asset in ASSETS:
        with open(Path(prices_root)/f"{asset}_1h.csv",newline="") as f:
            for r in csv.DictReader(f):
                t=int(datetime.fromisoformat(r["open_time"].replace("Z","+00:00")).timestamp()*1000)
                if (asset,t) in prices:raise ValueError("DUPLICATE_PRICE")
                prices[asset,t]=(float(r["open"]),float(r["close"]))
    hours=sorted(set(t for _,t in prices))
    if not hours or any(b-a!=HOUR_MS for a,b in zip(hours,hours[1:])):
        raise ValueError("NONCONTIGUOUS_PRICES")
    if set(prices)!={(a,t) for a in ASSETS for t in hours}:
        raise ValueError("INCOMPLETE_PRICES")
    if set(targets)!={(a,t) for a in ASSETS for t in hours}:
        raise ValueError("INCOMPLETE_TARGET_GRID")
    if hours[-1]>=1767225600000:raise ValueError("TRAINING_BOUNDARY")
    rows=[]
    prev={a:0.0 for a in ASSETS}
    for i,t in enumerate(hours):
        for a in ASSETS:
            op,cl=prices[a,t]
            if not (0<op and 0<cl):raise ValueError("INVALID_PRICE")
            # No same-bar target is allowed to influence this hour's execution.
            target=targets[a,hours[i-1]] if i else 0.0
            rows.append(dict(zip(FIELDS,(a,t,t-HOUR_MS,prev[a],target,cl,op))))
            prev[a]=target*cl/op
    Path(output_path).parent.mkdir(parents=True,exist_ok=True)
    with open(output_path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    return len(rows)

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--targets",type=Path,required=True)
    p.add_argument("--prices-root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    print(bridge(a.targets,a.prices_root,a.output))
