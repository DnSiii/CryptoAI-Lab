#!/usr/bin/env python3
"""V98 source-only official 1m funding-event mark bounds, NOT exact tick or PnL."""
import argparse,csv,datetime as dt,hashlib,io,json,math,time,urllib.request,zipfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import ASSETS,START,load
from v98_mark_envelope_settlement import read_envelope
MONTHS=tuple(f'{y:04d}-{m:02d}' for y in (2022,2023,2024) for m in range(1,13) if y>2022 or m==12)
BASE='https://data.binance.vision/data/futures/um'
MINUTE=60000
HOUR=3600000

def fetch(url):
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'V98-Independent-Official-Mark-Source-Only/1.0'})
            with urllib.request.urlopen(req,timeout=55) as response:
                if response.status!=200:raise ValueError('V98_1M_HTTP_'+str(response.status))
                return response.read()
        except Exception as exc:
            last=exc
            if attempt<2:time.sleep(attempt+1)
    raise RuntimeError('V98_1M_TRANSPORT_UNAVAILABLE_'+str(last)[:150])

def parse_zip(raw,expected_month,needed):
    found={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members=[x for x in z.infolist() if not x.is_dir()]
        if len(members)!=1 or members[0].file_size>32_000_000:raise ValueError('V98_1M_MEMBER_OR_SIZE')
        with z.open(members[0]) as f:
            previous=-1;count=0
            for row in csv.reader(io.TextIOWrapper(f,encoding='utf-8')):
                try:ms=int(row[0]);o,h,l,c=map(float,row[1:5])
                except (ValueError,IndexError):
                    if count==0 and row and row[0].lower() in ('open_time','open time'):continue
                    raise ValueError('V98_1M_BAD_ROW')
                if ms<=previous or ms%MINUTE or not all(math.isfinite(x) and x>0 for x in (o,h,l,c)) or l>min(o,c) or h<max(o,c):
                    raise ValueError('V98_1M_BAD_OHLC_OR_ORDER')
                if dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).strftime('%Y-%m')!=expected_month:
                    raise ValueError('V98_1M_MONTH_ESCAPE')
                previous=ms;count+=1
                if ms in needed:found[ms]=(l,h)
            if not count:raise ValueError('V98_1M_EMPTY_ARCHIVE')
    return found,count

def download(symbol,month,needed,daily=False):
    if symbol not in ASSETS or (not daily and month not in MONTHS):
        raise ValueError('V98_1M_OUTSIDE_SCOPE')
    if daily:
        date=dt.date.fromisoformat(month)
        if not dt.date(2022,11,30)<=date<=dt.date(2024,12,31):raise ValueError('V98_1M_DAILY_SCOPE')
        url=f'{BASE}/daily/markPriceKlines/{symbol}/1m/{symbol}-1m-{month}.zip'
    else:
        url=f'{BASE}/monthly/markPriceKlines/{symbol}/1m/{symbol}-1m-{month}.zip'
    raw=fetch(url);sha=hashlib.sha256(raw).hexdigest()
    declared=fetch(url+'.CHECKSUM').decode('utf-8').strip().split()[0].lower()
    if sha!=declared:raise ValueError('V98_1M_SHA_MISMATCH_'+symbol+'_'+month)
    found,count=parse_zip(raw,month[:7],needed)
    if daily:
        for ms in found:
            if dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).date()!=date:
                raise ValueError('V98_1M_DAILY_DATE_ESCAPE')
    return found,{'sha256':sha,'rows':count,'matched_minutes':len(found),'url':url}

def build(d,old_lo,old_hi,symbol,months,get=download):
    j=ASSETS.index(symbol);start=int(START.timestamp()*1000)
    events={start+int(t)*HOUR:int(t) for t in np.flatnonzero(d['event'][:,j])
            if dt.datetime.fromtimestamp((start+int(t)*HOUR)/1000,dt.timezone.utc).strftime('%Y-%m') in months}
    if not events:raise ValueError('V98_1M_NO_EVENTS')
    needed={ms+offset for ms in events for offset in (-MINUTE,0)}
    bymonth=defaultdict(set)
    for ms in needed:
        month=dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).strftime('%Y-%m')
        if month in months:bymonth[month].add(ms)
    found={};manifest={}
    for month in months:
        part,receipt=get(symbol,month,bymonth[month])
        manifest['monthly/'+month]=receipt
        for ms,v in part.items():
            if ms in found and found[ms]!=v:raise ValueError('V98_1M_MONTH_CONFLICT')
            found[ms]=v
    missing=needed-found.keys()
    dates=sorted({dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).date().isoformat() for ms in missing})
    if len(dates)>12:raise ValueError('V98_1M_TOO_MANY_MISSING_DAYS_'+str(len(dates)))
    for date in dates:
        dayneed={ms for ms in missing if dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).date().isoformat()==date}
        part,receipt=get(symbol,date,dayneed,daily=True)
        manifest['daily/'+date]=receipt
        for ms,v in part.items():
            if ms in found and found[ms]!=v:raise ValueError('V98_1M_DAILY_CONFLICT')
            found[ms]=v
    if needed-found.keys():raise ValueError('V98_1M_MISSING_MINUTES_'+str(len(needed-found.keys())))
    rows=[];new_width=[];old_width=[];outside=0
    for ms,t in sorted(events.items()):
        low=min(found[ms][0],found[ms-MINUTE][0])
        high=max(found[ms][1],found[ms-MINUTE][1])
        oldl=float(old_lo[t,j]);oldh=float(old_hi[t,j])
        if low<=0 or high<low or low<oldl-1e-7 or high>oldh+1e-7:
            raise ValueError('V98_1M_OUTSIDE_PINNED_1H_'+str(ms))
        orig=float(d['mark'][t,j]);outside+=int(not low<=orig<=high)
        rows.append((symbol,ms,low,high,orig,oldl,oldh))
        new_width.append(high/low-1);old_width.append(oldh/oldl-1)
    nw=np.array(new_width);ow=np.array(old_width)
    return rows,{'symbol':symbol,'events':len(rows),'minute_samples':len(needed),
        'original_conservative_mark_outside_1m_interval':outside,
        'median_width_1m':float(np.median(nw)),'p95_width_1m':float(np.quantile(nw,.95)),
        'median_width_1h':float(np.median(ow)),'p95_width_1h':float(np.quantile(ow,.95)),
        'median_width_reduction_pct':float(100*(1-np.median(nw)/np.median(ow))),
        'source_manifest':manifest,'exact_funding_tick_attested':False,
        'scope':'TRAINING_2022_12_TO_2024_12_ONLY','pnl_computed':False}

