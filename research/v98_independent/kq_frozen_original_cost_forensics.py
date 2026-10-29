#!/usr/bin/env python3
"""KQ frozen ORIGINAL-receipt-only cost/turnover forensic; no rerun or rescue of rejected alpha."""
from __future__ import annotations
import argparse,glob,json,math
from pathlib import Path

BOOKS=("KQ_core_only","KQ_full","KQ_minus_opportunity","KQ_minus_RV","KQ_minus_stress")
def run(root):
    raw={}
    for filename in sorted(glob.glob(str(Path(root)/"**"/"*.json"),recursive=True)):
        d=json.loads(Path(filename).read_text())
        if d.get("path") not in BOOKS:continue
        os="ubuntu-24.04" if "ubuntu-24.04" in filename else "ubuntu-22.04"
        if (os,d["path"]) in raw:raise ValueError("KQ_DUPLICATE_ORIGINAL")
        raw[(os,d["path"])]=d
    if len(raw)!=10:raise ValueError("KQ_MISSING_ORIGINAL_"+str(len(raw)))
    out={"architecture":"KQ","historical_training_only":True,
         "validation_2025_read":False,"future_holdout_read":False,
         "system_pnl_rerun":False,"trading_authorized":False,
         "source":"frozen_original_30cell_receipts_run_40808742939",
         "book_costs":{},"marginal_log_growth":{},"severe_minus_base":{}}
    for book in BOOKS:
        for os in ("ubuntu-22.04","ubuntu-24.04"):
            d=raw[(os,book)]
            rows={(c["fee"],c["order"]):c for c in d["cells"]}
            if len(rows)!=6 or not all(c["passed"] for c in rows.values()):
                raise ValueError("KQ_INCOMPLETE_ORIGINAL_"+book)
            if os=="ubuntu-24.04":
                out["book_costs"][book]={}
                for fee in ("base","severe","supersevere"):
                    c=rows[(fee,"carried_before_fill")]
                    out["book_costs"][book][fee]={k:float(c[k]) for k in (
                        "two_year_cagr","net_log_growth","turnover","funding",
                        "fees","slippage","max_drawdown","max_gross_to_nav")}
                base=rows[("base","carried_before_fill")]
                severe=rows[("severe","carried_before_fill")]
                out["severe_minus_base"][book]={
                    "delta_log_growth":float(severe["net_log_growth"]-base["net_log_growth"]),
                    "delta_turnover":float(severe["turnover"]-base["turnover"]),
                    "delta_fees_slippage":float((severe["fees"]+severe["slippage"])-(base["fees"]+base["slippage"])),
                    "delta_signed_funding":float(severe["funding"]-base["funding"])}
    for name,minus in (("Opportunity","KQ_minus_opportunity"),("RelativeValue","KQ_minus_RV"),("StressRecovery","KQ_minus_stress")):
        out["marginal_log_growth"][name]={}
        for fee in ("base","severe"):
            full=out["book_costs"]["KQ_full"][fee]
            ab=out["book_costs"][minus][fee]
            out["marginal_log_growth"][name][fee]={
                "net_log_growth_difference":full["net_log_growth"]-ab["net_log_growth"],
                "turnover_difference":full["turnover"]-ab["turnover"],
                "funding_difference":full["funding"]-ab["funding"],
                "fee_slippage_difference":(full["fees"]+full["slippage"])-(ab["fees"]+ab["slippage"])}
    out["decision"]="KQ_FROZEN_REJECTION_COST_FORENSICS_NOT_PROMOTION"
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();out=run(a.root)
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("KQ_FROZEN_COST_FORENSICS",json.dumps(out,sort_keys=True))
