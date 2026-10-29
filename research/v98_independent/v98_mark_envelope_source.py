#!/usr/bin/env python3
"""V98 original Clean4 training-only checksum-verified two-sided funding mark bounds.
Exact native funding-tick mark remains unavailable; this is a conservative OHLC envelope.
"""
import argparse,csv,datetime,hashlib,json
import numpy as np
from v98_clean4_training_reader import load,ASSETS,START
from v98_mark_archive_full_crosscheck import MONTHS
from v98_mark_archive_crosscheck import download
from v98_mark_archive_daily_recovery import download_daily

def build(d,output_csv):
    rows=[];summary={};monthly_sha={};daily_sha={}
    for j,symbol in enumerate(ASSETS):
        slots=np.flatnonzero(d['event'][:,j]);assert len(slots)==2286
        needed={int((START+t*np.timedelta64(1,'h')).timestamp()*1000) for t in slots}
        candles={};hashes={};dhash={}
        for month in MONTHS:
            print('V98_MARK_ENVELOPE_FETCH',symbol,month,flush=True)
            monthly,sha=download(symbol,month);hashes[month]=sha
            for ms,c in monthly.items():
                if ms in candles and candles[ms]!=c:raise ValueError('V98_MARK_ENVELOPE_MONTH_CONFLICT')
                candles[ms]=c
        missing=[ms for ms in needed if ms not in candles or (ms-3600000 not in candles and ms!=min(needed))]
        for date in sorted(set(datetime.datetime.fromtimestamp(ms/1000,datetime.timezone.utc).strftime('%Y-%m-%d') for ms in missing)):
            daily,sha=download_daily(symbol,date)
            for ms,c in daily.items():
                if ms in candles and candles[ms]!=c:raise ValueError('V98_MARK_ENVELOPE_DAILY_CONFLICT_'+symbol+'_'+str(ms))
                candles[ms]=c
            dhash[date]=sha
        widths=[];outside=0
        for t in slots:
            ms=int((START+t*np.timedelta64(1,'h')).timestamp()*1000)
            if ms not in candles or (ms-3600000 not in candles and t!=0):raise ValueError('V98_MARK_ENVELOPE_MISSING_'+symbol+'_'+str(ms))
            current=candles[ms];prior=candles.get(ms-3600000,current)
            lo=min(current[2],prior[2]);hi=max(current[1],prior[1]);mark=float(d['mark'][t,j])
            if not lo<=mark<=hi:outside+=1
            rows.append((symbol,ms,lo,hi,mark));widths.append(hi/lo-1)
        if outside:raise ValueError('V98_MARK_ENVELOPE_ORIGINAL_OUTSIDE_'+symbol+':'+str(outside))
        summary[symbol]={'events':len(slots),'median_relative_envelope_width':float(np.median(widths)),
          'p95_relative_envelope_width':float(np.quantile(widths,.95)),
          'max_relative_envelope_width':float(np.max(widths)),
          'conservative_original_mark_outside_envelope':outside,'official_daily_gap_archives':len(dhash)}
        monthly_sha[symbol]=hashes;daily_sha[symbol]=dhash
    with open(output_csv,'w',newline='') as f:
        writer=csv.writer(f);writer.writerow(('symbol','funding_time_ms','mark_lower_bound','mark_upper_bound','original_conservative_mark'))
        writer.writerows((s,t,f'{lo:.12f}',f'{hi:.12f}',f'{m:.12f}') for s,t,lo,hi,m in rows)
    raw=open(output_csv,'rb').read()
    return {'decision':'PASS_TWO_SIDED_OFFICIAL_MARK_OHLC_ENVELOPE_NOT_EXACT_NATIVE_TICK',
      'training_only':True,'holdout_read':False,'events':len(rows),'csv_sha256':hashlib.sha256(raw).hexdigest(),
      'monthly_archive_sha256':monthly_sha,'daily_archive_sha256':daily_sha,'summary':summary,
      'exact_funding_tick_mark_attested':False,'pnl_computed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--csv',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=build(load(a.root),a.csv);open(a.output,'w').write(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('monthly_archive_sha256','daily_archive_sha256')},indent=2))
