#!/usr/bin/env python3
"""JF independent ORIGINAL-artifact-only audit. No engine, governor, signal or official reconciler import.
Consumes 10 raw GitHub Actions JSON book artifacts, two OS x five books x six physical cases.
Training 2023-24 only; no 2025, benchmark internals, Frozen, paper or orders.
"""
from __future__ import annotations
import argparse,glob,hashlib,json,math
from pathlib import Path

BOOKS=("JF_core_only","JF_full","JF_minus_opportunity","JF_minus_RV","JF_minus_stress")
PLATFORMS=("ubuntu-22.04","ubuntu-24.04")
COSTS=("base","severe","supersevere")
ORDERS=("carried_before_fill","new_after_fill")
EXPECTED_SHA="833013a2e18836a203afd267ca698175907cff8f4c153c919a7811f14cb80752"
EPS=1e-7

def close(x,y,abs_tol=2e-5):
    return math.isclose(float(x),float(y),rel_tol=2e-8,abs_tol=abs_tol)

def audit(root):
    errors=[]
    books={}
    fingerprints={}
    seen=set()
    paths=sorted(glob.glob(str(Path(root)/"**"/"*.json"),recursive=True))
    for filename in paths:
        try:
            data=json.loads(Path(filename).read_text())
            book=data["path"]
            platform=next(p for p in PLATFORMS if p in filename)
            key=(platform,book)
            if book not in BOOKS or key in seen:
                raise ValueError("duplicate or invalid book")
            seen.add(key)
            books[key]=data
            sha=data["source_manifest_sha256"]
            if sha!=EXPECTED_SHA:errors.append(["SOURCE_PIN",platform,book,sha])
            if (data.get("historical_training_only") is not True or
                data.get("validation_2025_read") is not False or
                data.get("external_benchmarks_used") is not False):
                errors.append(["SOURCE_FIREWALL",platform,book])
            cells=data.get("cells",[])
            if len(cells)!=6:errors.append(["CELL_INVENTORY",platform,book,len(cells)])
            unique=set()
            for c in cells:
                k=(c.get("fee"),c.get("order"))
                if k in unique or k not in {(f,o) for f in COSTS for o in ORDERS}:
                    errors.append(["COST_GRID",platform,book,str(k)])
                unique.add(k)
                if not c.get("passed"):
                    errors.append(["PHYSICAL_FAILURE",platform,book,str(k),c.get("reason")])
                    continue
                if (c.get("validation_2025_read") is not False or
                    c.get("trading_authorized") is not False or
                    c.get("external_benchmarks_used") is not False):
                    errors.append(["CELL_FIREWALL",platform,book,str(k)])
                a,b=float(c["initial_nav"]),float(c["final_nav"])
                y0,y1=c["annual"]["2023"],c["annual"]["2024"]
                if not (a>0 and b>0 and float(c["min_nav"])>0 and
                        c["max_drawdown"]>=0 and c["max_drawdown"]<1):
                    errors.append(["SURVIVAL",platform,book,str(k)])
                tests={
                    "NAV":close(b,a*(1+c["net_total_return"])),
                    "LOG":close(math.log(b/a),c["net_log_growth"]),
                    "CAGR":close((b/a)**(365.25/731)-1,c["two_year_cagr"]),
                    "ANNUAL_CONTINUITY":close(y0["start_nav"],a) and
                        close(y0["end_nav"],y1["start_nav"]) and close(y1["end_nav"],b),
                    "YEAR_LOGS":close(math.log(y0["end_nav"]/y0["start_nav"]),y0["net_log_growth"])
                        and close(math.log(y1["end_nav"]/y1["start_nav"]),y1["net_log_growth"]),
                    "ANNUAL_RETURNS":close(y0["end_nav"]/y0["start_nav"]-1,y0["net_return"])
                        and close(y1["end_nav"]/y1["start_nav"]-1,y1["net_return"]),
                    "COST_NONNEGATIVE":all(float(c[z])>=-EPS for z in ("fees","slippage","turnover")),
                    "DAY_INVENTORY":int(c["total_utc_days"])==731 and
                        int(y0["total_utc_days"])==365 and int(y1["total_utc_days"])==366,
                    "POSITIVE_DAYS":0<=int(c["positive_utc_days"])<=731,
                    "HOURLY_WINS":int(c["positive_hours"])+int(c["negative_hours"])<=17544,
                }
                wins=int(c["positive_hours"]);losses=int(c["negative_hours"])
                if wins and losses and c["hourly_net_payoff"] is not None:
                    tests["PF_PAYOFF_WIN_RATE"]=close(
                        c["hourly_net_profit_factor"],
                        c["hourly_net_payoff"]*wins/losses) and close(
                        c["hourly_net_win_rate"],wins/(wins+losses))
                for name,ok in tests.items():
                    if not ok:errors.append([name,platform,book,str(k)])
                fingerprint=(platform,book,*k)
                fingerprints[fingerprint]={
                    "final_nav":b,"funding":float(c["funding"]),
                    "fees":float(c["fees"]),"slippage":float(c["slippage"]),
                    "turnover":float(c["turnover"]),"max_drawdown":float(c["max_drawdown"]),
                    "log":float(c["net_log_growth"]),
                    "2023":float(y0["net_log_growth"]),"2024":float(y1["net_log_growth"]),
                    "cagr":float(c["two_year_cagr"]),
                }
        except Exception as exc:
            errors.append(["READ_OR_SCHEMA",filename,str(exc)])
    expected={(p,b) for p in PLATFORMS for b in BOOKS}
    if seen!=expected:errors.append(["MISSING_OR_DUPLICATE_BOOKS",sorted(expected-seen),len(paths)])
    for book in BOOKS:
        for fee in COSTS:
            for order in ORDERS:
                x=fingerprints.get(("ubuntu-22.04",book,fee,order))
                y=fingerprints.get(("ubuntu-24.04",book,fee,order))
                if x is None or y is None:
                    errors.append(["MISSING_OS_CELL",book,fee,order]);continue
                for metric in x:
                    if not close(x[metric],y[metric]):
                        errors.append(["CROSS_OS_DISAGREEMENT",book,fee,order,metric])
    marginals={}
    for name,minus in (("Opportunity","JF_minus_opportunity"),
                       ("RelativeValue","JF_minus_RV"),
                       ("StressRecovery","JF_minus_stress")):
        marginals[name]={}
        for fee in ("base","severe"):
            for order in ORDERS:
                a=fingerprints.get(("ubuntu-24.04","JF_full",fee,order))
                b=fingerprints.get(("ubuntu-24.04",minus,fee,order))
                if not a or not b:continue
                per_year={yr:a[yr]-b[yr] for yr in ("2023","2024")}
                total=per_year["2023"]+per_year["2024"]
                marginals[name][fee+"|"+order]={
                    **per_year,"combined":total,
                    "passed":total>.02 and min(per_year.values())>=-.03}
    full_base=fingerprints.get(("ubuntu-24.04","JF_full","base","carried_before_fill"))
    full_severe=fingerprints.get(("ubuntu-24.04","JF_full","severe","carried_before_fill"))
    economic_pass=not errors and all(
        d["passed"] for sleeve in marginals.values() for d in sleeve.values()
    ) and len(marginals)==3 and all(len(s)==4 for s in marginals.values())
    for fee,minimum in (("base",.50),("severe",.30)):
        for order in ORDERS:
            f=fingerprints.get(("ubuntu-24.04","JF_full",fee,order))
            if not f or f["cagr"]<=minimum or min(f["2023"],f["2024"])<=0 or f["turnover"]>600000:
                economic_pass=False
            if fee=="severe" and f and f["max_drawdown"]>=.45:
                economic_pass=False
    decision=("BLOCK_JF_INDEPENDENT_RECEIPT_AUDIT" if errors else
              "PASS_JF_TRAINING_ONLY_REQUIRES_2025_VALIDATION" if economic_pass else
              "REJECT_JF_HISTORICAL_GROWTH_OR_MARGINAL")
    return {"architecture":"JF","decision":decision,"source_sha_expected":EXPECTED_SHA,
            "raw_files":len(paths),"distinct_original_receipts":len(fingerprints),
            "physical_cells":len(fingerprints)//2,
            "cross_os_reproducible":not any(e[0]=="CROSS_OS_DISAGREEMENT" for e in errors),
            "errors":errors[:60],"marginal_log_growth":marginals,
            "full_base":full_base,"full_severe":full_severe,
            "validation_2025_read":False,"trading_authorized":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    result=audit(a.root)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("JF_ORIGINAL_ARTIFACT_INDEPENDENT_AUDIT",result["decision"],
          "raw",result["raw_files"],"receipts",result["distinct_original_receipts"],
          "cells",result["physical_cells"],"errors",result["errors"][:3])
    for key in ("full_base","full_severe"):
        if result[key]:print(key,result[key])
    print("JF_INDEPENDENT_MARGINALS",json.dumps(result["marginal_log_growth"],sort_keys=True))
    raise SystemExit(2 if result["errors"] else 0)
