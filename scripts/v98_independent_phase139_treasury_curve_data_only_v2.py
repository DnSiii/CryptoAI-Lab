#!/usr/bin/env python3
"""V98 Independent Phase139 corrected DATA_ONLY integrity auditor.

Training calendar only: 2023-01-01..2025-12-31.
Persisted output excludes observed values, signs, distributions, returns and performance.
Canonical reproducibility digest covers date + normalized finite value so source revisions
cannot evade the double-acquisition check.
"""
from __future__ import annotations
import csv, hashlib, io, json, sys
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from urllib.request import Request, urlopen

SERIES="T10Y2Y"
START=date(2023,1,1); END=date(2025,12,31)
URL="https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10Y2Y&cosd=2023-01-01&coed=2025-12-31"
YEARS=(2023,2024,2025)
MIN_COVERAGE=0.95

def weekdays(y:int)->int:
    d=date(y,1,1); e=date(y,12,31); n=0
    while d<=e:
        n += d.weekday()<5
        d=date.fromordinal(d.toordinal()+1)
    return n

def acquire()->bytes:
    req=Request(URL,headers={"User-Agent":"CryptoAI-Lab-V98-Independent-Phase139/1.1"})
    with urlopen(req,timeout=30) as r:
        return r.read()

def audit(raw:bytes)->dict:
    text=raw.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(text))
    if reader.fieldnames != ["DATE",SERIES]:
        raise RuntimeError("unexpected schema")
    obs=[]; malformed=0; missing=0
    for row in reader:
        try: d=datetime.strptime(row["DATE"],"%Y-%m-%d").date()
        except Exception: malformed+=1; continue
        if not START<=d<=END: continue
        v=(row.get(SERIES) or "").strip()
        if v in ("",".","NA","NaN"): missing+=1; continue
        try:
            x=Decimal(v)
            if not x.is_finite(): raise InvalidOperation
            normalized=format(x.normalize(),"f")
        except (InvalidOperation, ValueError):
            malformed+=1; continue
        obs.append((d,normalized))
    dates=[d for d,_ in obs]
    duplicate_count=len(dates)-len(set(dates))
    ordered=all(a<b for a,b in zip(dates,dates[1:]))
    future_count=sum(d>date.today() for d in dates)
    by_year={y:sum(d.year==y for d in dates) for y in YEARS}
    expected={y:weekdays(y) for y in YEARS}
    coverage={str(y):by_year[y]/expected[y] for y in YEARS}
    total_expected=sum(expected.values()); total=len(dates)
    canonical="\n".join(f"{d.isoformat()},{v}" for d,v in obs).encode()
    digest=hashlib.sha256(canonical).hexdigest()
    gates={
      "schema_identity": True,
      "unique_dates": duplicate_count==0,
      "strictly_increasing": ordered,
      "no_future_dates": future_count==0,
      "global_coverage": total/total_expected>=MIN_COVERAGE,
      "year_coverage": all(coverage[str(y)]>=MIN_COVERAGE for y in YEARS),
      "no_malformed": malformed==0,
    }
    return {
      "phase":"139","mode":"DATA_ONLY","series":SERIES,
      "calendar":{"start":START.isoformat(),"end":END.isoformat()},
      "counts":{"valid":total,"missing":missing,"malformed":malformed,"duplicates":duplicate_count,"future":future_count},
      "expected_business_days":expected,
      "coverage":coverage,"global_coverage":total/total_expected,
      "normalized_observations_sha256":digest,
      "gates":gates,"decision":"PASS" if all(gates.values()) else "FAIL"
    }

def main():
    a=audit(acquire()); b=audit(acquire())
    a["reproducibility"]={
      "second_normalized_observations_sha256":b["normalized_observations_sha256"],
      "identical_hash":a["normalized_observations_sha256"]==b["normalized_observations_sha256"],
      "identical_integrity_metadata":(
        a["counts"]==b["counts"] and a["coverage"]==b["coverage"] and a["gates"]==b["gates"]
      )
    }
    if not all(a["reproducibility"].values()): a["decision"]="FAIL"
    print(json.dumps(a,sort_keys=True,indent=2))
    return 0 if a["decision"]=="PASS" else 2
if __name__=="__main__": sys.exit(main())
