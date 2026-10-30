#!/usr/bin/env python3
"""LF independent scalar source-count replay; no LF source import or PnL.
Stage pinned original artifact 12549265452 under this directory.
"""
from pathlib import Path
import pandas as pd,numpy as np,csv,json,hashlib
root=Path(__file__).resolve().parent
assets=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
rec=json.loads((root/'phase803_official_training_ohlc_receipt.json').read_text())
nat=json.loads((root/'phase1000_four_asset_source_policy_receipt.json').read_text())
assert rec['decision']=='PASS_PHASE803_100_OFFICIAL_KLINE_ARCHIVES_TRAINING_ONLY'
assert nat['decision'].startswith('PASS_100_MARK_100_FUNDING_')
assert hashlib.sha256((root/'phase1000_four_asset_conservative_bounds_source_only.csv').read_bytes()).hexdigest()==nat['bounds_csv_sha256']
frames=[]
for asset in assets:
 p=root/'phase243_clean4_canonical'/f'{asset}_1h.csv'
 assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['assets'][asset]['sha256']
 d=pd.read_csv(p);assert len(d)==18288
 assert pd.to_datetime(d.open_time,utc=True).equals(pd.Series(pd.date_range('2022-12-01',periods=18288,freq='h',tz='UTC')))
 frames.append(d)
cl=np.column_stack([x.close.to_numpy(float) for x in frames])
q=np.column_stack([x.quote_volume.to_numpy(float) for x in frames])
lc=np.log(cl)
seen=set();start=int(pd.Timestamp('2022-12-01',tz='UTC').value//1000000)
with (root/'phase1000_four_asset_conservative_bounds_source_only.csv').open() as f:
 for row in csv.DictReader(f):
  j=assets.index(row['asset']);t=(int(row['funding_slot_ms'])-start)//3600000
  assert 0<=t<18288 and t%8==0 and (t,j) not in seen;seen.add((t,j))
assert len(seen)==9144
counts={y:{k:0 for k in ('Opportunity','Relative_Value','Stress_Recovery')} for y in ('2023','2024')}
expiry=[-1,-1,-1]
for t in range(744,18288):
 safe=bool(np.all(q[t-23:t+1]>0) and np.all(q[t-167:t+1]>0) and np.all(q[t-63:t+1]>0) and all(np.all(q[t-k]>0) for k in (6,24,72,168,336)))
 y='2023' if t<9504 else '2024'
 a=lc[t]-lc[t-336];b=lc[t]-lc[t-168];c=lc[t]-lc[t-72];d=lc[t]-lc[t-24];f=lc[t]-lc[t-6]
 median72=float(np.median(c));risk_on=float(np.median(b))>0;stress=int((c<-.04).sum())>=2 and median72<0
 expired=[x>=0 and t>=x for x in expiry]
 for k in range(3):
  if expired[k]:expiry[k]=-1
 if safe and (t-744)%48==0 and risk_on and expiry[0]<0 and not expired[0] and np.any((a>0)&(d<0)&(f>0)):
  counts[y]['Opportunity']+=1;expiry[0]=t+48
 if safe and (t-744)%72==0 and abs(median72)<.08 and expiry[1]<0 and not expired[1] and np.ptp(d)>.05:
  counts[y]['Relative_Value']+=1;expiry[1]=t+72
 if safe and (t-744)%48==0 and stress and expiry[2]<0 and not expired[2]:
  counts[y]['Stress_Recovery']+=1;expiry[2]=t+48
result={'architecture':'LF','counts':counts,'hours':18288,'native_events':9144,'source_only':True,'independent_from_lf_source':True,'pnl_computed':False,'decision':'PASS_SOURCE_ONLY' if all(v>=8 for x in counts.values() for v in x.values()) else 'REJECT_SOURCE_ONLY_NO_PNL'}
print(json.dumps(result,sort_keys=True))
