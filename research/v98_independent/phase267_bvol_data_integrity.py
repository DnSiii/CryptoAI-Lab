#!/usr/bin/env python3
"""V98 Independent Phase267: Binance BTCBVOLUSDT source integrity, DATA ONLY.

No market prices, returns, strategy, future holdout, or economic PnL.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,io,json,math,zipfile
from pathlib import Path

SYMBOL='BTCBVOLUSDT'
HEAD=['calc_time','symbol','base_asset','quote_asset','index_value']
UTC=dt.timezone.utc
START=dt.date(2023,1,1)
CUT=dt.date(2026,1,1)

def timestamp(s):
    s=s.strip()
    if s.isdigit():
        if len(s)==13:return dt.datetime.fromtimestamp(int(s)/1000,UTC)
        if len(s)==10:return dt.datetime.fromtimestamp(int(s),UTC)
        raise ValueError('unsupported numeric timestamp precision')
    t=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
    if t.tzinfo is None or t.utcoffset()!=dt.timedelta(0):
        raise ValueError('timestamp must be UTC')
    return t.astimezone(UTC)

def audit_day(path:Path,day:dt.date,expected_seconds=86400):
    if not START<=day<CUT:raise ValueError('outside training')
    expected=f'{SYMBOL}-BVOLIndex-{day.isoformat()}.csv'
    with zipfile.ZipFile(path) as z:
        if z.namelist()!=[expected]:raise ValueError('unexpected archive members')
        with z.open(expected) as f:
            rows=csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''))
            if rows.fieldnames!=HEAD:raise ValueError('unexpected BVOL schema')
            count=0;last=None;hours={};first=None
            for r in rows:
                if None in r or set(r)!=set(HEAD):raise ValueError('malformed row')
                if (r['symbol'],r['base_asset'],r['quote_asset'])!=(SYMBOL,'BTC','USDT'):
                    raise ValueError('wrong contract')
                t=timestamp(r['calc_time'])
                if t.date()!=day or (last is not None and t<=last):
                    raise ValueError('noncausal or duplicate timestamp')
                v=float(r['index_value'])
                if not math.isfinite(v) or v<=0:raise ValueError('invalid implied volatility')
                if first is None:first=t
                last=t;count+=1
                key=t.replace(minute=0,second=0,microsecond=0)
                hours[key]=(t,v)
    if count>expected_seconds:raise ValueError('more than expected seconds')
    sampled=[]
    for h,(t,v) in sorted(hours.items()):
        end=h+dt.timedelta(hours=1)
        if t<end-dt.timedelta(seconds=60) or t>=end:continue
        sampled.append({'hour_end_utc':end.isoformat().replace('+00:00','Z'),
                        'observed_at_utc':t.isoformat().replace('+00:00','Z'),
                        'index_value':v})
    return {'date':day.isoformat(),'zip_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'rows':count,'second_coverage':count/expected_seconds,
            'causal_hourly_observations':len(sampled),
            'first_timestamp':first.isoformat() if first else None,
            'last_timestamp':last.isoformat() if last else None,'hourly':sampled}

def audit_folder(folder:Path):
    records=[];missing=[];d=START
    while d<CUT:
        p=folder/f'{SYMBOL}-BVOLIndex-{d.isoformat()}.zip'
        if p.exists():records.append(audit_day(p,d))
        else:missing.append(d.isoformat())
        d+=dt.timedelta(days=1)
    byyear={}
    for year in (2023,2024,2025):
        days=366 if year==2024 else 365
        observed=[r for r in records if r['date'].startswith(str(year))]
        byyear[str(year)]={'expected_days':days,'available_days':len(observed),
                          'coverage':len(observed)/days,
                          'min_second_coverage':min((r['second_coverage'] for r in observed),default=0),
                          'causal_hourly_observations':sum(r['causal_hourly_observations'] for r in observed)}
    valid=all(z['coverage']>=.95 and z['min_second_coverage']>=.95 and z['causal_hourly_observations']>=.95*z['expected_days']*24 for z in byyear.values())
    return {'engine':'V98 Independent','phase':267,'kind':'BVOL_DATA_ONLY',
            'decision':'PENDING_INDEPENDENT_PIT_PROVENANCE' if valid else 'FAIL_DATA_COVERAGE',
            'training_only':True,'validation_accessed':False,'holdout_accessed':False,
            'v14_used':False,'v15_used':False,'v99_used':False,
            'crypto_price_join':False,'pnl_computed':False,'alpha_computed':False,
            'yearly':byyear,'missing_days':missing,'daily':records,
            'source_pit_revision_provenance':'UNRESOLVED: no independent historical source snapshot; never auto-PASS'}

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--folder',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    r=audit_folder(a.folder)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'decision':r['decision'],'yearly':r['yearly'],
                      'missing_count':len(r['missing_days'])},indent=2))
