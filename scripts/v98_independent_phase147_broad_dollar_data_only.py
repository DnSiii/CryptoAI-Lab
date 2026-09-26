#!/usr/bin/env python3
"""V98 Independent Phase147 DTWEXBGS DATA_ONLY integrity auditor.
Frozen training calendar only; output excludes observed values and economic metrics.
"""
from __future__ import annotations
import csv, hashlib, io, json, sys, time
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from urllib.request import Request, urlopen
SERIES="DTWEXBGS"; START=date(2023,1,1); END=date(2025,12,31)
URL="https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXBGS&cosd=2023-01-01&coed=2025-12-31"
YEARS=(2023,2024,2025); MIN_COVERAGE=.95; DATE_FIELD="observation_date"
FORBIDDEN_KEYS={"return","returns","correlation","pnl","signal","profit_factor","win_rate","drawdown"}
def weekdays(y):
 d=date(y,1,1); e=date(y,12,31); n=0
 while d<=e:
  n+=d.weekday()<5; d=date.fromordinal(d.toordinal()+1)
 return n
def acquire():
 last=None
 for attempt in range(4):
  try:
   req=Request(URL,headers={"User-Agent":"CryptoAI-Lab-V98-Independent-Phase147/1.0","Accept":"text/csv","Connection":"close"})
   with urlopen(req,timeout=90) as r:return r.read()
  except Exception as exc:
   last=exc
   if attempt<3:time.sleep(2**attempt)
 raise RuntimeError(f"Phase147 transport failed after retries: {type(last).__name__}") from last
def audit(raw):
 reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
 if reader.fieldnames != [DATE_FIELD,SERIES]:raise RuntimeError(f"unexpected schema: {reader.fieldnames!r}")
 obs=[]; malformed=missing=outside=0
 for row in reader:
  try:d=datetime.strptime(row[DATE_FIELD],"%Y-%m-%d").date()
  except Exception:malformed+=1;continue
  if not START<=d<=END:outside+=1;continue
  v=(row.get(SERIES) or "").strip()
  if v in ("",".","NA","NaN"):missing+=1;continue
  try:
   x=Decimal(v)
   if not x.is_finite():raise InvalidOperation
   normalized=format(x.normalize(),"f")
  except (InvalidOperation,ValueError):malformed+=1;continue
  obs.append((d,normalized))
 dates=[d for d,_ in obs]; duplicates=len(dates)-len(set(dates)); ordered=all(a<b for a,b in zip(dates,dates[1:]))
 by_year={y:sum(d.year==y for d in dates) for y in YEARS}; expected={y:weekdays(y) for y in YEARS}; coverage={str(y):by_year[y]/expected[y] for y in YEARS}
 total_expected=sum(expected.values()); total=len(dates); canonical="\n".join(f"{d.isoformat()},{v}" for d,v in obs).encode(); digest=hashlib.sha256(canonical).hexdigest()
 gates={"schema_identity":True,"unique_dates":duplicates==0,"strictly_increasing":ordered,"all_inside_frozen_window":outside==0,"global_coverage":total/total_expected>=MIN_COVERAGE,"year_coverage":all(coverage[str(y)]>=MIN_COVERAGE for y in YEARS),"no_malformed":malformed==0}
 out={"phase":"147","mode":"DATA_ONLY","series":SERIES,"calendar":{"start":START.isoformat(),"end":END.isoformat()},"schema":{"date_field":DATE_FIELD,"value_field":SERIES},"counts":{"valid":total,"missing":missing,"malformed":malformed,"duplicates":duplicates,"outside_window":outside},"expected_weekdays":expected,"coverage":coverage,"global_coverage":total/total_expected,"normalized_observations_sha256":digest,"gates":gates,"decision":"PASS_DATA_ONLY" if all(gates.values()) else "REJECT_DATA_QUALITY_NO_RESCUE"}
 if any(any(token in k.lower() for token in FORBIDDEN_KEYS) for k in out):raise RuntimeError("economic firewall violation")
 return out
def main():
 a=audit(acquire()); b=audit(acquire()); a["reproducibility"]={"second_normalized_observations_sha256":b["normalized_observations_sha256"],"identical_hash":a["normalized_observations_sha256"]==b["normalized_observations_sha256"],"identical_integrity_metadata":a["counts"]==b["counts"] and a["coverage"]==b["coverage"] and a["gates"]==b["gates"] and a["schema"]==b["schema"]}
 if not all(a["reproducibility"].values()):a["decision"]="REJECT_DATA_QUALITY_NO_RESCUE"
 print(json.dumps(a,sort_keys=True,indent=2)); return 0 if a["decision"]=="PASS_DATA_ONLY" else 2
if __name__=="__main__":sys.exit(main())
