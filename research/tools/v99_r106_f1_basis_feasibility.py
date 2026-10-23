"""One-shot F1 basis-convergence structural feasibility; NOT PNL or a trading strategy.

Prerecorded in research/V99_R106_F1_BASIS_CONVERGENCE_STRUCTURAL_PREREG_20261023.md
at commit d21215df971aae1afedf6915a7ecc46e3af623ee.
Original OKX TRAIN only; never touches sealed validation or holdout.
"""
from __future__ import annotations
import json, math, statistics, sys
from datetime import datetime, timezone
from pathlib import Path
from research.verification.independent_d1_native_train_receipts import verify
from research.tools.v99_r106_d1_real_train_source_join import START, END, HOUR, HOURS, FOLD_EDGES, strict_json

ASSETS=("BTC","ETH")
COST_HURDLES={"severe":0.0048,"supersevere":0.0096}
PREREG="d21215df971aae1afedf6915a7ecc46e3af623ee"

def fold_for(ts):
    for k,(a,b) in enumerate(zip(FOLD_EDGES,FOLD_EDGES[1:]),1):
        if a<=ts<b:return str(k)
    raise ValueError("OUTSIDE_FROZEN_TRAIN_FOLDS")

def analyze(price_root, output_dir):
    price_root=Path(price_root)
    proof=verify(price_root)
    if proof["status"]!="INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("ORIGINAL_OKX_RECEIPTS_NOT_VERIFIED")
    prices={}
    grid=list(range(START,END,HOUR))
    for asset in ASSETS:
        for suffix in ("-USDT","-USDT-SWAP"):
            inst=asset+suffix
            raw=strict_json(price_root/inst/"train_opens.json")
            if len(raw)!=HOURS or [r["ts"] for r in raw]!=grid:
                raise ValueError("F1_BAD_ORIGINAL_TRAIN_GRID_"+inst)
            prices[inst]=[float(r["open"]) for r in raw]
            if not all(math.isfinite(x) and x>0 for x in prices[inst]):
                raise ValueError("F1_NONPOSITIVE_PRICE_"+inst)
    by_fold={str(k):{asset:{"eligible_days":{s:0 for s in COST_HURDLES},
                                 "observed_midnights":0,"max_basis":None,"median_basis":None}
                          for asset in ASSETS}
             for k in range(1,6)}
    fold_premiums={str(k):{asset:[] for asset in ASSETS} for k in range(1,6)}
    qualifying_days={str(k):{s:set() for s in COST_HURDLES} for k in range(1,6)}
    total_decisions=0
    for i in range(1,HOURS):
        t=grid[i]
        if t%(24*HOUR)!=0:continue
        f=fold_for(t)
        total_decisions+=1
        for asset in ASSETS:
            premium=prices[asset+"-USDT-SWAP"][i-1]/prices[asset+"-USDT"][i-1]-1
            fold_premiums[f][asset].append(premium)
            entry=by_fold[f][asset]
            entry["observed_midnights"]+=1
            for scenario,hurdle in COST_HURDLES.items():
                if premium>hurdle:
                    entry["eligible_days"][scenario]+=1
                    qualifying_days[f][scenario].add(t)
    for fold in by_fold:
        for asset in ASSETS:
            vals=fold_premiums[fold][asset]
            if vals:
                by_fold[fold][asset]["max_basis"]=max(vals)
                by_fold[fold][asset]["median_basis"]=statistics.median(vals)
    distinct={f:{s:len(days) for s,days in scenarios.items()}
              for f,scenarios in qualifying_days.items()}
    qualifying_folds={s:sum(distinct[f][s]>=5 for f in distinct) for s in COST_HURDLES}
    go=qualifying_folds["severe"]>=4 and qualifying_folds["supersevere"]>=3
    result={"schema":"F1_ORIGINAL_OKX_BASIS_STRUCTURAL_SCREEN_V1",
            "preregistration_commit":PREREG,
            "status":"STRUCTURAL_SCREEN_PASS_NOT_ECONOMIC_TRAIN" if go else "F1_STRUCTURAL_REJECT_NO_RETUNE",
            "full_train_original_okx_receipts_verified":True,
            "train_start_ms":START,"train_end_exclusive_ms":END,"train_hours":HOURS,
            "utc_midnight_decisions":total_decisions,"four_trade_side_cost_hurdles":COST_HURDLES,
            "fold_asset_diagnostics":by_fold,"unique_qualifying_days_by_fold":distinct,
            "folds_with_at_least_five_days":qualifying_folds,
            "structural_go_for_separate_complete_engine":go,
            "basis_convergence_only_before_funding_margin_liquidation_and_execution":True,
            "historical_economic_train_run":False,"roi_computed":False,
            "native_fee_tier_authenticated":False,"actual_fills_authenticated":False,
            "funding_cash_authenticated":False,"validation_opened":False,"holdout_opened":False,
            "paper_results_modified":False,"orders_enabled":False,"promotion_authorized":False}
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"f1_basis_screen.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"status":result["status"],"decision_days":total_decisions,
                      "qualifying_days":distinct,"qualifying_folds":qualifying_folds,
                      "no_promotion":True},sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: python -m research.tools.v99_r106_f1_basis_feasibility ORIGINAL_TRAIN OUT")
    analyze(*sys.argv[1:])
