from __future__ import annotations
import hashlib,io,json,urllib.request,zipfile
from pathlib import Path
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'v98_independent_phase047_oi_acquisition_audit.json'
SYMBOLS=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','ADAUSDT','LINKUSDT','LTCUSDT','DOGEUSDT','SOLUSDT','AVAXUSDT')
# Integrity-only sample across training-era years. No return/alpha evaluation here.
DATES=('2023-01-15','2023-07-15','2024-01-15','2024-07-15','2025-01-15','2025-07-15','2026-01-15','2026-07-15')
BASE='https://data.binance.vision/data/futures/um/daily/metrics/{symbol}/{symbol}-metrics-{date}.zip'

def canonical_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Map source observations to the frozen 1h information grid.

    Source row order is not treated as information. Rows are deterministically sorted
    by their own exchange timestamp, then the last strictly valid positive OI observed
    inside each UTC hour is selected. No interpolation, backfill, price data, future
    observation, or alpha-dependent choice is allowed.
    """
    x=pd.DataFrame({'timestamp':pd.to_datetime(df['create_time'],utc=True,errors='coerce'),'oi':pd.to_numeric(df['sum_open_interest'],errors='coerce')})
    x=x[x['timestamp'].notna() & x['oi'].notna() & (x['oi']>0)].copy().sort_values('timestamp',kind='stable')
    x['hour']=x['timestamp'].dt.floor('h')
    return x.groupby('hour',sort=True,as_index=False).tail(1).reset_index(drop=True)

def one(symbol,date):
    url=BASE.format(symbol=symbol,date=date)
    try:
        with urllib.request.urlopen(url,timeout=30) as r: payload=r.read()
        digest=hashlib.sha256(payload).hexdigest()
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            names=[n for n in z.namelist() if n.lower().endswith('.csv')]
            if len(names)!=1: raise RuntimeError(f'csv_members={names}')
            with z.open(names[0]) as f: df=pd.read_csv(f)
        if 'create_time' not in df or 'sum_open_interest' not in df: raise RuntimeError(f'required columns absent: {list(df.columns)}')
        ts=pd.to_datetime(df['create_time'],utc=True,errors='coerce'); oi=pd.to_numeric(df['sum_open_interest'],errors='coerce')
        dup=int(ts.duplicated().sum()); invalid_ts=int(ts.isna().sum()); invalid_oi=int((~oi.notna() | (oi<=0)).sum()); raw_monotonic=bool(ts.dropna().is_monotonic_increasing)
        unique=ts.dropna().sort_values().unique(); cadence_seconds=sorted(set(int(x.total_seconds()) for x in pd.Series(unique[1:]-unique[:-1]))) if len(unique)>1 else []
        hourly=canonical_hourly(df); expected=pd.date_range(pd.Timestamp(date,tz='UTC'),periods=24,freq='h'); got=pd.DatetimeIndex(hourly['hour']); missing=[str(x) for x in expected.difference(got)]; future_cross_hour=int((hourly['timestamp']>=hourly['hour']+pd.Timedelta(hours=1)).sum()); hourly_ok=len(hourly)==24 and not missing and future_cross_hour==0
        return {'ok':dup==0 and invalid_ts==0 and hourly_ok,'url':url,'archive_sha256':digest,'rows':int(len(df)),'first_timestamp':str(ts.min()),'last_timestamp':str(ts.max()),'duplicate_timestamps':dup,'invalid_timestamps':invalid_ts,'raw_invalid_or_nonpositive_oi':invalid_oi,'raw_row_order_monotonic':raw_monotonic,'raw_rows_sorted_by_exchange_timestamp_before_canonicalization':True,'cadence_seconds':cadence_seconds,'columns':list(map(str,df.columns)),'canonicalization':'stable timestamp sort, then last valid positive OI observed within each UTC hour; no interpolation/backfill','canonical_hourly_rows':int(len(hourly)),'canonical_missing_hours':missing,'canonical_future_cross_hour_violations':future_cross_hour,'raw_anomalies_tolerated_only_if_hour_has_prior_valid_observation':True}
    except Exception as e: return {'ok':False,'url':url,'error':f'{type(e).__name__}: {e}'}

def main():
    checks={f'{s}:{d}':one(s,d) for s in SYMBOLS for d in DATES}; ok=sum(bool(v.get('ok')) for v in checks.values()); schemas=sorted({tuple(v.get('columns',[])) for v in checks.values() if 'columns' in v}); raw_anomaly_files=sum(int(v.get('raw_invalid_or_nonpositive_oi',0)>0) for v in checks.values()); raw_nonmonotonic_files=sum(int(v.get('raw_row_order_monotonic') is False) for v in checks.values())
    report={'engine':'V98 Independent','phase':'047','purpose':'OI acquisition/integrity audit only; no alpha returns, validation, or final holdout access','source':'Binance public USD-M daily metrics archive','symbols':SYMBOLS,'dates':DATES,'canonical_grid':'1h UTC, stable timestamp sort then last valid positive observation within each hour','checks':checks,'ok_count':ok,'total_count':len(checks),'schema_count':len(schemas),'raw_anomaly_files':raw_anomaly_files,'raw_nonmonotonic_files':raw_nonmonotonic_files,'column_sets':[list(x) for x in schemas],'decision':'integrity_sample_pass' if ok==len(checks) and len(schemas)==1 else 'block_phase047_backtest'}
    OUT.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({k:report[k] for k in ('ok_count','total_count','schema_count','raw_anomaly_files','raw_nonmonotonic_files','decision')},indent=2))
if __name__=='__main__': main()
