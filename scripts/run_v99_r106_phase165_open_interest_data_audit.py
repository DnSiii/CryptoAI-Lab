#!/usr/bin/env python3
"""Phase165 preregistered TRAIN-only Binance open-interest integrity audit. No PnL."""
from __future__ import annotations
import io,json,time,zipfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[1]
OUT=P/'reports'/'candidate_v99_r106_phase165_open_interest_data_audit.json'
PRE=P/'research'/'v99_r106_phase165_open_interest_data_prereg.md'
START=pd.Timestamp('2021-12-01',tz='UTC'); END=pd.Timestamp('2024-01-18',tz='UTC'); A=int(START.timestamp()*1000); B=int(END.timestamp()*1000)
SYMS=['BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','DOGEUSDT']
URL='https://data.binance.vision/data/futures/um/monthly/metrics/{s}/{s}-metrics-{m}.zip'
def get(url):
 for k in range(4):
  try:
   with urlopen(Request(url,headers={'User-Agent':'CryptoAI-Lab-Phase165/1.0'}),timeout=60) as r:return r.read()
  except HTTPError as e:
   if e.code==404:return None
   err=e
  except Exception as e:err=e
  time.sleep(1.5*(k+1))
 raise RuntimeError(repr(err))
def months(): return pd.period_range(START.tz_localize(None).to_period('M'),(END-pd.Timedelta(milliseconds=1)).tz_localize(None).to_period('M'),freq='M')
def load(s):
 rows={}; missing=[]; schemas=[]
 for m in months():
  raw=get(URL.format(s=s,m=str(m)))
  if raw is None: missing.append(str(m)); continue
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   names=[n for n in z.namelist() if n.lower().endswith('.csv')]
   if len(names)!=1: raise RuntimeError(f'{s} {m}: csv count {names}')
   d=pd.read_csv(z.open(names[0])); schemas.append(list(map(str,d.columns)))
  c={str(x).strip().lower():x for x in d.columns}
  tc=next((c[x] for x in ('createtime','create_time','timestamp','time') if x in c),None)
  oc=next((c[x] for x in ('sum_open_interest','sumopeninterest','open_interest','openinterest') if x in c),None)
  if tc is None or oc is None: raise RuntimeError(f'{s} {m}: schema {list(d.columns)}')
  tt=pd.to_datetime(d[tc],utc=True,errors='coerce') if not pd.api.types.is_numeric_dtype(d[tc]) else pd.to_datetime(pd.to_numeric(d[tc],errors='coerce'),unit='ms',utc=True,errors='coerce')
  oo=pd.to_numeric(d[oc],errors='coerce')
  for t,o in zip(tt,oo):
   if pd.isna(t) or pd.isna(o): continue
   ms=int(t.timestamp()*1000)
   if A<=ms<B: rows[ms]=float(o)
 return pd.Series(rows,dtype=float).sort_index(),missing,schemas[-1] if schemas else []
def main():
 q=PRE.read_text(); assert 'BEFORE ANY Phase165 PnL' in q and 'DATA ONLY' in q and '>=90%' in q and '>=85%' in q
 series={}; assets={}; ok=True; cadence_ms=None
 for s in SYMS:
  x,miss,schema=load(s); idx=np.asarray(x.index,dtype=np.int64); dif=np.diff(idx); native=int(np.median(dif)) if len(dif) else 0
  if cadence_ms is None and native>0: cadence_ms=native
  expected=max(1,int((B-A)//native)) if native>0 else 1
  st={'rows':len(x),'native_cadence_ms':native,'coverage_native':len(x)/expected,'first_ms':int(idx[0]) if len(idx) else None,'last_ms':int(idx[-1]) if len(idx) else None,'duplicate_timestamps':int(len(idx)-len(set(idx.tolist()))),'strictly_increasing':bool(len(idx)<2 or np.all(dif>0)),'invalid_nonpositive_oi':int((~np.isfinite(x.to_numpy()) | (x.to_numpy()<=0)).sum()),'missing_archives':miss,'schema':schema}
  st['pass']=bool(st['coverage_native']>=.90 and st['strictly_increasing'] and st['duplicate_timestamps']==0 and st['invalid_nonpositive_oi']==0); ok &= st['pass']; assets[s]=st; series[s]=x
 if cadence_ms and all(len(x) for x in series.values()):
  grid=np.arange(A,B,cadence_ms,dtype=np.int64); good=0
  for t in grid:
   n=sum(bool(len(x) and np.min(np.abs(np.asarray(x.index,dtype=np.int64)-t))<=cadence_ms//2) for x in series.values()); good += n>=4
  cross=good/max(1,len(grid))
 else: cross=0.0
 ok &= cross>=.85
 out={'study':'V99 R106 Phase165 open-interest DATA-only audit','status':'PASS_DATA_ONLY' if ok else 'FAIL_DATA_ONLY','train_start':str(START),'train_end_exclusive':str(END),'assets':assets,'declared_native_cadence_ms':cadence_ms,'cross_section_coverage_ge4':cross,'pnl_computed':False,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'decision':'Eligible only for separately preregistered OI alpha hypothesis.' if ok else 'Reject before alpha; frozen OI data gates failed.'}
 OUT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
