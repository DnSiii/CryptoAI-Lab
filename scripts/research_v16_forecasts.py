"""Monthly purged V16 forecast batch; parameters fixed before evaluation."""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from pathlib import Path
import pandas as pd
from evaluate_v16_recent import PROJECT, hashes, subset, windows
from cryptoai_v13.data import load_data
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.v16_walkforward import forecast_menu,walkforward_forecasts,forecasts_to_targets


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--market-root",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    out=args.output_dir
    if out.resolve().is_relative_to(args.market_root.resolve()): raise ValueError("read-only market input")
    out.mkdir(parents=True,exist_ok=True)
    if (out/"protocol.json").exists(): raise ValueError("do not overwrite an earlier trial")
    menu=forecast_menu()
    source=PROJECT/"src/cryptoai_v13/v16_walkforward.py"
    protocol={"registered_at":pd.Timestamp.now(tz="UTC").isoformat(),
        "menu":{k:v.to_dict() for k,v in menu.items()},
        "code_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "label_purging":"entire holding interval and next-open execution mature strictly before fit time",
        "fit_frequency":"monthly", "observations":"all eligible assets, earlier rolling 180 days",
        "scaling":"training-fold only", "early_stopping":False,
        "backtest_start":"2025-09-01", "end":"2026-08-31",
        "data_previously_used_for_research":True,"automatic_promotion":False,
        "research_gates":{"year":.50,"six_months":.15,"three_months":.05,"month":0.,"week":0.,"year_drawdown":-.20}}
    (out/"protocol.json").write_text(json.dumps(protocol,indent=2)+"\n")
    before=hashes(args.market_root)
    end=pd.Timestamp("2026-08-31T23:00Z")
    data=subset(load_data(args.market_root,"research_pit48.json"),"2025-01-01",end)
    records={}
    for name,spec in menu.items():
        started=time.monotonic()
        def progress(r): print(name,r["fit_at"][:10],"trained",r["training_rows"],flush=True)
        predicted,fits=walkforward_forecasts(data,spec,progress=progress)
        targets=forecasts_to_targets(data,predicted,spec)
        (out/f"{name}_fits.json").write_text(json.dumps(fits,indent=2)+"\n")
        predicted.to_csv(out/f"{name}_forecasts.csv",index_label="timestamp")
        targets.to_csv(out/f"{name}_targets.csv",index_label="timestamp")
        scenarios={}
        for label,kwargs,delay in (("base",{},0),("severe_cost",{"cost_per_side":.0012},0),
                                   ("delay_3h",{},2),("adverse_funding",{"funding_debit_multiplier":2.,"funding_credit_multiplier":.5},0)):
            result=exact_fast(data,targets.shift(delay).fillna(0),gross_guard_cap=2.0,**kwargs)
            scenarios[label]={"windows":windows(result.equity,end),"ruin":result.ruin}
            if label=="base":
                result.equity.to_csv(out/f"{name}_equity.csv",index_label="timestamp",header=["equity"])
                scenarios[label]["exposed_missing_price_hours"]=int((result.positions.shift(1).abs().gt(1e-8)&data.close.isna()).sum().sum())
        base=scenarios["base"]["windows"]
        g=protocol["research_gates"]
        checks={"year":base["1Y"]["return"]>=g["year"],"6m":base["6M"]["return"]>=g["six_months"],
            "3m":base["3M"]["return"]>=g["three_months"],"30d":base["30D"]["return"]>0,
            "7d":base["7D"]["return"]>0,"dd":base["1Y"]["max_drawdown"]>=g["year_drawdown"],
            "no_missing_execution":scenarios["base"]["exposed_missing_price_hours"]==0,
            "without_best3":base["1Y"]["without_best_3_days"]>0,
            "stress_years_positive":all(s["windows"]["1Y"]["return"]>0 for s in scenarios.values()),
            "stress_6m_positive":all(s["windows"]["6M"]["return"]>0 for s in scenarios.values())}
        records[name]={"scenarios":scenarios,"gates":checks,"research_gate_passed":all(checks.values()),
                       "status":"NOT_APPROVED","fold_count":len(fits)}
        (out/"results.json").write_text(json.dumps(records,indent=2,allow_nan=False)+"\n")
        print("EXACT",name,{k:round(v["return"]*100,2) for k,v in base.items()},"DD",round(base["1Y"]["max_drawdown"]*100,2),"PASS",all(checks.values()),"seconds",round(time.monotonic()-started,1),flush=True)
    unchanged=before==hashes(args.market_root)
    if not unchanged: raise RuntimeError("protected source changed")
    verdict={"status":"RESEARCH_COMPLETE_NOT_APPROVED","tested":len(records),
             "passes":[n for n,v in records.items() if v["research_gate_passed"]],"source_preserved":True}
    (out/"verdict.json").write_text(json.dumps(verdict,indent=2)+"\n")
    print(json.dumps(verdict),flush=True)

if __name__=="__main__": main()
