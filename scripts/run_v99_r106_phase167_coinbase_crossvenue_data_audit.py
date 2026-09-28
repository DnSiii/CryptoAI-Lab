#!/usr/bin/env python3
"""Phase167 preregistered TRAIN-only Coinbase cross-venue integrity audit. No PnL."""
from __future__ import annotations
import json,time
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[1]
OUT=P/'reports'/'candidate_v99_r106_phase167_coinbase_crossvenue_data_audit.json'
PRE=P/'research'/'v99_r106_phase167_coinbase_crossvenue_data_prereg.md'
START=pd.Timestamp('2021-12-01T00:00:00Z'); END=pd.Timestamp('2024-01-18T00:00:00Z')
PRODUCTS=['BTC-USD','ETH-USD','SOL-USD','XRP-USD','DOGE-USD']; GRAN=3600; STEP=pd.Timedelta(hours=300)
BASE='https://api.exchange.coinbase.com'
def get_json(url):
 last=None
 for k in range(6):
  try:
   with urlopen(Request(url,headers={'User-Agent':'CryptoAI-Lab-Phase167/1.0','Accept':'application/json'}),timeout=60) as r:
    return json.loads(r.read().decode())
  except HTTPError as e:
   last=e
   if e.code in (429,500,502,503,504): time.sleep(min(30,2**k)); continue
   raise
  except (URLError,TimeoutError,ConnectionError) as e: last=e; time.sleep(min(30,2**k))
 raise RuntimeError(f'{url}: {last!r}')
def load(product):
 rows={}; requests=0; cursor=START
 while cursor<END:
  stop=min(END,cursor+STEP)
  q=urlencode({'start':cursor.isoformat().replace('+00:00','Z'),'end':stop.isoformat().replace('+00:00','Z'),'granularity':GRAN})
  data=get_json(f'{BASE}/products/{product}/candles?{q}'); requests+=1
  if not isinstance(data,list): raise RuntimeError(f'{product}: non-list response {data!r}')
  for row in data:
   if not isinstance(row,list) or len(row)<6: continue
   ts=int(row[0]); t=pd.Timestamp(ts,unit='s',tz='UTC')
   if START<=t<END: rows[ts]=[float(x) for x in row[1:6]] # low high open close volume
  cursor=stop; time.sleep(.12)
 idx=sorted(rows); arr=np.asarray([rows[t] for t in idx],dtype=float) if idx else np.empty((0,5))
 return idx,arr,requests
def main():
 q=PRE.read_text(); assert 'DATA ONLY. BEFORE ANY Phase167 PnL.' in q
 expected=pd.date_range(START,END-pd.Timedelta(hours=1),freq='h'); expected_s=set((expected.view('int64')//10**9).tolist())
 assets={}; sets={}; ok=True
 for product in PRODUCTS:
  idx,a,nreq=load(product); s=set(idx); sets[product]=s
  finite=bool(np.isfinite(a).all()) if len(a) else False
  price_bad=int((~np.isfinite(a[:,:4]) | (a[:,:4]<=0)).sum()) if len(a) else 0
  vol_bad=int((~np.isfinite(a[:,4]) | (a[:,4]<0)).sum()) if len(a) else 0
  offgrid=sum((t%GRAN)!=0 for t in idx); outside=sum(t not in expected_s for t in idx)
  dif=np.diff(np.asarray(idx,dtype=np.int64))
  st={'rows':len(idx),'requests':nreq,'coverage_hourly':len(s&expected_s)/len(expected_s),'duplicate_timestamps_after_canonicalization':len(idx)-len(s),'strictly_increasing':bool(len(idx)<2 or np.all(dif>0)),'off_hour_grid':offgrid,'rows_outside_train':outside,'all_finite':finite,'invalid_ohlc_cells':price_bad,'invalid_volume_cells':vol_bad}
  st['pass']=bool(st['coverage_hourly']>=.95 and st['duplicate_timestamps_after_canonicalization']==0 and st['strictly_increasing'] and offgrid==0 and outside==0 and finite and price_bad==0 and vol_bad==0)
  assets[product]=st; ok &= st['pass']
 good=sum(sum(t in sets[p] for p in PRODUCTS)>=4 for t in expected_s); cross=good/len(expected_s); ok &= cross>=.90
 out={'study':'V99 R106 Phase167 Coinbase cross-venue spot DATA-only audit','status':'PASS_DATA_ONLY' if ok else 'FAIL_DATA_ONLY','source':'Coinbase Exchange public hourly candles','train_start':str(START),'train_end_exclusive':str(END),'fixed_products':PRODUCTS,'assets':assets,'cross_section_coverage_ge4':cross,'pnl_computed':False,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'decision':'Eligible only for separately preregistered Phase168 cross-venue hypothesis.' if ok else 'Reject this frozen Coinbase source contract before alpha; no gate rescue.'}
 OUT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
