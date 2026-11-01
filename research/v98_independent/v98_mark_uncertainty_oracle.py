#!/usr/bin/env python3
"""Independent scalar Decimal oracle for V98 funding envelope source uncertainty."""
import argparse,csv,datetime as dt,hashlib,json,math
from decimal import Decimal,InvalidOperation
from pathlib import Path

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
N=13524
CAP=Decimal("0.84")
FIELDS=["asset","funding_hour_utc","funding_rate","mark_lower","mark_upper",
        "mark_width_bps","hypothetical_equity_width_bps"]

def near(a,b):
    return math.isclose(float(a),float(b),rel_tol=1e-11,abs_tol=1e-8)

def audit_rows(rows,d):
    if len(rows)!=N:raise ValueError("ORACLE_EVENT_COUNT")
    widths=[];budget_by_hour={};asset_widths={a:[] for a in ASSETS};event_info=[]
    for i,row in enumerate(rows):
        t=(i//4)*8;j=i%4;asset=ASSETS[j]
        timestamp=(START+dt.timedelta(hours=t)).isoformat()
        if list(row)!=FIELDS or row["asset"]!=asset or row["funding_hour_utc"]!=timestamp or not bool(d["event"][t,j]):
            raise ValueError("ORACLE_EVENT_IDENTITY_OR_ORDER")
        try:
            rate=Decimal(row["funding_rate"]);lo=Decimal(row["mark_lower"])
            hi=Decimal(row["mark_upper"]);w=Decimal(row["mark_width_bps"])
            b=Decimal(row["hypothetical_equity_width_bps"])
        except (InvalidOperation,KeyError):
            raise ValueError("ORACLE_EVENT_PARSE")
        if not all(x.is_finite() for x in (rate,lo,hi,w,b)) or lo<=0 or hi<lo:
            raise ValueError("ORACLE_EVENT_GEOMETRY")
        if not all(near(x,y) for x,y in
            ((rate,d["rate"][t,j]),(lo,d["mark_lower"][t,j]),(hi,d["mark_upper"][t,j]))):
            raise ValueError("ORACLE_SOURCE_VALUE")
        calculated=(hi-lo)/lo*Decimal(10000)
        expected_budget=CAP*abs(rate)*calculated
        if not near(w,calculated) or not near(b,expected_budget):
            raise ValueError("ORACLE_DERIVED_VALUE")
        width=float(calculated);budget=float(expected_budget)
        widths.append(width);asset_widths[asset].append(width)
        budget_by_hour[t]=max(budget_by_hour.get(t,0.),budget)
        event_info.append((asset,timestamp,width))
    if len(budget_by_hour)!=3381 or any(len(v)!=3381 for v in asset_widths.values()):
        raise ValueError("ORACLE_HOUR_COVERAGE")
    def rank(v,p):
        return sorted(v)[max(0,math.ceil(len(v)*p)-1)]
    def stat(v):
        return {"p50":rank(v,.5),"p95":rank(v,.95),"p99":rank(v,.99),"max":max(v)}
    budgets=list(budget_by_hour.values())
    return {"funding_asset_events":len(rows),"funding_hour_slots":len(budgets),
        "width_bps":stat(widths),
        "hypothetical_equity_width_bps_per_slot":stat(budgets),
        "hour_slots_above_equity_width_bps":{str(x):sum(v>x for v in budgets) for x in (1,5,10,50)},
        "max_width_bps_by_asset":{a:max(v) for a,v in asset_widths.items()},
        "top10_widest_event_intervals":[
            {"asset":a,"funding_hour_utc":t,"width_bps":w}
            for a,t,w in sorted(event_info,key=lambda z:(-z[2],z[1],z[0]))[:10]]}

def compare(expected,actual):
    if isinstance(expected,dict):
        if not isinstance(actual,dict) or set(expected)!=set(actual):
            raise ValueError("ORACLE_RECEIPT_SCHEMA")
        for k in expected:compare(expected[k],actual[k])
    elif isinstance(expected,list):
        if not isinstance(actual,list) or len(expected)!=len(actual):
            raise ValueError("ORACLE_RECEIPT_LIST")
        for x,y in zip(expected,actual):compare(x,y)
    elif isinstance(expected,(float,int)) and not isinstance(expected,bool):
        if not near(expected,actual):raise ValueError("ORACLE_RECEIPT_NUMBER")
    elif expected!=actual:raise ValueError("ORACLE_RECEIPT_VALUE")

def main():
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","csv","receipt"):
        p.add_argument("--"+k,required=True)
    a=p.parse_args()
    from v98_2025_full_training_source_bridge import load
    d=load(a.old_root,a.old_envelope,a.new_root,a.corrected_root)
    raw=Path(a.csv).read_bytes()
    with Path(a.csv).open(newline="") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FIELDS:raise ValueError("ORACLE_CSV_FIELDS")
        rows=list(reader)
    receipt=json.loads(Path(a.receipt).read_text())
    if hashlib.sha256(raw).hexdigest()!=receipt.get("canonical_csv_sha256"):
        raise ValueError("ORACLE_CSV_SHA")
    expected=audit_rows(rows,d)
    compare(expected,{k:receipt[k] for k in expected})
    if receipt.get("decision")!="PASS_ENVELOPE_UNCERTAINTY_QUANTIFIED_NOT_EXACT_MARK" or not (
        receipt.get("hypothetical_local_equity_fraction_only") is True and
        receipt.get("not_a_dynamic_nav_or_cagr_bound") is True and
        receipt.get("exact_exchange_funding_event_marks_present") is False and
        receipt.get("pnl_computed") is False and
        receipt.get("holdout_accessed") is False and
        receipt.get("2026_data_accessed") is False):
        raise ValueError("ORACLE_SOURCE_SCOPE")
    tampered=0
    for kind in ("inverted_interval","rate_change","duplicate_event","missing_event"):
        fake=[dict(r) for r in rows]
        if kind=="inverted_interval":
            fake[0]["mark_upper"]="0"
        elif kind=="rate_change":
            fake[0]["funding_rate"]=str(float(fake[0]["funding_rate"])+.001)
        elif kind=="duplicate_event":
            fake[1]=dict(fake[0])
        else:fake.pop(0)
        try:audit_rows(fake,d)
        except ValueError:tampered+=1
        else:raise ValueError("ORACLE_TAMPER_UNDETECTED_"+kind)
    if tampered!=4:raise ValueError("ORACLE_TAMPER_COVERAGE")
    print(json.dumps({"decision":"PASS_INDEPENDENT_DECIMAL_SOURCE_ORACLE_NOT_EXACT_MARK",
        "source_events_reconciled":N,"funding_slots":3381,
        "negative_controls_rejected":tampered,
        "receipt_numeric_mismatches":0,"pnl_computed":False,
        "holdout_accessed":False},sort_keys=True))
if __name__=="__main__":main()