def self_test():
    def zipped(lines):
        mem=io.BytesIO()
        with zipfile.ZipFile(mem,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('sample.csv','\n'.join(lines)+'\n')
        return mem.getvalue()
    ts=int(dt.datetime(2023,1,1,tzinfo=dt.timezone.utc).timestamp()*1000)
    lines=[f'{ts+i*MINUTE},100,102,99,101,0' for i in range(3)]
    found,n=parse_zip(zipped(lines),'2023-01',{ts,ts+MINUTE})
    assert n==3 and found[ts]==(99.,102.) and len(found)==2
    for bad in ([lines[1],lines[0]],[lines[0],lines[0]],
                [f'{ts},100,90,110,101,0'],[f'{ts},100,nan,99,101,0']):
        try:parse_zip(zipped(bad),'2023-01',{ts})
        except ValueError:pass
        else:raise AssertionError('V98_1M_FAIL_OPEN')
    fake={'event':np.zeros((18288,4),bool),'mark':np.ones((18288,4))*100}
    fake['event'][744,0]=True
    lo=np.ones((18288,4))*90;hi=np.ones((18288,4))*110
    def sample(s,m,need,daily=False):
        return {ms:(99.,101.) for ms in need},{'sha256':'synthetic','rows':len(need)}
    rows,r=build(fake,lo,hi,'BTCUSDT',('2023-01',),get=sample)
    assert len(rows)==1 and r['minute_samples']==2 and 'daily/2022-12-31' in r['source_manifest']
    return True

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root');p.add_argument('--envelope-csv');p.add_argument('--symbol',choices=ASSETS)
    p.add_argument('--mode',choices=('sample','full'),default='sample')
    p.add_argument('--output');p.add_argument('--bounds-csv');p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test:
        self_test();print('V98_OFFICIAL_1M_SYNTHETIC_SOURCE_PASS_NOT_PNL');return
    if not all((a.root,a.envelope_csv,a.symbol,a.output,a.bounds_csv)):
        p.error('root, envelope-csv, symbol, output and bounds-csv required')
    d=load(a.root);lo,hi,sha=read_envelope(a.envelope_csv,d)
    months=('2023-01',) if a.mode=='sample' else MONTHS
    rows,report=build(d,lo,hi,a.symbol,months)
    if a.mode=='sample' and len(rows)!=93:raise ValueError('V98_1M_SAMPLE_NOT_93_EVENTS')
    if a.mode=='full' and len(rows)!=2286:raise ValueError('V98_1M_FULL_NOT_2286_EVENTS')
    with open(a.bounds_csv,'w',newline='') as f:
        w=csv.writer(f);w.writerow(('symbol','funding_time_ms','one_minute_lower','one_minute_upper',
            'original_conservative_mark','one_hour_lower','one_hour_upper'))
        for s,ms,l,h,orig,ol,oh in rows:w.writerow((s,ms,f'{l:.12f}',f'{h:.12f}',f'{orig:.12f}',f'{ol:.12f}',f'{oh:.12f}'))
    report.update({'decision':'PASS_OFFICIAL_CHECKSUMMED_1M_MARK_INTERVAL_NOT_EXACT_FUNDING_TICK',
        'one_hour_envelope_sha256':sha,'one_minute_bounds_sha256':hashlib.sha256(Path(a.bounds_csv).read_bytes()).hexdigest(),
        'mode':a.mode,'native_funding_rates_authenticated':True,
        'no_2025_or_2026_data_read':True,'no_model_tuning':True,'no_live_authorization':True})
    Path(a.output).write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('V98_OFFICIAL_1M_SOURCE_RESULT',json.dumps({k:v for k,v in report.items() if k!='source_manifest'},sort_keys=True),flush=True)
if __name__=='__main__':main()
