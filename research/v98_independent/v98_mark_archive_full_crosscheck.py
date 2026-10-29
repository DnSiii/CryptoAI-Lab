#!/usr/bin/env python3
"""V98 official checksum-verified hourly mark archives, ALL Clean4 2022-24 funding slots.
Mark 1h open is a timestamp proxy, NOT exact exchange funding-tick mark attestation.
"""
import argparse,datetime,hashlib,json,math
import numpy as np
from v98_clean4_training_reader import load,ASSETS,START
from v98_mark_archive_crosscheck import download
from v98_mark_archive_daily_recovery import download_daily
MONTHS=tuple(f'{y}-{m:02d}' for y in (2022,2023,2024) for m in range(1,13) if y>2022 or m==12)

def run(d,fetch=None):
    summary={};sha_by_asset={};total=0
    for j,symbol in enumerate(ASSETS):
        slots=np.flatnonzero(d['event'][:,j]);assert len(slots)==2286
        monthly={m:[] for m in MONTHS}
        for t in slots:
            ms=int((START+t*np.timedelta64(1,'h')).timestamp()*1000)
            month=datetime.datetime.fromtimestamp(ms/1000,datetime.timezone.utc).strftime('%Y-%m')
            if month not in monthly:raise ValueError('V98_MARK_ARCHIVE_OUTSIDE_TRAINING')
            monthly[month].append((int(t),ms))
        orig=[];proxy=[];outside=[];hashes={};daily_hashes={};recovered=0
        for month in MONTHS:
            print('V98_MARK_ARCHIVE_FETCH',symbol,month,flush=True)
            candles,sha=download(symbol,month,fetch);hashes[month]=sha
            print('V98_MARK_ARCHIVE_ROWS',symbol,month,len(candles),flush=True)
            missing=[(t,ms) for t,ms in monthly[month] if ms not in candles]
            for date in sorted(set(datetime.datetime.fromtimestamp(ms/1000,datetime.timezone.utc).strftime('%Y-%m-%d') for t,ms in missing)):
                daily,dsha=download_daily(symbol,date,fetch)
                for ms in set(candles).intersection(daily):
                    if candles[ms]!=daily[ms]:raise ValueError('V98_MARK_MONTH_DAILY_CONFLICT_'+symbol+'_'+str(ms))
                candles.update(daily);daily_hashes[date]=dsha
            for t,ms in monthly[month]:
                if ms not in candles:raise ValueError('V98_MARK_ARCHIVE_MISSING_EVENT_'+symbol+'_'+str(ms))
                if (t,ms) in missing:recovered+=1
                o,h,l,c=candles[ms];m=float(d['mark'][t,j])
                orig.append(m);proxy.append(o);outside.append(not l<=m<=h)
        if len(orig)!=2286:raise ValueError('V98_MARK_ARCHIVE_INCOMPLETE_'+symbol)
        orig=np.asarray(orig);proxy=np.asarray(proxy);gap=np.abs(orig/proxy-1)
        summary[symbol]={'funding_slots_compared':len(orig),'mark_kline_open_median_relative_gap':float(np.median(gap)),
          'mark_kline_open_p95_relative_gap':float(np.quantile(gap,.95)),
          'mark_kline_open_max_relative_gap':float(np.max(gap)),
          'conservative_mark_outside_same_hour_mark_kline_fraction':float(np.mean(outside)),
          'relative_gap_above_1pct_fraction':float(np.mean(gap>.01)),
          'relative_gap_above_5pct_fraction':float(np.mean(gap>.05)),
          'funding_slots_recovered_from_official_daily':recovered,'daily_archive_sha256':daily_hashes}
        sha_by_asset[symbol]=hashes;total+=len(orig)
    return {'decision':'PASS_FULL_CLEAN4_OFFICIAL_HOURLY_MARK_ARCHIVE_CROSSCHECK_NOT_EXACT_TICK_MARK',
       'training_only':True,'holdout_read':False,'native_funding_tick_mark_attested':False,
       'funding_events_compared':total,'archive_count':len(MONTHS)*len(ASSETS),
       'archive_sha256':sha_by_asset,'summary':summary,'pnl_computed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    x=run(load(a.root));open(a.output,'w').write(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps(x,indent=2))
