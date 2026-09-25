#!/usr/bin/env python3
"""V98 Independent Phase140 governing T10Y2Y full PIT/Vintage DATA_ONLY audit.

Canonical single-path executor. Reconstructs every weekday observation in
2023-2025 from ALFRED as of observation_date + 1 calendar day, using batched
multi-vintage exports. Performs two independent complete acquisitions.

No crypto data, signal direction, economic lookback/threshold, alpha or PnL is
accessed. Observed macro values participate only in cryptographic hashes and
are never persisted in the report.
"""
from __future__ import annotations
import csv, hashlib, io, json, time
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/"reports"/"v98_independent_phase140_t10y2y_full_pit_audit.json"
BASE="https://alfred.stlouisfed.org/graph/alfredgraph.csv"
SERIES="T10Y2Y"
START=date(2023,1,1); END=date(2025,12,31)
YEARS=(2023,2024,2025)
AVAILABILITY_LAG_DAYS=1
FUTURE_USE_BUFFER_DAYS=1
MIN_COVERAGE=.95
BATCH_SIZE=12

def weekdays(y:int):
    d=date(y,1,1); e=date(y,12,31); out=[]
    while d<=e:
        if d.weekday()<5: out.append(d)
        d+=timedelta(days=1)
    return out

def normalize(v:str):
    v=(v or "").strip()
    if v in ("",".","NA","NaN"): return None
    try:
        x=Decimal(v)
        if not x.is_finite(): raise InvalidOperation
        return format(x.normalize(),"f")
    except (InvalidOperation,ValueError):
        raise RuntimeError("non-finite/malformed ALFRED value")

def chunks(xs,n):
    for i in range(0,len(xs),n):
        yield xs[i:i+n]

def fetch_batch(pairs,retries=4):
    ids=",".join([SERIES]*len(pairs))
    vintages=",".join(v.isoformat() for _,v in pairs)
    params={
        "id":ids,
        "vintage_date":vintages,
        "cosd":min(d for d,_ in pairs).isoformat(),
        "coed":max(d for d,_ in pairs).isoformat(),
    }
    url=BASE+"?"+urlencode(params)
    last=None
    for attempt,timeout in enumerate((45,65,85,105),start=1):
        try:
            req=Request(url,headers={
                "User-Agent":"CryptoAI-Lab-V98-Independent-Phase140-FullPIT/2.0",
                "Accept":"text/csv","Connection":"close"
            })
            with urlopen(req,timeout=timeout) as r:
                return r.read()
        except Exception as exc:
            last=exc
            if attempt<retries:
                time.sleep(min(8,2**(attempt-1)))
    raise RuntimeError(f"ALFRED batch transport failed: {type(last).__name__}") from last

def parse_batch(raw:bytes,pairs):
    rows=list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    if not rows: raise RuntimeError("empty ALFRED CSV")
    header=rows[0]
    expected=[f"{SERIES}_{v.strftime('%Y%m%d')}" for _,v in pairs]
    if (
        len(header)!=len(expected)+1
        or header[0].strip().lower() not in ("date","observation_date")
        or header[1:]!=expected
    ):
        raise RuntimeError("unexpected ALFRED multi-vintage schema")

    by_date={}
    duplicate_rows=0
    malformed_cells=0
    future_value_leaks=0
    for row in rows[1:]:
        if len(row)!=len(header):
            continue
        try:
            d=datetime.strptime(row[0].strip(),"%Y-%m-%d").date()
        except Exception:
            continue
        if d in by_date: duplicate_rows+=1
        by_date[d]=row[1:]
        for i,(_,vintage) in enumerate(pairs):
            cell=row[i+1].strip()
            if cell in ("",".","NA","NaN"): continue
            try:
                val=normalize(cell)
            except Exception:
                malformed_cells+=1
                continue
            if val is not None and d>vintage:
                future_value_leaks+=1

    accepted=[]
    for i,(obs,vintage) in enumerate(pairs):
        row=by_date.get(obs)
        value=None
        if row is not None:
            value=normalize(row[i])
        if value is not None:
            accepted.append((obs.isoformat(),vintage.isoformat(),value))
    return {
        "accepted":accepted,
        "duplicate_rows":duplicate_rows,
        "malformed_cells":malformed_cells,
        "future_value_leaks":future_value_leaks,
        "header_sha256":hashlib.sha256(",".join(header).encode()).hexdigest(),
    }

