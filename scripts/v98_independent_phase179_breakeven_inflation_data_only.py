#!/usr/bin/env python3
"""V98 Independent Phase179 DATA_ONLY checker for FRED T10YIE.
No crypto data/PnL is read. Training era only; validation/final holdout remain closed.
"""
from __future__ import annotations
import csv, hashlib, io, json, math, time, urllib.error, urllib.request
from collections import Counter
from datetime import date
SERIES="T10YIE"; START=date(2023,1,1); END=date(2025,12,31)
URL=f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES}&cosd={START.isoformat()}&coed={END.isoformat()}"
def acquire():
 req=urllib.request.Request(URL,headers={"User-Agent":"CryptoAI-Lab-V98-Independent/1.0","Accept":"text/csv"}); errors=[]
 for attempt in range(4):
  try:
   with urllib.request.urlopen(req,timeout=90) as r: raw=r.read()
   if len(raw)<100: raise RuntimeError(f"implausibly short response: {len(raw)} bytes")
   return raw
  except (TimeoutError,urllib.error.URLError,RuntimeError) as exc:
   errors.append(f"{type(exc).__name__}: {exc}")
   if attempt<3: time.sleep(2**attempt)
 raise RuntimeError("FRED acquisition failed after 4 attempts: "+" | ".join(errors))
def normalize(raw):
 reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))); rows=list(reader); fields=[(x or "").strip() for x in (reader.fieldnames or [])]
 dc="DATE" if "DATE" in fields else "observation_date" if "observation_date" in fields else None
 if not rows or dc is None or SERIES not in fields: raise RuntimeError(f"unexpected FRED schema: {fields}")
 seen=set(); valid=[]; missing=[]
 for row in rows:
  d=date.fromisoformat(row[dc])
  if not START<=d<=END: raise RuntimeError(f"out-of-window observation: {d}")
  if d in seen: raise RuntimeError(f"duplicate date: {d}")
  seen.add(d); s=row[SERIES].strip()
  if s in ("","."): missing.append(d); continue
  x=float(s)
  if not math.isfinite(x) or x<=0: raise RuntimeError(f"invalid value {s!r}: {d}")
  valid.append((d.isoformat(),format(x,".10g")))
 dates=[date.fromisoformat(d) for d,_ in valid]
 if not all(b>a for a,b in zip(dates,dates[1:])): raise RuntimeError("non-monotonic valid dates")
 gaps=[(b-a).days for a,b in zip(dates,dates[1:])]; annual=Counter(d[:4] for d,_ in valid)
 payload=("DATE,"+SERIES+"\n"+"".join(f"{d},{x}\n" for d,x in valid)).encode()
 return payload,valid,missing,dict(sorted(annual.items())),{"source_date_column":dc,"max_calendar_gap_days":max(gaps,default=0)}
def main():
 p1,v1,m1,a1,q1=normalize(acquire()); p2,v2,m2,a2,q2=normalize(acquire()); h1=hashlib.sha256(p1).hexdigest(); h2=hashlib.sha256(p2).hexdigest()
 if not (h1==h2 and p1==p2 and v1==v2 and m1==m2 and a1==a2 and q1==q2): raise RuntimeError("reacquisition mismatch")
 if set(a1)!={"2023","2024","2025"} or min(a1.values())<240: raise RuntimeError(f"insufficient annual coverage: {a1}")
 first=date.fromisoformat(v1[0][0]); last=date.fromisoformat(v1[-1][0])
 if (first-START).days>7 or (END-last).days>7: raise RuntimeError(f"boundary coverage failure: {first}..{last}")
 if q1["max_calendar_gap_days"]>7: raise RuntimeError(f"unexpected calendar gap: {q1}")
 out={"phase":179,"status":"PASS_DATA_ONLY","series":SERIES,"window":[str(START),str(END)],"valid_observations":len(v1),"explicit_missing_rows":len(m1),"first_valid":v1[0][0],"last_valid":v1[-1][0],"annual_valid":a1,"normalized_sha256":h1,"reacquisition_identical":True,"boundary_coverage_le_7d":True,"same_day_use_forbidden":True,"causal_availability_floor":"next_US_business_day_or_more_conservative","crypto_pnl_inspected":False,"validation_inspected":False,"final_holdout_inspected":False,"v16_used":False,"v99_used":False,**q1}
 print(json.dumps(out,sort_keys=True,indent=2))
if __name__=="__main__": main()
