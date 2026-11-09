#!/usr/bin/env python3
"""A3 retrospective leave-one-sleeve-out attribution. NOT independent validation.

Predefined counterfactual: remove each of the four economic sleeves in turn,
reproject the unchanged A3 75% gross / 40% single-asset limits, and replay with
the SAME authenticated Clean-4 bars, native funding, and 1x/2x/4x costs.
No parameter search, sign flip, or promotion; 2023-2025 already observed.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS
from research.v98_independent.v98_phase243_training_reader import load, START_MS, EXPECTED_HOURS
from research.v98_independent.v98_sevenslot_weight_to_targets import FIELDS, SLEEVES
from research.v98_independent.v98_compound_scenario_replay import replay

def run(slots, prices, manifest, funding, output, baseline_summary):
    paths = (slots, prices, manifest, funding, output, baseline_summary)
    if any("v98_independent" not in Path(p).absolute().parts for p in paths):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    data = load(prices, manifest, funding)
    with open(slots, newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError("INVALID_SLOT_SCHEMA")
        grid = {}
        for row in reader:
            a, t = row["asset"], int(row["hour_open_ms"])
            if a not in ASSETS or t < START_MS or t >= START_MS + EXPECTED_HOURS*HOUR_MS or t % HOUR_MS:
                raise ValueError("INVALID_ASSET_TIME")
            if (t,a) in grid:
                raise ValueError("DUPLICATE_SLOT")
            v = {k: float(row[k]) for k in FIELDS[2:]}
            if not all(math.isfinite(x) for x in v.values()):
                raise ValueError("NONFINITE_SLOT")
            grid[t,a] = v
    if len(grid) != EXPECTED_HOURS * len(ASSETS):
        raise ValueError("INCOMPLETE_SLOT_GRID")
    baseline = json.loads(Path(baseline_summary).read_text())
    if baseline.get('status') != 'ECONOMIC_REPLAY_ONLY_NOT_VALIDATED_ENGINE' or baseline.get('holdout_accessed') is not False:
        raise ValueError('INVALID_BASELINE_STATUS')
    scenarios = baseline.get('scenarios', {})
    if set(scenarios) != {'cost_1x', 'cost_2x', 'cost_4x'}:
        raise ValueError('INVALID_BASELINE_SCENARIOS')
    result = {"status":"RETROSPECTIVE_ABLATION_NOT_INDEPENDENT_VALIDATION",
              "holdout_accessed":False, "cost_multipliers":[1,2,4],
              "baseline_final_equity_usd":{k:scenarios[k]["final_equity_usd"] for k in scenarios},
              "counterfactuals":{}}
    for removed in SLEEVES:
        decisions = []
        previous = {a:0. for a in ASSETS}
        for i in range(EXPECTED_HOURS):
            t = START_MS + i*HOUR_MS
            decisions.append({"hour_open_ms":t,"decision_time_ms":t-HOUR_MS,
                              "weights":previous.copy()})
            raw = {}
            for a in ASSETS:
                v = grid[t,a]
                if any(not 0 <= v[k] <= 1 for k in ("regime_router","risk_governor","dynamic_allocator")):
                    raise ValueError("INVALID_CONTROL")
                raw[a] = sum(v[s] for s in SLEEVES if s != removed)*v["regime_router"]
                if raw[a] < -1e-12:
                    raise ValueError("NEGATIVE_A3_SLEEVE")
            gross = sum(abs(x) for x in raw.values())
            peak = max(abs(x) for x in raw.values())
            scale = min(1., .75/gross if gross else 1., .4/peak if peak else 1.)
            previous = {a:raw[a]*scale for a in ASSETS}
            if sum(abs(x) for x in previous.values()) > .75+1e-10 or max(abs(x) for x in previous.values()) > .4+1e-10:
                raise ValueError("ABLATED_GOVERNOR_BREACH")
        ledgers = replay(decisions, data["bars"], data["funding"],
                         first_hour_ms=START_MS, initial_equity_usd=10000.,
                         fee_bps=4., slippage_bps=2.,
                         multipliers=(1.,2.,4.),gross_cap=1.,leverage_cap=2.)
        result["counterfactuals"][removed] = {
            scenario:{"hours":len(rows),"final_equity_usd":rows[-1]["ending_equity_usd"],
                      "marginal_equity_usd":scenarios[scenario]["final_equity_usd"]-rows[-1]["ending_equity_usd"],
                      "positive_marginal_contribution":scenarios[scenario]["final_equity_usd"]>rows[-1]["ending_equity_usd"]}
            for scenario,rows in ledgers.items()}
        if any(len(rows) != EXPECTED_HOURS for rows in ledgers.values()):
            raise ValueError("INCOMPLETE_ABLATION")
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("slots","prices","manifest","funding","output","baseline-summary"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(run(a.slots,a.prices,a.manifest,a.funding,a.output,a.baseline_summary),sort_keys=True))
