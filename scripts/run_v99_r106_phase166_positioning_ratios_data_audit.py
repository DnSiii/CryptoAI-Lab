#!/usr/bin/env python3
"""Phase166 preregistered TRAIN-only positioning-ratios integrity audit. No PnL."""
from __future__ import annotations
import hashlib,io,json,time,zipfile
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[1]
OUT=P/'reports'/'candidate_v99_r106_phase166_positioning_ratios_data_audit.json'
PRE=P/'research'/'v99_r106_phase166_positioning_ratios_data_prereg.md'
START=pd.Timestamp('2021-12-01',tz='UTC'); END=pd.Timestamp('2024-01-18',tz='UTC')
A=int(START.timestamp()*1000); B=int(END.timestamp()*1000)
SYMS=['BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','DOGEUSDT']
FIELDS=['count_toptrader_long_short_ratio','sum_toptrader_long_short_ratio','count_long_short_ratio','sum_taker_long_short_vol_ratio']
BASE='https://data.binance.vision/data/futures/um/daily/metrics'
def get(url,allow404=False):
 last=None
 for k in range(5):
  try:
   with urlopen(Request(url,headers={'User-Agent':'CryptoAI-Lab-Phase166/1.0'}),timeout=90) as r:return r.read()
  except HTTPError as e:
   if allow404 and e.code==404:return None
   last=e
  except (URLError,TimeoutError,ConnectionError) as e:last=e
  time.sleep(2**k)
 raise RuntimeError(f'{url}: {last!r}')
def days(): return pd.date_range(START,END-pd.Timedelta(days=1),freq='D')
def load(s):
 rows={f:{} for f in FIELDS}; missing=[]; checks=archives=0; schema=[]
 for d in days():
  ds=d.date().isoformat(); stem=f'{s}-metrics-{ds}.zip'; url=f'{BASE}/{s}/{stem}'; raw=get(url,True)
  if raw is None: missing.append(ds); continue
  want=get(url+'.CHECKSUM').decode().split()[0].lower(); got=hashlib.sha256(raw).hexdigest()
  if got!=want: raise RuntimeError(f'{s} {ds}: checksum mismatch')
  checks+=1; archives+=1
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   if z.testzip() is not None: raise RuntimeError(f'{s} {ds}: zip CRC failure')
   names=[n for n in z.namelist() if n.lower().endswith('.csv')]
   if len(names)!=1: raise RuntimeError(f'{s} {ds}: csv count {names}')
   frame=pd.read_csv(z.open(names[0])); schema=list(map(str,frame.columns))
  c={str(x).strip().lower():x for x in frame.columns}; tc=c.get('create_time')
  if tc is None or any(f not in c for f in FIELDS): raise RuntimeError(f'{s} {ds}: schema {schema}')
  tt=pd.to_datetime(frame[tc],utc=True,errors='coerce')
  for f in FIELDS:
   vv=pd.to_numeric(frame[c[f]],errors='coerce')
   for t,v in zip(tt,vv):
    if pd.isna(t): continue
    ms=int(t.timestamp()*1000)
    if A<=ms<B: rows[f][ms]=float(v) if not pd.isna(v) else np.nan
 return {f:pd.Series(rows[f],dtype=float).sort_index() for f in FIELDS},missing,schema,checks,archives
def main():
 q=PRE.read_text(); assert 'BEFORE ANY Phase166 PnL' in q and 'DATA ONLY' in q
 assets={}; series={}; ok=True; cadence=None
 for s in SYMS:
  ff,miss,schema,checks,archives=load(s); assets[s]={'missing_archives':miss,'archives_loaded':archives,'checksum_verified_archives':checks,'schema':schema,'fields':{}}; series[s]=ff
  for f,x in ff.items():
   idx=np.asarray(x.index,dtype=np.int64); dif=np.diff(idx); native=int(np.median(dif)) if len(dif) else 0
   if cadence is None and native>0: cadence=native
   expected=max(1,int((B-A)//native)) if native else 1; vals=x.to_numpy()
   st={'rows':len(x),'native_cadence_ms':native,'coverage_native':len(x)/expected,'duplicate_timestamps':int(len(idx)-len(set(idx.tolist()))),'strictly_increasing':bool(len(idx)<2 or np.all(dif>0)),'nonfinite':int((~np.isfinite(vals)).sum()),'nonpositive':int((np.isfinite(vals)&(vals<=0)).sum())}
   st['pass']=bool(st['coverage_native']>=.90 and st['duplicate_timestamps']==0 and st['strictly_increasing'] and st['nonfinite']==0 and st['nonpositive']==0 and checks==archives)
   assets[s]['fields'][f]=st; ok &= st['pass']
 if cadence:
  grid=np.arange(A,B,cadence,dtype=np.int64); good=0; sets={s:set(series[s][FIELDS[0]].index) for s in SYMS}
  for t in grid: good += sum(t in sets[s] for s in SYMS)>=4
  cross=good/max(1,len(grid))
 else: cross=0.0
 ok &= cross>=.85
 out={'study':'V99 R106 Phase166 positioning-ratios DATA-only audit','status':'PASS_DATA_ONLY' if ok else 'FAIL_DATA_ONLY','source':'Binance Vision USD-M daily metrics + SHA256 CHECKSUM','train_start':str(START),'train_end_exclusive':str(END),'fixed_fields':FIELDS,'assets':assets,'declared_native_cadence_ms':cadence,'cross_section_coverage_ge4':cross,'pnl_computed':False,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'decision':'Eligible only for separately preregistered positioning alpha hypothesis.' if ok else 'Reject before alpha; frozen positioning DATA gates failed.'}
 OUT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
