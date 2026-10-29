#!/usr/bin/env python3
"""Checksum-verified official Binance Vision DAILY mark kline gap source, no imputation."""
import csv,hashlib,io,urllib.request,zipfile
import numpy as np
BASE='https://data.binance.vision/data/futures/um/daily/markPriceKlines'
def download_daily(symbol,date,fetch=None):
    name=f'{symbol}-1h-{date}.zip';url=f'{BASE}/{symbol}/1h/{name}'
    if fetch is None:
        def fetch(u):
            with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'V98-Independent-Daily-Mark-Audit/1.0'}),timeout=35) as r:return r.read()
    raw=fetch(url);checksum=fetch(url+'.CHECKSUM').decode('utf-8').strip().split()[0].lower()
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=checksum:raise ValueError('V98_DAILY_MARK_SHA_MISMATCH_'+symbol+'_'+date)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.namelist())!=1:raise ValueError('V98_DAILY_MARK_MEMBER_COUNT')
        rows=list(csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8')))
    out={}
    for row in rows:
        try:t=int(row[0]);o,h,l,c=map(float,row[1:5])
        except (ValueError,IndexError):continue
        if not all(np.isfinite(x) and x>0 for x in (o,h,l,c)) or l>min(o,c) or h<max(o,c) or t in out:
            raise ValueError('V98_DAILY_MARK_INVALID_'+symbol+'_'+date)
        out[t]=(o,h,l,c)
    if not out:raise ValueError('V98_DAILY_MARK_EMPTY_'+symbol+'_'+date)
    return out,sha
