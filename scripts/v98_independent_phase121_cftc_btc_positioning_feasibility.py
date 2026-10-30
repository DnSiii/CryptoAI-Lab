#!/usr/bin/env python3
"""V98 Independent Phase121: official CFTC CME Bitcoin positioning DATA_ONLY feasibility. Never emits position values."""
from __future__ import annotations
import csv,hashlib,io,json,time,urllib.request,zipfile
from datetime import date
from pathlib import Path
START=date(2023,1,1); END=date(2025,12,31)
YEARS=(2023,2024,2025)
URL='https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip'
OUT=Path('reports/v98_independent_phase121_cftc_btc_positioning_feasibility.json')

def fetch(url):
    last=None
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-Lab-V98-Independent/1.0'})
            with urllib.request.urlopen(req,timeout=90) as r:return r.status,r.read()
        except Exception as exc:
            last=exc
            if attempt<3:time.sleep(2**attempt)
    raise RuntimeError(f'Phase121 transport failed: {type(last).__name__}') from last

def pick(d,names):
    for n in names:
        if n in d:return d[n]
    return None

def main():
    payload_hashes={}; rows=[]; statuses={}; schema_ok=True
    for y in YEARS:
        status,raw=fetch(URL.format(year=y));statuses[str(y)]=status;payload_hashes[str(y)]=hashlib.sha256(raw).hexdigest()
        if status!=200:continue
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            candidates=[n for n in z.namelist() if n.lower().endswith(('.txt','.csv'))]
            if not candidates: schema_ok=False;continue
            b=z.read(candidates[0]); text=b.decode('utf-8-sig',errors='replace')
            rr=list(csv.DictReader(io.StringIO(text)))
            if not rr: schema_ok=False;continue
            rows.extend(rr)
    dates=[];invalid=0;matched=0
    for r in rows:
        market=str(pick(r,['Market_and_Exchange_Names','Market and Exchange Names','Market_and_Exchange_Names ']) or '').upper()
        if 'BITCOIN' not in market or not ('CHICAGO MERCANTILE' in market or 'CME' in market):continue
        matched+=1
        rawd=pick(r,['Report_Date_as_YYYY-MM-DD','Report_Date_as_YYYY-MM-DD ','Report Date as YYYY-MM-DD'])
        try:d=date.fromisoformat(str(rawd).strip()[:10])
        except Exception:invalid+=1;continue
        if START<=d<=END:dates.append(d)
    unique=sorted(set(dates));dup=len(dates)-len(unique)
    # COT is weekly; 52 weeks/year is the conservative expected denominator for coverage gating.
    expected=52*len(YEARS); coverage=min(1.0,len(unique)/expected)
    idxhash=hashlib.sha256('\n'.join(d.isoformat() for d in unique).encode()).hexdigest()
    passed=all(statuses.get(str(y))==200 for y in YEARS) and schema_ok and matched>0 and coverage>=.95 and invalid==0 and dup==0
    rep={'engine':'V98 Independent','phase':'121','purpose':'official CFTC CME Bitcoin positioning DATA_ONLY feasibility; ZERO POSITION VALUES/ZERO ALPHA/ZERO RETURNS/ZERO PNL','source':'CFTC historical financial futures COT annual archives','training_only':True,'training_start':START.isoformat(),'training_end':END.isoformat(),'validation_accessed':False,'final_holdout_accessed':False,'v16_used':False,'v99_used':False,'values_exposed':False,'descriptives_computed':False,'returns_computed':False,'correlations_computed':False,'alpha_computed':False,'pnl_computed':False,'parameter_search':False,'http_status_by_year':statuses,'payload_sha256_by_year':payload_hashes,'schema_ok':schema_ok,'matched_instrument_rows':matched,'usable_weekly_dates':len(unique),'expected_weekly_dates_conservative':expected,'coverage':coverage,'invalid_records':invalid,'postcanonical_duplicate_dates':dup,'canonical_date_index_sha256':idxhash,'decision':'PASS_DATA_ONLY' if passed else 'REJECT_DATA_SOURCE_NO_RESCUE'}
    OUT.write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps({k:rep[k] for k in ['phase','coverage','invalid_records','postcanonical_duplicate_dates','decision']}))
if __name__=='__main__':main()
