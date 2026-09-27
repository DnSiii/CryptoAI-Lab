#!/usr/bin/env python3
"""Phase165 preregistered TRAIN-only Binance open-interest integrity audit. No PnL."""
from __future__ import annotations
import hashlib,io,json,time,zipfile
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[1]
OUT=P/'reports'/'candidate_v99_r106_phase165_open_interest_data_audit.json'
PRE=P/'research'/'v99_r106_phase165_open_interest_data_prereg.md'
START=pd.Timestamp('2021-12-01',tz='UTC'); END=pd.Timestamp('2024-01-18',tz='UTC')
A=int(START.timestamp()*1000); B=int(END.timestamp()*1000)
SYMS=['BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','DOGEUSDT']
BASE='https://data.binance.vision/data/futures/um/daily/metrics'

def get(url,allow404=False):
 last=None
 for k in range(5):
  try:
   with urlopen(Request(url,headers={'User-Agent':'CryptoAI-Lab-Phase165/2.0'}),timeout=90) as r:return r.read()
  except HTTPError as e:
   if allow404 and e.code==404:return None
   last=e
  except (URLError,TimeoutError,ConnectionError) as e:last=e
  time.sleep(2**k)
 raise RuntimeError(f'{url}: {last!r}')

def days(): return pd.date_range(START,END-pd.Timedelta(days=1),freq='D')

def load(s):
 rows={}; missing=[]; schemas=[]; checksum_verified=0; archives=0
 for d in days():
  ds=d.date().isoformat(); stem=f'{s}-metrics-{ds}.zip'; url=f'{BASE}/{s}/{stem}'
  raw=get(url,allow404=True)
  if raw is None: missing.append(ds); continue
  chk=get(url+'.CHECKSUM')
  want=chk.decode().split()[0].strip().lower(); got=hashlib.sha256(raw).hexdigest()
  if got!=want: raise RuntimeError(f'{s} {ds}: checksum mismatch')
  checksum_verified+=1; archives+=1
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   if z.testzip() is not None: raise RuntimeError(f'{s} {ds}: zip CRC failure')
   names=[n for n in z.namelist() if n.lower().endswith('.csv')]
   if len(names)!=1: raise RuntimeError(f'{s} {ds}: csv count {names}')
   frame=pd.read_csv(z.open(names[0])); schemas.append(list(map(str,frame.columns)))
  c={str(x).strip().lower():x for x in frame.columns}
  tc=next((c[x] for x in ('create_time','createtime','timestamp','time') if x in c),None)
  oc=next((c[x] for x in ('sum_open_interest_value','sum_open_interest','sumopeninterest','open_interest','openinterest') if x in c),None)
  if tc is None or oc is None: raise RuntimeError(f'{s} {ds}: schema {list(frame.columns)}')
  tt=pd.to_datetime(frame[tc],utc=True,errors='coerce') if not pd.api.types.is_numeric_dtype(frame[tc]) else pd.to_datetime(pd.to_numeric(frame[tc],errors='coerce'),unit='ms',utc=True,errors='coerce')
  oo=pd.to_numeric(frame[oc],errors='coerce')
  for t,o in zip(tt,oo):
   if pd.isna(t) or pd.isna(o): continue
   ms=int(t.timestamp()*1000)
   if A<=ms<B: rows[ms]=float(o)
 return pd.Series(rows,dtype=float).sort_index(),missing,schemas[-1] if schemas else [],checksum_verified,archives

def main():
 q=PRE.read_text(); assert 'BEFORE ANY Phase165 PnL' in q and 'DATA ONLY' in q and '>=90%' in q and '>=85%' in q
 series={}; assets={}; ok=True; cadence_ms=None
 for s in SYMS:
  x,miss,schema,checks,archives=load(s); idx=np.asarray(x.index,dtype=np.int64); dif=np.diff(idx); native=int(np.median(dif)) if len(dif) else 0
  if cadence_ms is None and native>0: cadence_ms=native
  expected=max(1,int((B-A)//native)) if native>0 else 1
  vals=x.to_numpy(); st={'rows':len(x),'native_cadence_ms':native,'coverage_native':len(x)/expected,'first_ms':int(idx[0]) if len(idx) else None,'last_ms':int(idx[-1]) if len(idx) else None,'duplicate_timestamps':int(len(idx)-len(set(idx.tolist()))),'strictly_increasing':bool(len(idx)<2 or np.all(dif>0)),'invalid_nonpositive_oi':int((~np.isfinite(vals)|(vals<=0)).sum()),'missing_archives':miss,'archives_loaded':archives,'checksum_verified_archives':checks,'schema':schema}
  st['pass']=bool(st['coverage_native']>=.90 and st['strictly_increasing'] and st['duplicate_timestamps']==0 and st['invalid_nonpositive_oi']==0 and checks==archives); ok &= st['pass']; assets[s]=st; series[s]=x
 if cadence_ms and all(len(x) for x in series.values()):
  grid=np.arange(A,B,cadence_ms,dtype=np.int64); good=0
  sets={s:set(np.asarray(x.index,dtype=np.int64).tolist()) for s,x in series.items()}
  for t in grid: good += sum(t in sets[s] for s in SYMS)>=4
  cross=good/max(1,len(grid))
 else: cross=0.0
 ok &= cross>=.85
 out={'study':'V99 R106 Phase165 open-interest DATA-only audit','status':'PASS_DATA_ONLY' if ok else 'FAIL_DATA_ONLY','source':'Binance Vision USD-M daily metrics archives with SHA256 CHECKSUM','train_start':str(START),'train_end_exclusive':str(END),'assets':assets,'declared_native_cadence_ms':cadence_ms,'cross_section_coverage_ge4':cross,'pnl_computed':False,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'decision':'Eligible only for separately preregistered OI alpha hypothesis.' if ok else 'Reject before alpha; frozen OI data gates failed.'}
 OUT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
