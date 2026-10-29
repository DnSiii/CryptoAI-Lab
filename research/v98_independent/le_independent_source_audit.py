#!/usr/bin/env python3
"""LE independent source-count replay; no LE bundle import and no system PnL.
Requires original pinned Clean-4 artifact 12549265452 staged beside this script.
"""
from pathlib import Path
import numpy as np,pandas as pd,csv,hashlib,json
root=Path(__file__).resolve().parent
assets=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
receipt=json.loads((root/'phase803_official_training_ohlc_receipt.json').read_text())
native=json.loads((root/'phase1000_four_asset_source_policy_receipt.json').read_text())
assert receipt['decision']=='PASS_PHASE803_100_OFFICIAL_KLINE_ARCHIVES_TRAINING_ONLY'
assert native['decision'].startswith('PASS_100_MARK_100_FUNDING_')
assert hashlib.sha256((root/'phase1000_four_asset_conservative_bounds_source_only.csv').read_bytes()).hexdigest()==native['bounds_csv_sha256']
cols=[]
for a in assets:
    p=root/'phase243_clean4_canonical'/f'{a}_1h.csv'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==receipt['assets'][a]['sha256']
    d=pd.read_csv(p)
    assert len(d)==18288
    assert pd.to_datetime(d.open_time,utc=True).equals(pd.Series(pd.date_range('2022-12-01',periods=18288,freq='h',tz='UTC')))
    cols.append(d)
close=np.column_stack([d.close.to_numpy(dtype=float) for d in cols])
quotes=np.column_stack([d.quote_volume.to_numpy(dtype=float) for d in cols])
logc=np.log(close)
fund=np.zeros_like(close);event=np.zeros_like(close)
start=int(pd.Timestamp('2022-12-01',tz='UTC').value//1000000)
seen=set()
with (root/'phase1000_four_asset_conservative_bounds_source_only.csv').open() as f:
 for row in csv.DictReader(f):
    j=assets.index(row['asset']);t=(int(row['funding_slot_ms'])-start)//3600000
    assert t%8==0 and 0<=t<18288 and (t,j) not in seen
    seen.add((t,j));fund[t,j]=float(row['funding_rate']);event[t,j]=1
assert len(seen)==9144
counts={'2023':{'Opportunity':0,'Relative_Value':0,'Stress_Recovery':0},'2024':{'Opportunity':0,'Relative_Value':0,'Stress_Recovery':0}}
expiry=[-1,-1,-1]
for t in range(744,18288):
    good=bool(np.all(quotes[t-23:t+1]>0) and np.all(quotes[t-167:t+1]>0) and np.all(quotes[t-63:t+1]>0) and all(np.all(quotes[t-k]>0) for k in (6,24,72,168,504)))
    year='2023' if t<9504 else '2024'
    ret168=logc[t]-logc[t-168];ret72=logc[t]-logc[t-72]
    ret24=logc[t]-logc[t-24];ret6=logc[t]-logc[t-6]
    med=float(np.median(ret168))
    stress=int((ret72<-.03).sum())>=3 and med<0
    expired=[x>=0 and t>=x for x in expiry]
    for k in range(3):
        if expired[k]:expiry[k]=-1
    if good and (t-744)%72==0 and med>0 and expiry[0]<0 and not expired[0]:
        ids=np.arange(t//8-5,t//8+1)*8
        if len(ids)==6 and np.all(event[ids]>0):
            mean=fund[ids].mean(axis=0)
            if np.any((mean<-.00003)&(ret24>0)&(ret6>0)):
                counts[year]['Opportunity']+=1;expiry[0]=t+72
    if good and (t-744)%168==0 and expiry[1]<0 and not expired[1]:
        if np.max(ret168)>0 and np.min(ret168)<0 and np.ptp(ret168)>.12:
            counts[year]['Relative_Value']+=1;expiry[1]=t+168
    if good and (t-744)%72==0 and stress and expiry[2]<0 and not expired[2]:
        counts[year]['Stress_Recovery']+=1;expiry[2]=t+72
result={'architecture':'LE','source':'pinned Clean4 2022-2024 only','native_events':len(seen),'hours':len(close),'counts':counts,'method':'independent scalar/event counter, no LE import','decision':'PASS_SOURCE_ONLY' if all(v>=8 for x in counts.values() for v in x.values()) else 'REJECT_SOURCE_ONLY_NO_PNL','pnl_computed':False,'validation_2025_read':False}
print(json.dumps(result,sort_keys=True))
