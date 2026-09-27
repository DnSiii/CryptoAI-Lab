#!/usr/bin/env python3
"""V98 Independent Phase171 — T10Y2Y DATA_ONLY acquisition.
No crypto returns/PnL, validation/holdout, V16 or V99 access.
"""
from __future__ import annotations
import csv,hashlib,io,json,math,socket,time,urllib.error,urllib.request
from datetime import date,timedelta
SERIES='T10Y2Y'; START,END=date(2023,1,1),date(2025,12,31)
URLS=(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES}&cosd={START}&coed={END}',f'https://api.stlouisfed.org/fred/graph/fredgraph.csv?id={SERIES}&cosd={START}&coed={END}')
def acquire(attempts=3):
 last=None
 for url in URLS:
  for i in range(attempts):
   try:
    req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-Lab-V98-Independent/1.0','Accept':'text/csv'})
    with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode('utf-8')
   except (TimeoutError,socket.timeout,urllib.error.URLError) as e:
    last=e
    if i+1<attempts:time.sleep(2**i)
 raise last
def parse(raw):
 rows=[];seen=set();qa={'duplicate_dates':0,'malformed_dates':0,'out_of_window_rows':0,'nonfinite_values':0,'missing_values':0,'weekend_dates':0}
 for row in csv.DictReader(io.StringIO(raw)):
  ds=row.get('observation_date') or row.get('DATE') or row.get('date');vs=row.get(SERIES)
  try:d=date.fromisoformat(ds)
  except Exception:qa['malformed_dates']+=1;continue
  if not START<=d<=END:qa['out_of_window_rows']+=1;continue
  if d in seen:qa['duplicate_dates']+=1;continue
  seen.add(d)
  if d.weekday()>=5:qa['weekend_dates']+=1
  try:v=float(vs)
  except Exception:qa['missing_values']+=1;continue
  if not math.isfinite(v):qa['nonfinite_values']+=1;continue
  rows.append((d.isoformat(),v))
 rows.sort();return rows,qa
def canonical(rows):return ''.join(f'{d},{v:.10g}\n' for d,v in rows).encode()
def weekdays(a,b):
 n=0;d=a
 while d<=b:
  if d.weekday()<5:n+=1
  d+=timedelta(days=1)
 return n
def main():
 a,b=parse(acquire()),parse(acquire());rows,qa=a;hs=[hashlib.sha256(canonical(x[0])).hexdigest() for x in (a,b)]
 expected=weekdays(START,END);annual={str(y):sum(d.startswith(str(y)) for d,_ in rows)/weekdays(date(y,1,1),date(y,12,31)) for y in (2023,2024,2025)};coverage=len(rows)/expected
 gates={'double_acquisition_hash_equal':hs[0]==hs[1],'global_weekday_coverage_ge_090':coverage>=.90,'annual_weekday_coverage_ge_085':all(v>=.85 for v in annual.values()),'duplicates_zero':qa['duplicate_dates']==0,'malformed_dates_zero':qa['malformed_dates']==0,'out_of_window_zero':qa['out_of_window_rows']==0,'finite_values':qa['nonfinite_values']==0,'weekend_dates_zero':qa['weekend_dates']==0}
 r={'engine':'V98 Independent','phase':'171','kind':'DATA_ONLY','series':SERIES,'window':[str(START),str(END)],'native_frequency':'daily_business_days','observations':len(rows),'expected_weekdays':expected,'coverage':coverage,'annual_coverage':annual,'first_date':rows[0][0] if rows else None,'last_date':rows[-1][0] if rows else None,'min_value':min((v for _,v in rows),default=None),'max_value':max((v for _,v in rows),default=None),'sha256':hs,'qa':qa,'gates':gates,'missing_policy':'no interpolation/no imputation/no carry-forward/no backfill','economic_firewall':True,'transport_retry_policy':'three bounded attempts per official FRED host, 25s timeout; transport only','status':'PASS_DATA_ONLY' if all(gates.values()) else 'REJECT_DATA_QUALITY_NO_RESCUE'}
 print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
