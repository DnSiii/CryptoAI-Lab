#!/usr/bin/env python3
"""KI immutable original receipt attribution. Diagnostic only; never KI rescue."""
from __future__ import annotations
import argparse,glob,json,math
from pathlib import Path

BOOKS=("KI_core_only","KI_full","KI_minus_opportunity","KI_minus_RV","KI_minus_stress")
OS=("ubuntu-22.04","ubuntu-24.04")
FEES=("base","severe")
ORDERS=("carried_before_fill","new_after_fill")
PIN="833013a2e18836a203afd267ca698175907cff8f4c153c919a7811f14cb80752"

def run(root):
    rows={}
    for f in sorted(glob.glob(str(Path(root)/"**"/"*.json"),recursive=True)):
        x=json.loads(Path(f).read_text())
        book=x["path"]
        os=next((o for o in OS if o in f),None)
        if book not in BOOKS or os is None or (os,book) in rows:
            raise ValueError("KI_DUPLICATE_OR_FOREIGN_RECEIPT")
        if x["source_manifest_sha256"]!=PIN or not x["historical_training_only"] or x["validation_2025_read"]:
            raise ValueError("KI_PROVENANCE_FIREWALL")
        cases={(c["fee"],c["order"]):c for c in x["cells"]}
        if len(cases)!=6 or any(not c["passed"] for c in cases.values()):
            raise ValueError("KI_INCOMPLETE_PHYSICAL")
        rows[(os,book)]=cases
    if len(rows)!=10:
        raise ValueError("KI_MISSING_ORIGINAL_BOOKS")
    by_book={}
    for book in BOOKS:
        by_book[book]={}
        for fee in FEES:
            for order in ORDERS:
                a=rows[(OS[0],book)][(fee,order)]
                b=rows[(OS[1],book)][(fee,order)]
                for key in ("final_nav","turnover","fees","slippage","funding","net_log_growth"):
                    if not math.isclose(a[key],b[key],rel_tol=1e-8,abs_tol=1e-5):
                        raise ValueError("KI_CROSS_OS_"+book+"_"+key)
                by_book[book][fee+"|"+order]={
                    key:float(a[key]) for key in
                    ("two_year_cagr","final_nav","turnover","fees","slippage","funding","net_log_growth","max_drawdown")}
    marginals={}
    for name,minus in (("Opportunity","KI_minus_opportunity"),
                       ("RelativeValue","KI_minus_RV"),
                       ("StressRecovery","KI_minus_stress")):
        marginals[name]={}
        for key,full in by_book["KI_full"].items():
            abl=by_book[minus][key]
            marginals[name][key]={
                "full_minus_ablation_net_log_growth":full["net_log_growth"]-abl["net_log_growth"],
                "incremental_turnover_usd":full["turnover"]-abl["turnover"],
                "incremental_fees_slippage_usd":full["fees"]+full["slippage"]-abl["fees"]-abl["slippage"],
                "incremental_signed_funding_usd":full["funding"]-abl["funding"]}
    core_vs_full={}
    for key,full in by_book["KI_full"].items():
        core=by_book["KI_core_only"][key]
        core_vs_full[key]={
            "full_minus_core_log_growth":full["net_log_growth"]-core["net_log_growth"],
            "full_minus_core_turnover_usd":full["turnover"]-core["turnover"],
            "full_minus_core_fees_slippage_usd":full["fees"]+full["slippage"]-core["fees"]-core["slippage"],
            "full_minus_core_funding_usd":full["funding"]-core["funding"]}
    return {"architecture":"KI","training_only":True,"read_only_attribution":True,
        "KI_terminally_rejected":True,"2025_validation_read":False,
        "live_trading_authorized":False,"original_receipts":60,
        "book_metrics":by_book,"full_vs_core":core_vs_full,
        "sleeve_ablation_deltas":marginals,
        "decision":"DIAGNOSTIC_ONLY_NO_KI_RESCUE"}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();r=run(a.root)
    Path(a.output).write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("KI_DIAGNOSTIC",r["decision"],"original",r["original_receipts"])
    print("KI_FULL_VS_CORE",json.dumps(r["full_vs_core"],sort_keys=True))
    print("KI_SLEEVE_COST_ATTRIBUTION",json.dumps(r["sleeve_ablation_deltas"],sort_keys=True))
