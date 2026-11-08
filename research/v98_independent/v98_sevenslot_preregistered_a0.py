#!/usr/bin/env python3
"""V98 preregistered seven-slot baseline A0. Research-only, NOT approved alpha.

Uses only the close and history available by the end of the named hour.
No fitting, external engines, holdout, 2026+ prices, or performance-dependent tuning.
Fixed hypotheses: 168h trend growth, 24h momentum opportunity,
cross-sectional 24h relative strength, 168h drawdown recovery.
Router/allocator/governor constrain concentration and realized volatility.
This is a *candidate to reject or validate*, not an optimized champion.
"""
import argparse
import csv
import math
from pathlib import Path
from research.v98_independent.v98_phase243_training_reader import load, START_MS
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS
from research.v98_independent.v98_sevenslot_weight_to_targets import FIELDS

def generate(prices, manifest, funding, output):
    if "v98_independent" not in Path(output).absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    data = load(prices, manifest, funding)
    closes = {a: [float(bar[3]) for bar in data["bars"][a]] for a in ASSETS}
    n = data["hours"]
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for i in range(n):
            returns24 = {a: closes[a][i]/closes[a][i-24]-1 if i>=24 else 0. for a in ASSETS}
            avg24 = sum(returns24.values())/len(ASSETS)
            proposals = {}
            for a in ASSETS:
                p = closes[a]
                if i < 168:
                    proposals[a] = (0., 0., 0., 0., 0.)
                    continue
                trend = p[i]/p[i-168]-1
                mom = returns24[a]
                drawdown = p[i]/max(p[i-167:i+1])-1
                hourly = [math.log(p[j]/p[j-1]) for j in range(i-23,i+1)]
                volatility = math.sqrt(sum(v*v for v in hourly)/24)
                growth = 0.12 if trend>0 else -0.06
                opportunity = 0.04 if mom>0.04 and trend>0 else 0.
                relative = 0.035 if mom>avg24+0.015 else (-0.035 if mom<avg24-0.015 else 0.)
                recovery = 0.03 if drawdown < -0.12 and mom>0 else 0.
                proposals[a] = (growth, opportunity, relative, recovery, volatility)
            gross_raw = sum(abs(sum(proposals[a][:4])) for a in ASSETS)
            scale = min(1., 0.65/gross_raw) if gross_raw else 1.
            for a in ASSETS:
                g,o,r,s,vol = proposals[a]
                router = 0.5 if vol>0.025 else 1.
                allocator = scale
                governor = 0.25
                # Risk governor is an exposure ceiling, not a post-hoc clip.
                exposure = abs((g+o+r+s)*router*allocator)
                if exposure > governor + 1e-12:
                    raise ValueError("GOVERNOR_BREACH")
                writer.writerow(dict(zip(FIELDS,(a,START_MS+i*HOUR_MS,
                    g,o,r,s,router,allocator,governor))))
    return {"rows":n*len(ASSETS),"hours":n,"status":"PREREGISTERED_A0_UNVALIDATED"}

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    for key in ("prices","manifest","funding","output"):
        p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    print(generate(a.prices,a.manifest,a.funding,a.output))
