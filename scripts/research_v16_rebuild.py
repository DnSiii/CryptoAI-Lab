"""Frozen-menu experiment batch. Historical diagnostics, never auto-promotion."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_v16_recent import PROJECT, audit_market, hashes, metrics, subset, windows
from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.data import load_data
from cryptoai_v13.v16_rebuild import growth_targets, online_mix, research_menu


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--market-root",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--end",default="2026-08-31")
    args=p.parse_args()
    if args.output_dir.resolve().is_relative_to(args.market_root.resolve()):
        raise ValueError("cannot write to read-only market inputs")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    if (args.output_dir/"protocol.json").exists():
        raise ValueError("use a new explicit batch path; do not overwrite evidence")
    end=pd.Timestamp(args.end,tz="UTC")+pd.Timedelta(hours=23)
    menu=research_menu()
    protocol={
        "created_at":pd.Timestamp.now(tz="UTC").isoformat(),"mode":"RESEARCH_ONLY",
        "end":end.isoformat(),"decision_menu":{k:s.to_dict() for k,s in menu.items()},
        "train_start":"2025-04-01T00:00:00Z","train_end":"2025-08-31T23:00:00Z",
        "diagnostic_start":"2025-09-01T00:00:00Z",
        "training_selection":"top 3 by log net return / max(absolute drawdown, 0.05); no evaluation input",
        "overlapping_windows_are_not_independent_tests":True,
        "historical_data_was_used_in_prior_research":True,
        "pristine_holdout_available":False,
        "approval":"NEVER_AUTO_PROMOTE; research gates do not establish commercial readiness",
        "minimum_research_gates":{
            "return_1y":0.50,"return_6m":0.15,"return_3m":0.05,
            "return_30d":0.0,"return_7d":0.0,"max_drawdown_1y":-0.20,
            "annual_return_over_drawdown":2.5,"positive_without_best_3_days":True,
        },
        "normal_cost_per_side":0.0007,"severe_cost_per_side":0.0012,
        "normal_decision_delay_hours":1,"stress_decision_delay_hours":3,
        "sources":["https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf",
                   "https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data"],
    }
    protocol["code_hash"]=hashlib.sha256((PROJECT/"src/cryptoai_v13/v16_rebuild.py").read_bytes()).hexdigest()
    (args.output_dir/"protocol.json").write_text(json.dumps(protocol,indent=2)+"\n")
    before=hashes(args.market_root)
    data=subset(load_data(args.market_root,"research_pit48.json"),"2025-01-01",end)
    audit=audit_market(data)
    if any(x.get("internal_missing_hours",0)>0 for x in audit.values()):
        raise ValueError("incomplete market panel; repair source before evaluating")
    canonical=args.market_root/"data/canonical"
    data_hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest()
        for s in data.symbols for f in (canonical/f"{s}_1h.csv",canonical/f"{s}_funding.csv")}
    (args.output_dir/"dataset_manifest.json").write_text(json.dumps({"market_audit":audit,"hashes":data_hashes},indent=2)+"\n")
    targets={}
    screen_returns={}
    rows={}
    for name,spec in menu.items():
        started=time.monotonic()
        target,diag=growth_targets(data,spec)
        targets[name]=target
        approx=screen(data,target)
        screen_returns[name]=approx.equity.pct_change(fill_method=None).fillna(0)
        train=metrics(approx.equity,protocol["train_start"],protocol["train_end"])
        rows[name]={"screen_training":train,"maximum_target_asset_weight":float(diag.max_asset.max()),
                    "maximum_target_gross":float(diag.gross.max())}
        print("TRAIN",name,"net",round(train["return"]*100,2),"dd",round(train["max_drawdown"]*100,2),"seconds",round(time.monotonic()-started,2),flush=True)
    def train_score(name):
        t=rows[name]["screen_training"]
        return np.log1p(max(t["return"],-0.9999))/max(abs(t["max_drawdown"]),0.05)
    chosen=sorted(menu,key=train_score,reverse=True)[:3]
    # Selection record saved BEFORE examining any evaluation-period results.
    (args.output_dir/"training_selection.json").write_text(json.dumps({"selected":chosen,"rows":rows},indent=2)+"\n")
    selected_mix=sum(targets[n] for n in chosen)/len(chosen)
    targets["training_top3_equal"]=selected_mix
    targets["all_families_equal"]=sum(targets[n] for n in menu)/len(menu)
    for label,lookbacks in (("online_30_90",(30,90)),("online_30_90_180",(30,90,180))):
        targets[label],weights=online_mix({n:targets[n] for n in menu},pd.DataFrame(screen_returns),lookbacks)
        weights.to_csv(args.output_dir/f"{label}_allocation.csv",index_label="timestamp")
    reports={}
    for name,target in targets.items():
        started=time.monotonic()
        result=exact_fast(data,target,gross_guard_cap=2.0)
        profile=windows(result.equity,end)
        annual=profile["1Y"]
        gates={"annual_return":annual["return"]>=0.50,"six_month_return":profile["6M"]["return"]>=0.15,
            "three_month_return":profile["3M"]["return"]>=0.05,
            "month_positive":profile["30D"]["return"]>0,"week_positive":profile["7D"]["return"]>0,
            "annual_drawdown":annual["max_drawdown"]>=-0.20,
            "return_drawdown_ratio":(annual["return_over_drawdown"] or 0)>=2.5,
            "positive_without_top3":annual["without_best_3_days"]>0,"no_ruin":not result.ruin}
        start=pd.Timestamp(annual["start"])
        pre=float(result.equity.loc[result.equity.index<start].iloc[-1])
        attribution={"gross":(result.asset_gross.loc[start:].sum()/pre).to_dict(),
                     "fees":(result.asset_fees.loc[start:].sum()/pre).to_dict(),
                     "funding_cost":(result.asset_funding.loc[start:].sum()/pre).to_dict()}
        # Do not hide invalid/optimistic handling at an unavailable-asset boundary.
        missing=(data.frames["open"].isna() | data.close.isna())
        exposed_gap=int((result.positions.shift(1).abs().gt(1e-8)&missing).sum().sum())
        gates["no_held_asset_missing_price"]=exposed_gap==0
        item={"windows":profile,"gates":gates,"research_gate_passed":all(gates.values()),
            "attribution_annual_fraction":attribution,"exposed_missing_asset_hours":exposed_gap,
            "max_realized_asset_weight":float(result.positions.abs().max().max()),
            "max_gross":float(result.gross_exposure.max()),
            "position_adjustments":int(result.asset_orders.loc[start:].abs().gt(1e-12).sum().sum()),
            "evaluation_used_for_selection":False,"promotion_status":"NOT_APPROVED"}
        result.equity.to_csv(args.output_dir/f"{name}_equity.csv",index_label="timestamp",header=["equity"])
        reports[name]=item
        (args.output_dir/"results.json").write_text(json.dumps(reports,indent=2,allow_nan=False)+"\n")
        print("EXACT",name,{k:round(v["return"]*100,2) for k,v in profile.items()},"DD",round(annual["max_drawdown"]*100,2),"PASS",all(gates.values()),"s",round(time.monotonic()-started,1),flush=True)
    # Stress the training-selected finalists and fixed ensembles, not post-hoc best annual ROI.
    finalists=chosen+["training_top3_equal","all_families_equal","online_30_90","online_30_90_180"]
    stress={}
    for name in finalists:
        stress[name]={}
        for label,kwargs,delay in (("severe_cost",{"cost_per_side":0.0012},0),
            ("delay_3h",{},2),("adverse_funding",{"funding_debit_multiplier":2.0,"funding_credit_multiplier":0.5},0)):
            r=exact_fast(data,targets[name].shift(delay).fillna(0),gross_guard_cap=2.0,**kwargs)
            stress[name][label] = windows(r.equity,end)
        (args.output_dir/"stress.json").write_text(json.dumps(stress,indent=2,allow_nan=False)+"\n")
        print("STRESS",name,{k:round(v["1Y"]["return"]*100,2) for k,v in stress[name].items()},flush=True)
    after=hashes(args.market_root)
    if before != after:
        raise RuntimeError("protected source changed during run")
    manifest={"status":"RESEARCH_BATCH_COMPLETE_NOT_APPROVED","input_source_unchanged":True,
        "tested_count":len(reports),"training_selected":chosen,
        "research_gate_passes":[n for n,r in reports.items() if r["research_gate_passed"]],
        "not_a_pristine_holdout":True,"no_paper_or_live_changes":True,
        "remaining_acceptance_requirements":["expanded point-in-time universe and funding completeness",
            "historical delisting and execution filters", "capital/min-order/capacity limits",
            "additional rolling-origin validation", "untouched future paper"]}
    (args.output_dir/"verdict.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest),flush=True)

if __name__=="__main__": main()
