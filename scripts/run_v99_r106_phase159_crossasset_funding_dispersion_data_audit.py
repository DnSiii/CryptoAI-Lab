#!/usr/bin/env python3
"""Phase159 preregistered TRAIN-only Binance funding integrity audit. No PnL."""
from __future__ import annotations
import io,json,time,zipfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[1]
OUT=P/'reports'/'candidate_v99_r106_phase159_crossasset_funding_dispersion_data_audit.json'
PRE=P/'research'/'v99_r106_phase159_crossasset_funding_dispersion_prereg.md'
START=pd.Timestamp('2021-12-01',tz='UTC'); END=pd.Timestamp('2024-01-18',tz='UTC')
A=int(START.timestamp()*1000); B=int(END.timestamp()*1000)
SYMS=['BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','DOGEUSDT']
URL='https://data.binance.vision/data/futures/um/monthly/fundingRate/{s}/{s}-fundingRate-{m}.zip'
def get(url):
 for k in range(4):
  try:
   with urlopen(Request(url,headers={'User-Agent':'CryptoAI-Lab-Phase159/1.0'}),timeout=60) as r:return r.read()
  except HTTPError as e:
   if e.code==404:return None
   err=e
  except Exception as e:err=e
  time.sleep(1.5*(k+1))
 raise RuntimeError(repr(err))
def months(): return pd.period_range(START.tz_localize(None).to_period('M'),(END-pd.Timedelta(milliseconds=1)).tz_localize(None).to_period('M'),freq='M')
def load(s):
 rows={}; missing=[]
 for m in months():
  raw=get(URL.format(s=s,m=str(m)))
  if raw is None: missing.append(str(m)); continue
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   names=[n for n in z.namelist() if n.lower().endswith('.csv')]
   if len(names)!=1: raise RuntimeError(f'{s} {m}: csv count {names}')
   d=pd.read_csv(z.open(names[0]))
  c={str(x).strip().lower():x for x in d.columns}
  tc=next((c[x] for x in ('fundingtime','funding_time','calctime','calc_time') if x in c),None)
  rc=next((c[x] for x in ('fundingrate','funding_rate','lastfundingrate','last_funding_rate') if x in c),None)
  if tc is None or rc is None: raise RuntimeError(f'{s} {m}: schema {list(d.columns)}')
  for t,r in zip(pd.to_numeric(d[tc],errors='coerce'),pd.to_numeric(d[rc],errors='coerce')):
   if pd.isna(t) or pd.isna(r): continue
   t=int(t); t=t//1000 if t>10**14 else t
   if A<=t<B: rows[t]=float(r)
 return pd.Series(rows,dtype=float).sort_index(),missing
def main():
 q=PRE.read_text(); assert 'PREREGISTERED BEFORE PnL' in q and 'No holdout rows' in q and '>=95%' in q and '>=90%' in q
 exp=int((B-A)//(8*3600_000)); series={}; assets={}; ok=True
 for s in SYMS:
  x,miss=load(s); idx=np.asarray(x.index,dtype=np.int64)
  st={'rows':len(x),'expected_8h_events':exp,'coverage_vs_8h':len(x)/exp,'missing_archives':miss,'finite':bool(np.isfinite(x.to_numpy()).all()),'strictly_increasing':bool(len(idx)<2 or np.all(np.diff(idx)>0)),'inside_train':bool(len(idx)==0 or (idx.min()>=A and idx.max()<B))}
  st['pass']=bool(st['coverage_vs_8h']>=.95 and st['finite'] and st['strictly_increasing'] and st['inside_train']); ok &= st['pass']; assets[s]=st; series[s]=x
 # frozen cross-sectional availability: union of native events, nearest funding observation within 60m, require >=4 assets.
 ev=sorted(set().union(*(set(x.index) for x in series.values()))); good=0
 for t in ev:
  n=0
  for x in series.values():
   if len(x) and np.min(np.abs(np.asarray(x.index,dtype=np.int64)-t))<=3600_000:n+=1
  good += n>=4
 cross_cov=good/max(1,len(ev)); ok &= cross_cov>=.90
 out={'study':'V99 R106 Phase159 cross-asset funding dispersion DATA audit','status':'PASS_DATA_ONLY' if ok else 'FAIL_DATA_ONLY','train_start':str(START),'train_end_exclusive':str(END),'assets':assets,'cross_section_events':len(ev),'cross_section_ge4_within60m':good,'cross_section_coverage':cross_cov,'pnl_computed':False,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'decision':'Eligible for frozen Phase159 alpha implementation.' if ok else 'Reject before alpha; frozen data gates failed.'}
 OUT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__':main()
