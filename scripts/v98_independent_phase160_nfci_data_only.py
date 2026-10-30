#!/usr/bin/env python3
"""V98 Independent Phase160 — NFCI DATA_ONLY integrity gate.
Economic firewall: never loads crypto returns/PnL, validation/holdout, V16, or V99.
"""
from __future__ import annotations
import csv, hashlib, io, json, socket, time, urllib.error, urllib.request
from datetime import date, timedelta

SERIES="NFCI"
URLS=(
 f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES}&cosd=2023-01-01&coed=2025-12-31",
 f"https://api.stlouisfed.org/fred/graph/fredgraph.csv?id={SERIES}&cosd=2023-01-01&coed=2025-12-31",
)
START,END=date(2023,1,1),date(2025,12,31)

def acquire(attempts=2):
 last=None
 for url in URLS:
  for i in range(attempts):
   try:
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoAI-Lab-V98-Independent/1.0","Accept":"text/csv"})
    with urllib.request.urlopen(req,timeout=30) as r:return r.read().decode("utf-8")
   except (TimeoutError,socket.timeout,urllib.error.URLError) as e:
    last=e
    if i+1<attempts:time.sleep(2**i)
 raise last

def parse(raw):
 rows=[];seen=set();qa={"duplicate_dates":0,"malformed_dates":0,"out_of_window_rows":0,"nonfinite_values":0,"missing_values":0}
 for row in csv.DictReader(io.StringIO(raw)):
  ds=row.get("observation_date") or row.get("DATE") or row.get("date");vs=row.get(SERIES)
  try:d=date.fromisoformat(ds)
  except Exception:qa["malformed_dates"]+=1;continue
  if not START<=d<=END:qa["out_of_window_rows"]+=1;continue
  if d in seen:qa["duplicate_dates"]+=1;continue
  seen.add(d)
  try:v=float(vs)
  except Exception:qa["missing_values"]+=1;continue
  if not (-1e100<v<1e100):qa["nonfinite_values"]+=1;continue
  rows.append((d.isoformat(),v))
 rows.sort();return rows,qa

def weeks(y):
 d=date(y,1,1);e=date(y,12,31);seen=set()
 while d<=e:seen.add(d.isocalendar()[:2]);d+=timedelta(days=1)
 return len(seen)
def canonical(rows):return "".join(f"{d},{v:.10g}\n" for d,v in rows).encode()

def main():
 a,b=parse(acquire()),parse(acquire());rows,qa=a;hs=[hashlib.sha256(canonical(x[0])).hexdigest() for x in (a,b)]
 annual={str(y):sum(d.startswith(str(y)) for d,_ in rows)/weeks(y) for y in (2023,2024,2025)};expected=sum(weeks(y) for y in (2023,2024,2025));coverage=len(rows)/expected
 gates={"double_acquisition_hash_equal":hs[0]==hs[1],"global_weekly_coverage_ge_095":coverage>=.95,"annual_weekly_coverage_ge_090":all(v>=.90 for v in annual.values()),"duplicates_zero":qa["duplicate_dates"]==0,"malformed_dates_zero":qa["malformed_dates"]==0,"out_of_window_zero":qa["out_of_window_rows"]==0,"finite_values_only":qa["nonfinite_values"]==0}
 r={"engine":"V98 Independent","phase":"160","kind":"DATA_ONLY","series":SERIES,"window":[START.isoformat(),END.isoformat()],"observations":len(rows),"expected_weeks":expected,"coverage":coverage,"annual_coverage":annual,"sha256":hs,"qa":qa,"gates":gates,"missing_policy":"no imputation/no carry-forward","economic_firewall":True,"transport_retry_policy":"two bounded attempts per official FRED host, 30s timeout; transport only","status":"PASS_DATA_ONLY" if all(gates.values()) else "REJECT_DATA_QUALITY_NO_RESCUE"}
 print(json.dumps(r,indent=2,sort_keys=True));raise SystemExit(0 if r["status"]=="PASS_DATA_ONLY" else 2)
if __name__=="__main__":main()
