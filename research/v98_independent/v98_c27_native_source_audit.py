"""Independently reconcile C27 hourly prices and native funding to pinned Clean-4 sources.

Training-only audit; no strategy decisions, parameter selection or holdout access.
"""
import argparse
import json
import math
from pathlib import Path
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import ASSETS, HOUR_MS

def check(summary_path, prices, manifest, funding):
    summary_path=Path(summary_path)
    summary=json.loads(summary_path.read_text())
    if summary.get("source")!="AUTHENTICATED_CLEAN4" or summary.get("holdout_accessed") is not False:
        raise ValueError("C27_UNTRUSTED_SUMMARY")
    data=load(prices,manifest,funding)
    if (summary.get("price_manifest_sha256")!=data["price_manifest_sha256"] or
        summary.get("funding_manifest_sha256")!=data["funding_manifest_sha256"]):
        raise ValueError("C27_SOURCE_MANIFEST_MISMATCH")
    rates={a:{(t-START_MS)//HOUR_MS:v for t,v in data["funding"][a].items()} for a in ASSETS}
    report={}
    for scenario in ("1x","2x","4x"):
        ledger=summary_path.with_name(summary_path.stem+"_"+scenario+"_ledger.jsonl")
        previous={a:0. for a in ASSETS}
        count=0
        with ledger.open() as stream:
            for count,line in enumerate(stream,1):
                row=json.loads(line)
                if row["index"]!=count or count>=data["hours"]:
                    raise ValueError("C27_SOURCE_LEDGER_SEQUENCE")
                for a in ASSETS:
                    prior_open=data["bars"][a][count-1][0]
                    current_open=data["bars"][a][count][0]
                    expected_gross=previous[a]*(current_open/prior_open-1)
                    expected_funding=-previous[a]*rates[a].get(count,0.)
                    for label,expected in (("gross_by_asset",expected_gross),
                                           ("funding_by_asset",expected_funding)):
                        actual=row[label][a]
                        if not math.isfinite(actual) or not math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-11):
                            raise ValueError("C27_NATIVE_SOURCE_MISMATCH "+scenario+" "+a+" "+label+" "+str(count))
                # Independently verify the pre-fill marked book and aggregate cashflows.
                # This catches a source-correct gross ledger paired with an
                # inconsistent portfolio state or unaccounted native funding.
                expected_gross_total=sum(previous[a]*(data["bars"][a][count][0]/
                    data["bars"][a][count-1][0]-1) for a in ASSETS)
                expected_funding_total=sum(-previous[a]*rates[a].get(count,0.) for a in ASSETS)
                factor=1+expected_gross_total+expected_funding_total
                if not math.isfinite(factor) or factor<=0:
                    raise ValueError("C27_NATIVE_INSOLVENT_MARK")
                for label,expected in (("gross_return",expected_gross_total),
                                       ("funding_return",expected_funding_total)):
                    if not math.isclose(row[label],expected,rel_tol=1e-10,abs_tol=1e-11):
                        raise ValueError("C27_NATIVE_AGGREGATE_MISMATCH "+scenario+" "+label+" "+str(count))
                for a in ASSETS:
                    ret=data["bars"][a][count][0]/data["bars"][a][count-1][0]-1
                    marked=previous[a]*(1+ret)/factor
                    if not math.isclose(row["weights_before_fill"][a],marked,
                                        rel_tol=1e-10,abs_tol=1e-11):
                        raise ValueError("C27_NATIVE_MARKED_WEIGHT_MISMATCH "+scenario+" "+a+" "+str(count))
                previous=row["weights_after_fill"]
        if count!=data["hours"]-1:
            raise ValueError("C27_SOURCE_INCOMPLETE_LEDGER")
        last=sum(previous[a]*(data["bars"][a][-1][3]/data["bars"][a][-1][0]-1) for a in ASSETS)+1
        if not math.isclose(last,summary["results"][scenario]["last_mark_factor"],rel_tol=1e-10,abs_tol=1e-11):
            raise ValueError("C27_FINAL_NATIVE_CLOSE_MISMATCH")
        report[scenario]={"audited_hours":count,"native_price_funding_reconciled":True,
                          "final_close_reconciled":True}
    return report

def main():
    p=argparse.ArgumentParser()
    for name in ("summary","prices","manifest","funding","output"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    if any("v98_independent" not in x.resolve().parts for x in
           (a.summary,a.prices,a.manifest,a.funding,a.output)):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=check(a.summary,a.prices,a.manifest,a.funding)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
