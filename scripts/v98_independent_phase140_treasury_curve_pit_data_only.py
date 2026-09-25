#!/usr/bin/env python3
"""V98 Independent Phase140 T10Y2Y ALFRED PIT/Vintage DATA_ONLY audit.

No crypto returns, signals or PnL are computed. Persisted evidence contains only
coverage, provenance/integrity metadata and hashes.
"""
from __future__ import annotations
import csv, hashlib, io, json, time
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/"reports"/"v98_independent_phase140_treasury_curve_pit_data_only.json"
BASE="https://alfred.stlouisfed.org/graph/alfredgraph.csv"
SERIES="T10Y2Y"
START=date(2023,1,1); END=date(2025,12,31)
AVAILABILITY_LAG_DAYS=1
YEARS=(2023,2024,2025)
MIN_COVERAGE=.95
NEGATIVE_CONTROL_DATES=(date(2023,1,10),date(2024,6,10),date(2025,9,10))

def weekdays(y):
    d=date(y,1,1); e=date(y,12,31); n=0
    while d<=e:
        n+=d.weekday()<5
        d+=timedelta(days=1)
    return n

def fetch(obs_date:date,vintage_date:date,retries=4):
    params={"id":SERIES,"cosd":obs_date.isoformat(),"coed":obs_date.isoformat(),"vintage_date":vintage_date.isoformat()}
    last=None
    for attempt in range(retries):
        try:
            req=Request(BASE+"?"+urlencode(params),headers={"User-Agent":"CryptoAI-Lab-V98-Independent-Phase140/1.0","Cache-Control":"no-cache","Connection":"close"})
            with urlopen(req,timeout=30+15*attempt) as r:
                return r.read()
        except Exception as exc:
            last=exc
            if attempt+1<retries: time.sleep(1.5*(attempt+1))
    raise RuntimeError(f"ALFRED request failed for {obs_date} @ {vintage_date}: {last!r}")

def parse_one(raw:bytes,obs_date:date):
    txt=raw.decode("utf-8-sig").strip()
    if not txt:
        return None
    rows=list(csv.reader(io.StringIO(txt)))
    if not rows:
        return None
    # Expected ALFRED graph export: DATE,<series>_<vintage> or DATE,<series>
    if len(rows[0])<2 or rows[0][0].strip().upper()!="DATE":
        raise RuntimeError("unexpected ALFRED CSV schema")
    found=[]
    for row in rows[1:]:
        if len(row)<2: continue
        try: d=datetime.strptime(row[0].strip(),"%Y-%m-%d").date()
        except Exception: continue
        if d!=obs_date: continue
        v=row[1].strip()
        if v in ("",".","NA","NaN"): continue
        try:
            x=Decimal(v)
            if not x.is_finite(): raise InvalidOperation
            norm=format(x.normalize(),"f")
        except (InvalidOperation,ValueError):
            raise RuntimeError(f"non-finite/malformed value at {obs_date}")
        found.append(norm)
    if len(found)>1:
        raise RuntimeError(f"duplicate observation rows at {obs_date}")
    return found[0] if found else None

def one_pass():
    accepted=[]
    requests=0
    d=START
    by_year={y:0 for y in YEARS}
    while d<=END:
        if d.weekday()<5:
            vintage=d+timedelta(days=AVAILABILITY_LAG_DAYS)
            value=parse_one(fetch(d,vintage),d); requests+=1
            if value is not None:
                # Value enters hash only; it is never persisted.
                accepted.append((d.isoformat(),vintage.isoformat(),value))
                by_year[d.year]+=1
            time.sleep(.03)
        d+=timedelta(days=1)
    canon="\n".join(",".join(x) for x in accepted).encode()
    digest=hashlib.sha256(canon).hexdigest()
    expected={y:weekdays(y) for y in YEARS}
    coverage={str(y):by_year[y]/expected[y] for y in YEARS}
    total_expected=sum(expected.values())
    return {
        "valid_pit_observations":len(accepted),
        "expected_business_days":expected,
        "coverage":coverage,
        "global_coverage":len(accepted)/total_expected,
        "normalized_pit_sha256":digest,
        "requests":requests,
    }

def negative_controls():
    out=[]
    for d in NEGATIVE_CONTROL_DATES:
        prior=d-timedelta(days=1)
        leaked=parse_one(fetch(d,prior),d)
        out.append({"observation_date":d.isoformat(),"prior_vintage_date":prior.isoformat(),"future_observation_exposed":leaked is not None})
        time.sleep(.05)
    return out

def main():
    controls=negative_controls()
    a=one_pass(); b=one_pass()
    reproducible=(a["normalized_pit_sha256"]==b["normalized_pit_sha256"] and a["valid_pit_observations"]==b["valid_pit_observations"] and a["coverage"]==b["coverage"])
    gates={
        "negative_controls_no_future_leak":all(not x["future_observation_exposed"] for x in controls),
        "global_coverage":a["global_coverage"]>=MIN_COVERAGE,
        "year_coverage":all(a["coverage"][str(y)]>=MIN_COVERAGE for y in YEARS),
        "reproducible_double_acquisition":reproducible,
    }
    decision="PASS_PIT_DATA_ONLY" if all(gates.values()) else "FAIL_PIT_DATA"
    report={
        "engine":"V98 Independent","phase":"140","mode":"DATA_ONLY_NO_ALPHA_NO_PNL",
        "family":"T10Y2Y ALFRED point-in-time/vintage feasibility",
        "source":{"provider":"ALFRED / Federal Reserve Bank of St. Louis","series":SERIES,"endpoint":BASE},
        "calendar":{"start":START.isoformat(),"end":END.isoformat()},
        "availability_contract":{"vintage_date":"observation_date + 1 calendar day","lag_days":AVAILABILITY_LAG_DAYS},
        "negative_controls":controls,
        "first_acquisition":a,
        "second_acquisition":{"normalized_pit_sha256":b["normalized_pit_sha256"],"valid_pit_observations":b["valid_pit_observations"],"coverage":b["coverage"],"global_coverage":b["global_coverage"],"requests":b["requests"]},
        "gates":gates,"decision":decision,
        "alpha_or_pnl_inspected":False,"crypto_returns_accessed":False,
        "validation_accessed":False,"final_holdout_accessed":False,
        "phase083_selection_use":False,"v16_used":False,"v99_used":False,
        "next_gate":"PASS permits one separately preregistered causal Treasury-curve economic hypothesis; FAIL closes this family."
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":decision,"coverage":a["coverage"],"global_coverage":a["global_coverage"],"reproducible":reproducible,"negative_controls":gates["negative_controls_no_future_leak"]},indent=2))
    return 0 if decision=="PASS_PIT_DATA_ONLY" else 2

if __name__=="__main__":
    raise SystemExit(main())