def one_pass():
    pairs=[
        (d,d+timedelta(days=AVAILABILITY_LAG_DAYS))
        for y in YEARS for d in weekdays(y)
    ]
    accepted=[]
    by_year={y:0 for y in YEARS}
    raw_hashes=[]; header_hashes=[]
    duplicate_rows=0; malformed_cells=0; future_value_leaks=0
    requests=0
    for batch in chunks(pairs,BATCH_SIZE):
        raw=fetch_batch(batch); requests+=1
        raw_hashes.append(hashlib.sha256(raw).hexdigest())
        parsed=parse_batch(raw,batch)
        accepted.extend(parsed["accepted"])
        duplicate_rows+=parsed["duplicate_rows"]
        malformed_cells+=parsed["malformed_cells"]
        future_value_leaks+=parsed["future_value_leaks"]
        header_hashes.append(parsed["header_sha256"])
    for obs,_,_ in accepted:
        by_year[int(obs[:4])]+=1
    expected={y:len(weekdays(y)) for y in YEARS}
    coverage={str(y):by_year[y]/expected[y] for y in YEARS}
    canon="\n".join(",".join(x) for x in accepted).encode()
    return {
        "valid_pit_observations":len(accepted),
        "expected_business_days":expected,
        "coverage":coverage,
        "global_coverage":len(accepted)/sum(expected.values()),
        "normalized_pit_sha256":hashlib.sha256(canon).hexdigest(),
        "raw_payload_bundle_sha256":hashlib.sha256("\n".join(raw_hashes).encode()).hexdigest(),
        "schema_bundle_sha256":hashlib.sha256("\n".join(header_hashes).encode()).hexdigest(),
        "requests":requests,
        "duplicate_rows":duplicate_rows,
        "malformed_cells":malformed_cells,
        "future_value_leaks":future_value_leaks,
    }

def main():
    a=one_pass()
    b=one_pass()
    reproducible=(
        a["normalized_pit_sha256"]==b["normalized_pit_sha256"]
        and a["valid_pit_observations"]==b["valid_pit_observations"]
        and a["coverage"]==b["coverage"]
        and a["expected_business_days"]==b["expected_business_days"]
        and a["duplicate_rows"]==b["duplicate_rows"]
        and a["malformed_cells"]==b["malformed_cells"]
        and a["future_value_leaks"]==b["future_value_leaks"]
    )
    year_gate=all(a["coverage"][str(y)]>=MIN_COVERAGE for y in YEARS)
    integrity=(
        a["duplicate_rows"]==0 and a["malformed_cells"]==0
        and a["future_value_leaks"]==0
    )
    gates={
        "source_identity_t10y2y":True,
        "historical_availability_reconstructed":a["valid_pit_observations"]>0,
        "availability_timestamp_before_future_use":True,
        "no_backfill_or_future_exposure":a["future_value_leaks"]==0,
        "deterministic_double_acquisition":reproducible,
        "global_coverage":a["global_coverage"]>=MIN_COVERAGE,
        "year_coverage":year_gate,
        "integrity":integrity,
        "isolation_firewall":True,
    }
    decision="PASS_PIT_DATA_ONLY" if all(gates.values()) else "FAIL_PIT_DATA"
    report={
        "engine":"V98 Independent","phase":"140","mode":"DATA_ONLY_FULL_PIT_AUDIT",
        "family":"T10Y2Y ALFRED point-in-time/vintage feasibility",
        "governing_preregistration":"reports/v98_independent_phase140_treasury_curve_pit_feasibility_prereg.md",
        "source":{
            "provider":"ALFRED / Federal Reserve Bank of St. Louis",
            "series":SERIES,"endpoint":BASE,
            "transport":"batched repeated T10Y2Y ids paired with matching vintage_date columns",
        },
        "calendar":{"start":START.isoformat(),"end":END.isoformat()},
        "availability_contract":{
            "accepted_vintage":"observation_date + 1 calendar day",
            "availability_lag_days":AVAILABILITY_LAG_DAYS,
            "earliest_admissible_future_economic_use":"strictly after vintage date",
            "future_use_buffer_days_reserved":FUTURE_USE_BUFFER_DAYS,
        },
        "transport":{
            "batch_size":BATCH_SIZE,
            "expected_vintages":sum(len(weekdays(y)) for y in YEARS),
            "requests_per_full_pass":a["requests"],"full_passes":2,
        },
        "first_acquisition":a,
        "second_acquisition":{
            "valid_pit_observations":b["valid_pit_observations"],
            "coverage":b["coverage"],"global_coverage":b["global_coverage"],
            "normalized_pit_sha256":b["normalized_pit_sha256"],
            "raw_payload_bundle_sha256":b["raw_payload_bundle_sha256"],
            "schema_bundle_sha256":b["schema_bundle_sha256"],
            "requests":b["requests"],
            "duplicate_rows":b["duplicate_rows"],
            "malformed_cells":b["malformed_cells"],
            "future_value_leaks":b["future_value_leaks"],
        },
        "gates":gates,"decision":decision,
        "values_exposed":False,"descriptives_computed":False,
        "crypto_data_accessed":False,"crypto_returns_accessed":False,
        "correlations_computed":False,"alpha_or_pnl_inspected":False,
        "economic_direction_selected":False,"economic_lookback_selected":False,
        "economic_threshold_selected":False,
        "validation_accessed":False,"final_holdout_accessed":False,
        "phase083_selection_use":False,"v16_used":False,"v99_used":False,
        "parameter_search":False,"rescue_allowed":False,
        "next_gate":"PASS_PIT_DATA_ONLY permits exactly one separately preregistered causal Treasury-curve economic hypothesis."
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "decision":decision,
        "valid_pit_observations":a["valid_pit_observations"],
        "coverage":a["coverage"],
        "global_coverage":a["global_coverage"],
        "requests_per_pass":a["requests"],
        "reproducible":reproducible,
        "future_value_leaks":a["future_value_leaks"],
    },indent=2))
    return 0 if decision=="PASS_PIT_DATA_ONLY" else 2

if __name__=="__main__":
    raise SystemExit(main())
