#!/usr/bin/env python3
"""KN frozen ORIGINAL receipt-only failure attribution, never rerun/rewrite rejected KN."""
from __future__ import annotations
import argparse,glob,json,collections
from pathlib import Path

def run(root):
    files=sorted(glob.glob(str(Path(root)/"**"/"*.json"),recursive=True))
    if len(files)!=10:raise ValueError("KN_ORIGINAL_RECEIPTS_INCOMPLETE")
    books=collections.defaultdict(dict)
    errors=[]
    for f in files:
        d=json.loads(Path(f).read_text())
        book=d["path"]
        os=next((x for x in ("ubuntu-22.04","ubuntu-24.04") if x in f),None)
        if os is None or os in books[book]:raise ValueError("KN_DUPLICATE_OS")
        books[book][os]=d
    for book,oss in sorted(books.items()):
        if len(oss)!=2:raise ValueError("KN_MISSING_OS_"+book)
        for os,d in sorted(oss.items()):
            passed=[c for c in d["cells"] if c["passed"]]
            failed=[c for c in d["cells"] if not c["passed"]]
            errors.extend([{"book":book,"os":os,"fee":c["fee"],
                            "order":c["order"],"reason":c.get("reason")}
                           for c in failed])
    result={"architecture":"KN","frozen_rejected":True,
            "original_receipt_files":len(files),"books":{},
            "physical_failures":errors,
            "validation_2025_read":False,"trading_authorized":False}
    for book,oss in sorted(books.items()):
        c=next(c for c in oss["ubuntu-24.04"]["cells"]
               if c["fee"]=="base" and c["order"]=="carried_before_fill")
        result["books"][book]=(
            {"passed":True,
             "two_year_cagr":c["two_year_cagr"],
             "turnover":c["turnover"],
             "latch_asset_cuts":c.get("latch_asset_cuts"),
             "latch_event_hours":c.get("latch_event_hours"),
             "max_gross_to_nav":c["max_gross_to_nav"],
             "max_drawdown":c["max_drawdown"],
             "annual_returns":{y:c["annual"][y]["net_return"] for y in ("2023","2024")}}
            if c["passed"] else
            {"passed":False,"reason":c.get("reason")})
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();d=run(a.root)
    Path(a.output).write_text(json.dumps(d,sort_keys=True,indent=2)+"\n")
    print("KN_FROZEN_ORIGINAL_RECEIPT_ATTRIBUTION",json.dumps(d["books"],sort_keys=True))
    print("KN_PHYSICAL_FAILURE_COUNT",len(d["physical_failures"]))
