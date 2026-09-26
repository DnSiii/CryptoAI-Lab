#!/usr/bin/env python3
"""V98 Independent Phase156 — VIXCLS DATA_ONLY integrity gate.
Economic firewall: this script never loads crypto returns/PnL/validation/holdout/V16/V99.
"""
from __future__ import annotations
import csv, hashlib, io, json, urllib.request
from datetime import date

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&cosd=2023-01-01&coed=2025-12-31"
START, END = date(2023,1,1), date(2025,12,31)

def acquire():
    req=urllib.request.Request(URL, headers={"User-Agent":"CryptoAI-Lab-V98-Independent/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r: return r.read().decode("utf-8")

def parse(raw):
    rows=[]; malformed=duplicates=out=nonpositive=0; seen=set()
    for row in csv.DictReader(io.StringIO(raw)):
        ds=row.get("observation_date") or row.get("DATE") or row.get("date")
        vs=row.get("VIXCLS")
        try: d=date.fromisoformat(ds)
        except Exception: malformed+=1; continue
        if not (START <= d <= END): out+=1; continue
        if d in seen: duplicates+=1; continue
        seen.add(d)
        try: v=float(vs)
        except Exception: continue  # FRED holiday '.' is missing, not malformed observation
        if v <= 0: nonpositive+=1
        rows.append((d.isoformat(), v))
    rows.sort()
    return rows, {"duplicate_dates":duplicates,"malformed_dates":malformed,"out_of_window_rows":out,"nonpositive_values":nonpositive}

def business_days(y):
    d=date(y,1,1); e=date(y,12,31); n=0
    while d<=e:
        n += d.weekday()<5
        d=date.fromordinal(d.toordinal()+1)
    return n

def canonical(rows): return "".join(f"{d},{v:.10g}\n" for d,v in rows).encode()

def main():
    a, b = parse(acquire()), parse(acquire())
    rows, qa=a
    hashes=[hashlib.sha256(canonical(x[0])).hexdigest() for x in (a,b)]
    annual={str(y):sum(d.startswith(str(y)) for d,_ in rows)/business_days(y) for y in (2023,2024,2025)}
    total_bd=sum(business_days(y) for y in (2023,2024,2025))
    coverage=len(rows)/total_bd
    gates={"double_acquisition_hash_equal":hashes[0]==hashes[1],"global_coverage_ge_095":coverage>=.95,"annual_coverage_ge_095":all(v>=.95 for v in annual.values()),"duplicates_zero":qa["duplicate_dates"]==0,"malformed_dates_zero":qa["malformed_dates"]==0,"out_of_window_zero":qa["out_of_window_rows"]==0,"positive_values_only":qa["nonpositive_values"]==0}
    result={"engine":"V98 Independent","phase":"156","kind":"DATA_ONLY","series":"VIXCLS","window":[START.isoformat(),END.isoformat()],"observations":len(rows),"business_days":total_bd,"coverage":coverage,"annual_coverage":annual,"sha256":hashes,"qa":qa,"gates":gates,"missing_policy":"no imputation/no carry-forward","economic_firewall":True,"status":"PASS_DATA_ONLY" if all(gates.values()) else "REJECT_DATA_QUALITY_NO_RESCUE"}
    print(json.dumps(result,indent=2,sort_keys=True))
    if result["status"]!="PASS_DATA_ONLY": raise SystemExit(2)
if __name__=="__main__": main()
