#!/usr/bin/env python3
"""V98 Independent Phase140 DATA_ONLY PIT/revision audit for T10Y2Y."""
from __future__ import annotations
import calendar,csv,hashlib,io,json,math,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,datetime,timedelta
from decimal import Decimal,InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

OUT=Path('reports/v98_independent_phase140_t10y2y_pit_audit.json')
SERIES='T10Y2Y'; START=date(2023,1,1); END=date(2025,12,31)
FRED='https://fred.stlouisfed.org/graph/fredgraph.csv'
ALFRED='https://alfred.stlouisfed.org/graph/alfredgraph.csv'
VINTAGES=[date(y,m,calendar.monthrange(y,m)[1]) for y in (2023,2024,2025) for m in range(1,13)]
WINDOW_DAYS=60; MIN_OVERLAP=15

def get(url,ua):
    last=None
    for attempt,timeout in enumerate((45,75,105),start=1):
        try:
            req=Request(url,headers={'User-Agent':ua,'Accept':'text/csv','Connection':'close'})
            with urlopen(req,timeout=timeout) as r:return r.read()
        except Exception as exc:
            last=exc
            if attempt<3:time.sleep(2*attempt)
    raise RuntimeError(type(last).__name__) from last

def dec(s):
    s=(s or '').strip()
    if s in ('','.','NA','NaN'):return None
    try:
        x=Decimal(s)
        if not x.is_finite():raise InvalidOperation
        return format(x.normalize(),'f')
    except (InvalidOperation,ValueError):return None

def parse_current(raw):
    rd=csv.reader(io.StringIO(raw.decode('utf-8-sig'))); hdr=next(rd)
    if hdr!=['observation_date',SERIES]:raise RuntimeError('current_schema')
    out={}; malformed=0; dup=0
    for row in rd:
        if len(row)!=2:malformed+=1;continue
        try:d=datetime.strptime(row[0],'%Y-%m-%d').date()
        except Exception:malformed+=1;continue
        v=dec(row[1])
        if v is None:continue
        if d in out:dup+=1
        out[d]=v
    if malformed or dup:raise RuntimeError('current_integrity')
    return out

def one(vintage,current):
    cosd=vintage-timedelta(days=WINDOW_DAYS)
    q=urlencode({'id':SERIES,'vintage_date':vintage.isoformat(),'cosd':cosd.isoformat(),'coed':vintage.isoformat()})
    raw=get(ALFRED+'?'+q,'CryptoAI-Lab-V98-Phase140/1.0')
    rd=csv.reader(io.StringIO(raw.decode('utf-8-sig')));hdr=next(rd)
    expected_value=f'{SERIES}_{vintage.strftime("%Y%m%d")}'
    if len(hdr)!=2 or hdr[0] not in ('DATE','observation_date') or hdr[1]!=expected_value:
        return {'vintage':vintage.isoformat(),'ok':False,'failure':'schema','raw_sha256':hashlib.sha256(raw).hexdigest()}
    seen={}; malformed=0; duplicates=0; future=0
    for row in rd:
        if len(row)!=2:malformed+=1;continue
        try:d=datetime.strptime(row[0],'%Y-%m-%d').date()
        except Exception:malformed+=1;continue
        if d>vintage:future+=1
        x=dec(row[1])
        if x is None:continue
        if d in seen:duplicates+=1
        seen[d]=x
    overlap=sorted(set(seen)&set(current))
    mismatches=sum(seen[d]!=current[d] for d in overlap)
    ok=(malformed==0 and duplicates==0 and future==0 and len(overlap)>=MIN_OVERLAP and mismatches==0)
    return {'vintage':vintage.isoformat(),'ok':ok,'overlap':len(overlap),'mismatches':mismatches,
            'malformed':malformed,'duplicates':duplicates,'future':future,'raw_sha256':hashlib.sha256(raw).hexdigest()}

def main():
    q=urlencode({'id':SERIES,'cosd':(START-timedelta(days=WINDOW_DAYS)).isoformat(),'coed':END.isoformat()})
    craw=get(FRED+'?'+q,'CryptoAI-Lab-V98-Phase140/1.0');current=parse_current(craw)
    results=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        fut={ex.submit(one,v,current):v for v in VINTAGES}
        for f in as_completed(fut):
            v=fut[f]
            try:results.append(f.result())
            except Exception as e:results.append({'vintage':v.isoformat(),'ok':False,'failure':'transport_or_parse_'+type(e).__name__})
    results=sorted(results,key=lambda x:x['vintage'])
    success=sum(bool(x.get('ok')) for x in results)
    mismatch_total=sum(int(x.get('mismatches',0)) for x in results)
    overlap_total=sum(int(x.get('overlap',0)) for x in results)
    min_overlap=min((int(x.get('overlap',0)) for x in results),default=0)
    failures=[{'vintage':x['vintage'],'failure':x.get('failure','gate'),'mismatches':x.get('mismatches',0),'overlap':x.get('overlap',0)}
              for x in results if not x.get('ok')]
    bundle='\n'.join(f"{x.get('vintage')}|{x.get('raw_sha256','MISSING')}" for x in results).encode()
    decision='PASS_PIT_SHORTCUT' if success==len(VINTAGES) and mismatch_total==0 else 'FAIL_PIT_SHORTCUT'
    report={'engine':'V98 Independent','phase':'140','mode':'DATA_ONLY_PIT_AUDIT','series':SERIES,
            'vintage_sample':{'count':len(VINTAGES),'rule':'calendar month-end 2023-01 through 2025-12','window_days':WINDOW_DAYS},
            'counts':{'successful_vintages':success,'total_vintages':len(VINTAGES),'overlap_observations':overlap_total,
                      'mismatches':mismatch_total,'min_overlap_per_vintage':min_overlap},
            'failures':failures,'current_fred_payload_sha256':hashlib.sha256(craw).hexdigest(),
            'alfred_payload_bundle_sha256':hashlib.sha256(bundle).hexdigest(),'decision':decision,
            'values_exposed':False,'crypto_returns_accessed':False,'alpha_computed':False,'pnl_computed':False,
            'validation':None,'final_holdout':None,'phase083_selection_use':False,'v16_used':False,'v99_used':False,
            'parameter_search':False,'rescue_allowed':False}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
