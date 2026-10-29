#!/usr/bin/env python3
"""Official Binance Vision 1h mark-price archive check, NOT native funding-tick mark attestation."""
import argparse,csv,hashlib,io,json,urllib.request,zipfile
import numpy as np
from v98_clean4_training_reader import load,ASSETS,START
MONTH='2023-01'
BASE='https://data.binance.vision/data/futures/um/monthly/markPriceKlines'

def download(symbol,month=MONTH,fetch=None):
    name=f'{symbol}-1h-{month}.zip'
    url=f'{BASE}/{symbol}/1h/{name}'
    if fetch is None:
        def fetch(u):
            with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'V98-Independent-Archive-Audit/1.0'}),timeout=35) as r:return r.read()
    raw=fetch(url);checksum=fetch(url+'.CHECKSUM').decode('utf-8')
    declared=checksum.strip().split()[0].lower()
    actual=hashlib.sha256(raw).hexdigest()
    if declared!=actual:raise ValueError('V98_MARK_ARCHIVE_SHA_MISMATCH_'+symbol)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.namelist())!=1:raise ValueError('V98_MARK_ARCHIVE_MEMBER_COUNT')
        rows=list(csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8')))
    out={}
    for row in rows:
        try:t=int(row[0]);o,h,l,c=map(float,row[1:5])
        except (ValueError,IndexError):continue
        if not all(np.isfinite(x) and x>0 for x in (o,h,l,c)) or l>min(o,c) or h<max(o,c) or t in out:
            raise ValueError('V98_MARK_ARCHIVE_BAD_CANDLE_'+symbol)
        out[t]=(o,h,l,c)
    if len(out)<28*24:raise ValueError('V98_MARK_ARCHIVE_TOO_SHORT_'+symbol)
    return out,actual

def run(d,month=MONTH,fetch=None):
    summary={}
    for j,symbol in enumerate(ASSETS):
        candles,sha=download(symbol,month,fetch)
        times=np.flatnonzero(d['event'][:,j]);selected=[]
        for t in times:
            ms=int((START+t*np.timedelta64(1,'h')).timestamp()*1000)
            if ms in candles:selected.append((t,ms))
        if len(selected)!=93:raise ValueError('V98_MARK_ARCHIVE_FUNDING_MONTH_COUNT_'+symbol+':'+str(len(selected)))
        orig=np.array([d['mark'][t,j] for t,ms in selected]);open_=np.array([candles[ms][0] for t,ms in selected])
        rel=np.abs(orig/open_-1)
        summary[symbol]={'funding_slots_compared':len(selected),'archive_sha256':sha,'mark_kline_open_median_relative_gap':float(np.median(rel)),'mark_kline_open_max_relative_gap':float(np.max(rel))}
    return {'decision':'PASS_OFFICIAL_1H_MARK_KLINE_ARCHIVE_CROSSCHECK_NOT_NATIVE_TICK_MARK','training_only':True,'holdout_read':False,'native_funding_tick_mark_attested':False,'month':month,'summary':summary,'pnl_computed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=run(load(a.root));open(a.output,'w').write(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
