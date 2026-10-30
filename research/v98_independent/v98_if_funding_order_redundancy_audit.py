#!/usr/bin/env python3
"""V98 Independent artifact-only funding-order redundancy audit.
Never claims duplicate runs are independent economic evidence.
Only certified for a *specific* frozen experiment with all off-event fills.
No source, strategy, risk-governor, holdout or PnL imports.
"""
from __future__ import annotations
import argparse,glob,json,math
from pathlib import Path

PATHS=("IF_core_only","IF_full","IF_minus_opportunity","IF_minus_RV","IF_minus_stress")
FEES=("base","severe","supersevere")
ORDERS=("carried_before_fill","new_after_fill")
CLOCK=336
FIRST_SIGNAL=744
FUNDING_PERIOD=8
HOURS=18288
FIELDS=("final_nav","funding","fees","slippage","turnover","two_year_cagr",
        "max_drawdown","net_log_growth","hourly_net_profit_factor",
        "hourly_net_payoff","hourly_net_win_rate","hourly_cvar_1pct",
        "max_single_asset_gross_concentration","physical_fill_hours",
        "forced_risk_ratchets","target_updates")

def audit(root):
    files=sorted(glob.glob(str(Path(root)/"**"/"if30_IF_*.json"),recursive=True))
    by_path={}
    errors=[]
    for filename in files:
        try: data=json.loads(Path(filename).read_text())
        except Exception as exc:
            errors.append(("INVALID_RECEIPT",filename,str(exc)));continue
        path=data.get("path")
        if path not in PATHS or path in by_path:
            errors.append(("DUPLICATE_OR_UNKNOWN_PATH",filename,path));continue
        by_path[path]=data
    if set(by_path)!=set(PATHS):
        errors.append(("PATH_SET",sorted(by_path)))
    epochs=list(range(FIRST_SIGNAL,HOURS,CLOCK))
    off_event=bool(CLOCK%FUNDING_PERIOD==0 and
                   all((t+1)%FUNDING_PERIOD!=0 for t in epochs))
    if not off_event:errors.append(("EPOCH_OVERLAPS_FUNDING",))
    tested=0
    for path in PATHS:
        data=by_path.get(path)
        if not data:continue
        cells=data.get("cells",[])
        keyed={(x.get("fee"),x.get("order")):x for x in cells}
        if len(cells)!=6 or len(keyed)!=6:
            errors.append(("CELL_INVENTORY",path));continue
        for fee in FEES:
            a=keyed.get((fee,ORDERS[0]))
            b=keyed.get((fee,ORDERS[1]))
            if not a or not b or not a.get("passed") or not b.get("passed"):
                errors.append(("UNPAIRED_OR_FAILED",path,fee));continue
            if any(x.get("forced_risk_ratchets")!=0 or
                   x.get("physical_fill_hours")!=len(epochs) or
                   x.get("target_updates")!=len(epochs) for x in (a,b)):
                errors.append(("UNSCHEDULED_OR_FORCED_TRADE",path,fee))
                continue
            for field in FIELDS:
                if a.get(field)!=b.get(field):
                    errors.append(("ORDER_DIFFERENCE",path,fee,field))
            for year in ("2023","2024"):
                if a["annual"][year]!=b["annual"][year]:
                    errors.append(("ANNUAL_ORDER_DIFFERENCE",path,fee,year))
            tested+=1
    return {
        "architecture":"IF",
        "artifact_only":True,
        "holdout_2025_read":False,
        "pnl_computed":False,
        "source_signals_read":False,
        "funding_schedule_hours":FUNDING_PERIOD,
        "signal_interval_hours":CLOCK,
        "first_signal_hour":FIRST_SIGNAL,
        "execution_off_funding_event":off_event,
        "funding_order_pairs_tested":tested,
        "economic_scenarios_unique":len(PATHS)*len(FEES) if not errors else None,
        "physical_cells_one_os":len(PATHS)*len(FEES)*len(ORDERS),
        "economic_order_redundancy":not errors and tested==15,
        "errors":errors,
        "decision":"PASS_IF_15_UNIQUE_ECONOMIC_SCENARIOS_ORDER_REDUNDANT"
            if not errors and tested==15 else "BLOCK_IF_ORDER_EQUIVALENCE"
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    x=audit(a.root)
    Path(a.output).write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
    print("V98_IF_ORDER_AUDIT",x["decision"],"pairs",x["funding_order_pairs_tested"],
          "unique",x["economic_scenarios_unique"],"errors",x["errors"])
    raise SystemExit(0 if x["economic_order_redundancy"] else 2)
