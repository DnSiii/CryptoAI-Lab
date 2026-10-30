#!/usr/bin/env python3
"""BX independent original-receipt arithmetic auditor; never imports BX engine.
Does NOT independently reconstruct event-by-event funding/81 corners.
"""
from __future__ import annotations
import argparse,glob,json,math
from pathlib import Path
PATHS=("BX_core_only","BX_full","BX_minus_opportunity","BX_minus_RV","BX_minus_stress")
OS=("ubuntu-22.04","ubuntu-24.04")
CAPITAL={"immediate":10000.,"capacity_1m":1e6,"capacity_10m":1e7}
FEES={"base":(.0005,.0005),"severe":(.002,.003),"supersevere":(.005,.010)}
ORDERS=("carried_before_fill","new_after_fill")
SHARES=(.65,.15,.10,.10)
ACTIVE={"BX_core_only":(0,),"BX_full":(0,1,2,3),
        "BX_minus_opportunity":(0,2,3),"BX_minus_RV":(0,1,3),
        "BX_minus_stress":(0,1,2)}
def close(a,b):
    return math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-5)
def audit(root):
    receipts={};errors=[]
    for file in glob.glob(str(Path(root)/'*'/'*.json')):
        a=json.load(open(file));p=a.get("path")
        os=next((s for s in OS if s in str(file)),None)
        if p not in PATHS or not os or (p,os) in receipts:
            errors.append(("BAD_RECEIPT",str(file)));continue
        receipts[p,os]=a
    if set(receipts)!={(p,o) for p in PATHS for o in OS}:
        errors.append(("INCOMPLETE",len(receipts)))
    manifest={a.get("source_manifest_sha256") for a in receipts.values()}
    if len(manifest)!=1 or None in manifest:errors.append(("MANIFEST_MISMATCH",))
    count=0;survival=0;cells={}
    for (p,os),a in receipts.items():
        for c in a.get("cells",[]):
            count+=1;survival+=bool(c.get("passed"))
            key=(p,os,c.get("mode"),c.get("fee"),c.get("order"))
            if key in cells:errors.append(("DUPLICATE",key))
            cells[key]=c
            if not c.get("passed"):continue
            mode,fee,order=key[2:]
            if mode not in CAPITAL or fee not in FEES or order not in ORDERS:
                errors.append(("BAD_GRID",key));continue
            if not close(c["initial_nav"],CAPITAL[mode]):
                errors.append(("INITIAL",key))
            if not close(c["final_nav"],sum(c["book_final_nav"])):
                errors.append(("BOOK_SUM",key))
            if not close(c["annual"]["2023"]["start_nav"],CAPITAL[mode]):
                errors.append(("YEAR_START",key))
            if not close(c["annual"]["2023"]["end_nav"],c["annual"]["2024"]["start_nav"]):
                errors.append(("YEAR_BOUNDARY",key))
            if not close(c["annual"]["2024"]["end_nav"],c["final_nav"]):
                errors.append(("YEAR_END",key))
            for i,share in enumerate(SHARES):
                if not close(c["annual"]["2023"]["book_start_nav"][i],share*CAPITAL[mode]):
                    errors.append(("SHARE",key,i))
                if i not in ACTIVE[p] and not close(c["book_final_nav"][i],share*CAPITAL[mode]):
                    errors.append(("INACTIVE_BOOK_MOVED",key,i))
            for f in ("fees","slippage","funding","turnover"):
                if not close(c[f],sum(c["book_"+f])):
                    errors.append(("COST_BOOK_SUM",key,f))
            if not close(c["fees"],c["turnover"]*FEES[fee][0]):
                errors.append(("FEE_RATE",key))
            if not close(c["slippage"],c["turnover"]*FEES[fee][1]):
                errors.append(("SLIPPAGE_RATE",key))
            if not close(c["net_log_growth"],math.log(c["final_nav"]/c["initial_nav"])):
                errors.append(("LOG",key))
            if not close(c["two_year_cagr"],(c["final_nav"]/c["initial_nav"])**(365.25/731)-1):
                errors.append(("CAGR",key))
            for year,duration in (("2023",365),("2024",366)):
                y=c["annual"][year]
                if y["total_utc_days"]!=duration:
                    errors.append(("DAYS",key,year))
                if not close(y["end_nav"],sum(y["book_end_nav"])):
                    errors.append(("YEAR_BOOK",key,year))
                if not close(y["net_log_growth"],math.log(y["end_nav"]/y["start_nav"])):
                    errors.append(("YEAR_LOG",key,year))
                if not close(y["annualized_cagr"],(y["end_nav"]/y["start_nav"])**(365.25/duration)-1):
                    errors.append(("YEAR_CAGR",key,year))
            if not (0<=c["max_drawdown"]<1 and c["min_nav"]>0):
                errors.append(("SOLVENCY",key))
    expected={(p,o,m,f,d) for p in PATHS for o in OS for m in CAPITAL for f in FEES for d in ORDERS}
    if set(cells)!=expected:errors.append(("MISSING",len(expected-set(cells))))
    # Independent contamination check across the original 180 cells.
    for os in OS:
        for mode in CAPITAL:
            for fee in FEES:
                for order in ORDERS:
                    key=(os,mode,fee,order)
                    full=cells.get(("BX_full",)+key,{})
                    if not full.get("passed"):continue
                    for p in PATHS:
                        other=cells.get((p,)+key,{})
                        if not other.get("passed"):continue
                        for i in ACTIVE[p]:
                            for field in ("book_final_nav","book_fees","book_slippage",
                                          "book_funding","book_turnover"):
                                if not close(full[field][i],other[field][i]):
                                    errors.append(("BOOK_CONTAMINATION",p,key,i,field))
    return {"architecture":"BX","original_receipts":len(receipts),
        "cross_os_cells_checked":count,"cross_os_survival":survival,
        "source_manifest_sha256":next(iter(manifest)) if len(manifest)==1 else None,
        "independent_arithmetic_errors":errors[:40],
        "decision":"PASS_BX_ARITHMETIC_ONLY" if not errors and count==180 else
                   "BLOCK_BX_ARITHMETIC",
        "native_funding_independently_rederived":False,
        "validation_2025_read":False,"external_benchmarks_used":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",default="receipts")
    p.add_argument("--output",default="bx90_independent_arithmetic.json")
    a=p.parse_args();r=audit(a.root)
    Path(a.output).write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False))
    print("BX_INDEPENDENT",r["decision"],r["cross_os_survival"],"/",r["cross_os_cells_checked"],
          r["independent_arithmetic_errors"][:3])
    raise SystemExit(2 if r["independent_arithmetic_errors"] else 0)
