#!/usr/bin/env python3
"""V98 independent official checksum-verified signed funding-rate audit, 2022-24 ONLY.
No 2025/2026, no strategy PnL, no exact funding-tick markPrice claim.
"""
import argparse,csv,datetime,hashlib,io,json,urllib.request,zipfile
import numpy as np
from v98_clean4_training_reader import load,ASSETS,START
from v98_mark_archive_full_crosscheck import MONTHS
BASE='https://data.binance.vision/data/futures/um'

def fetch_archive(symbol,period,kind='monthly',fetch=None):
    name=f'{symbol}-fundingRate-{period}.zip';url=f'{BASE}/{kind}/fundingRate/{symbol}/{name}'
    if fetch is None:
        def fetch(u):
            with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'V98-Independent-Native-Funding-Audit/1.0'}),timeout=35) as r:return r.read()
    raw=fetch(url);declared=fetch(url+'.CHECKSUM').decode('utf-8').strip().split()[0].lower()
    sha=hashlib.sha256(raw).hexdigest()
    if declared!=sha:raise ValueError('V98_FUNDING_ARCHIVE_SHA_MISMATCH_'+symbol+'_'+period)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.namelist())!=1:raise ValueError('V98_FUNDING_ARCHIVE_MEMBER_COUNT')
        reader=csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8-sig'))
        fields=[x.strip() for x in reader.fieldnames]
        if not {'calc_time','funding_interval_hours','last_funding_rate'}.issubset(fields):
            raise ValueError('V98_FUNDING_ARCHIVE_BAD_HEADER_'+str(fields))
        out={}
        for row in reader:
            t=int(row['calc_time']);r=float(row['last_funding_rate']);interval=float(row['funding_interval_hours'])
            if t in out or not np.isfinite(r) or not np.isfinite(interval) or interval<=0:
                raise ValueError('V98_FUNDING_ARCHIVE_INVALID_'+symbol+'_'+period)
            out[t]=(r,interval)
    if not out:raise ValueError('V98_FUNDING_ARCHIVE_EMPTY_'+symbol+'_'+period)
    return out,sha

def audit(d,fetch=None):
    summary={};all_hashes={};daily_hashes={};total=0
    for j,symbol in enumerate(ASSETS):
        slots=np.flatnonzero(d['event'][:,j]);assert len(slots)==2286
        bymonth={m:[] for m in MONTHS}
        for t in slots:
            ms=int((START+t*np.timedelta64(1,'h')).timestamp()*1000)
            month=datetime.datetime.fromtimestamp(ms/1000,datetime.timezone.utc).strftime('%Y-%m')
            if month not in bymonth:raise ValueError('V98_FUNDING_ARCHIVE_OUTSIDE_TRAINING')
            bymonth[month].append((int(t),ms))
        diffs=[];intervals=[];hashes={};daily_sha={};recovered=0
        for month in MONTHS:
            print('V98_FUNDING_ARCHIVE_FETCH',symbol,month,flush=True)
            rows,sha=fetch_archive(symbol,month,'monthly',fetch);hashes[month]=sha
            missing=[(t,ms) for t,ms in bymonth[month] if ms not in rows]
            print('V98_FUNDING_ARCHIVE_DEBUG',symbol,month,'rows',len(rows),'first',list(rows.items())[:3],'expected',bymonth[month][:3],'missing',len(missing),flush=True)
            for date in sorted(set(datetime.datetime.fromtimestamp(ms/1000,datetime.timezone.utc).strftime('%Y-%m-%d') for t,ms in missing)):
                daily,dsha=fetch_archive(symbol,date,'daily',fetch)
                for ms in set(rows).intersection(daily):
                    if rows[ms]!=daily[ms]:raise ValueError('V98_FUNDING_MONTH_DAILY_CONFLICT_'+symbol+'_'+str(ms))
                rows.update(daily);daily_sha[date]=dsha
            for t,ms in bymonth[month]:
                if ms not in rows:raise ValueError('V98_FUNDING_ARCHIVE_MISSING_'+symbol+'_'+str(ms))
                if (t,ms) in missing:recovered+=1
                rate,interval=rows[ms];diffs.append(abs(rate-float(d['rate'][t,j])));intervals.append(interval)
        if len(diffs)!=2286:raise ValueError('V98_FUNDING_ARCHIVE_INCOMPLETE_'+symbol)
        maxdiff=float(np.max(diffs))
        if maxdiff>1e-10:raise ValueError('V98_FUNDING_ARCHIVE_RATE_CONFLICT_'+symbol+':'+str(maxdiff))
        summary[symbol]={'events_verified':len(diffs),'max_abs_funding_rate_diff':maxdiff,
           'funding_interval_hours':sorted(set(intervals)),
           'events_recovered_from_official_daily':recovered}
        all_hashes[symbol]=hashes;daily_hashes[symbol]=daily_sha;total+=len(diffs)
    return {'decision':'PASS_FULL_NATIVE_SIGNED_FUNDING_RATE_ARCHIVE_NOT_EXACT_MARK_PRICE',
      'training_only':True,'holdout_read':False,'events_verified':total,
      'monthly_archive_count':len(MONTHS)*len(ASSETS),'monthly_sha256':all_hashes,
      'daily_sha256':daily_hashes,'summary':summary,'exact_funding_tick_mark_attested':False,'pnl_computed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=audit(load(a.root));open(a.output,'w').write(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps(out,indent=2))
