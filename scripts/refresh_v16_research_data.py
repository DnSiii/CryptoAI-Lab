"""Append CLOSED Binance REST data to an isolated research-only dataset.

Never calls a paper synchronizer. Never rewrites the protected source. Requires
overlap agreement, complete hourly prices and bounded funding-event gaps.
REST candles remain provisional versus later checksum-verified daily archives.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse
import hashlib
import json
import shutil
import urllib.parse
import urllib.request
import pandas as pd
import numpy as np


def fetch(endpoint,parameters):
    url='https://fapi.binance.com/fapi/v1/'+endpoint+'?'+urllib.parse.urlencode(parameters)
    with urllib.request.urlopen(url,timeout=30) as response:
        payload=response.read()
    data=json.loads(payload)
    if not isinstance(data,list): raise ValueError(f'{endpoint}: invalid API response')
    return data,{'url':url,'response_sha256':hashlib.sha256(payload).hexdigest()}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--output-root',type=Path,required=True)
    p.add_argument('--end',default='2026-09-05')
    a=p.parse_args(); out=a.output_root.resolve(); source=a.source_root.resolve()
    if out==source or out.is_relative_to(source): raise ValueError('protected input')
    if out.exists(): raise ValueError('use a new dataset path; no evidence overwrite')
    end=pd.Timestamp(a.end,tz='UTC')+pd.Timedelta(hours=23)
    if end+pd.Timedelta(hours=1)>pd.Timestamp.now(tz='UTC'): raise ValueError('unclosed hour')
    (out/'config').mkdir(parents=True); (out/'data/canonical').mkdir(parents=True)
    config=source/'config/research_pit48.json'
    shutil.copy2(config,out/'config/research_pit48.json')
    symbols=json.loads(config.read_text())['symbols']
    def process(symbol):
        cp=source/f'data/canonical/{symbol}_1h.csv'; fp=source/f'data/canonical/{symbol}_funding.csv'
        prices=pd.read_csv(cp); funding=pd.read_csv(fp)
        before={cp.name:hashlib.sha256(cp.read_bytes()).hexdigest(),fp.name:hashlib.sha256(fp.read_bytes()).hexdigest()}
        dates=pd.to_datetime(prices.timestamp,utc=True)
        cutoff=pd.Timestamp('2026-08-31T23:00Z')
        if len(dates)==0 or dates.max()<cutoff:
            shutil.copy2(cp,out/'data/canonical'/cp.name); shutil.copy2(fp,out/'data/canonical'/fp.name)
            return symbol,{'status':'historically_retained_inactive','original_sha256':before}
        # Read one overlap day regardless of how far this symbol was previously synced.
        start=pd.Timestamp('2026-08-31T00:00Z')
        params={'symbol':symbol,'startTime':int(start.timestamp()*1000),
                'endTime':int((end+pd.Timedelta(hours=1)).timestamp()*1000)-1,'limit':1000}
        rows,pr=fetch('klines',{**params,'interval':'1h'})
        if not rows: raise ValueError(f'{symbol}: empty current price range')
        names=['open_time','open','high','low','close','volume','close_time','quote_volume','trades','tb','tq','ignore']
        new=pd.DataFrame(rows,columns=names)
        new['timestamp']=pd.to_datetime(new.open_time,unit='ms',utc=True)
        if (new.close_time>=int((end+pd.Timedelta(hours=1)).timestamp()*1000)).any():
            raise ValueError(f'{symbol}: partial/future candle')
        new=new[list(prices.columns)]
        numeric=[c for c in prices if c!='timestamp']
        new[numeric]=new[numeric].apply(pd.to_numeric,errors='raise')
        if new.timestamp.duplicated().any(): raise ValueError(f'{symbol}: duplicate candle')
        expected=pd.date_range(start,end,freq='h')
        if not pd.DatetimeIndex(new.timestamp).equals(expected): raise ValueError(f'{symbol}: incomplete hourly response')
        old=prices.copy(); old.timestamp=dates
        overlap=old.set_index('timestamp').join(new.set_index('timestamp'),lsuffix='_old',rsuffix='_new',how='inner')
        if len(overlap)<24: raise ValueError(f'{symbol}: missing overlap')
        for col in numeric:
            if not np.allclose(overlap[col+'_old'],overlap[col+'_new'],rtol=1e-9,atol=1e-8):
                raise ValueError(f'{symbol}: stored/API {col} disagreement')
        merged=pd.concat([old,new.loc[new.timestamp>dates.max()]],ignore_index=True)
        merged.to_csv(out/'data/canonical'/cp.name,index=False)
        events,fr=fetch('fundingRate',params)
        f=pd.DataFrame(events)
        if f.empty: raise ValueError(f'{symbol}: no funding records')
        f['timestamp']=pd.to_datetime(f.fundingTime,unit='ms',utc=True).dt.floor('h')
        f=f.sort_values('timestamp')
        if f.timestamp.duplicated().any(): raise ValueError(f'{symbol}: duplicated funding event')
        gaps=f.timestamp.diff().dropna()
        if gaps.max()>pd.Timedelta(hours=8) or f.timestamp.iloc[0]>start+pd.Timedelta(hours=8) or f.timestamp.iloc[-1]<end-pd.Timedelta(hours=8):
            raise ValueError(f'{symbol}: unverified funding gap')
        f['funding_rate']=pd.to_numeric(f.fundingRate,errors='raise')
        # Interval metadata inferred from actually observed event spacing.
        f['funding_interval_hours']=f.timestamp.diff().dt.total_seconds()/3600
        f.loc[f.index[0],'funding_interval_hours']=float(f.funding_interval_hours.dropna().iloc[0])
        f=f[list(funding.columns)]
        oldf=funding.copy(); oldf.timestamp=pd.to_datetime(oldf.timestamp,utc=True,format='mixed')
        shared=oldf.set_index('timestamp').join(f.set_index('timestamp'),lsuffix='_old',rsuffix='_new',how='inner')
        if len(shared)==0 or not np.allclose(shared.funding_rate_old,shared.funding_rate_new,atol=1e-12,rtol=0):
            raise ValueError(f'{symbol}: funding overlap missing/disagrees')
        mergedf=pd.concat([oldf,f.loc[f.timestamp>oldf.timestamp.max()]],ignore_index=True)
        mergedf.to_csv(out/'data/canonical'/fp.name,index=False)
        if before!={cp.name:hashlib.sha256(cp.read_bytes()).hexdigest(),fp.name:hashlib.sha256(fp.read_bytes()).hexdigest()}:
            raise RuntimeError('protected original source changed')
        return symbol,{'status':'closed_rest_verified_overlap','end':end.isoformat(),
            'overlap_hours':len(overlap),'appended_price_hours':len(merged)-len(old),
            'appended_funding_events':len(mergedf)-len(oldf),'original_sha256':before,'price_request':pr,'funding_request':fr,
            'output_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'data/canonical'/cp.name,out/'data/canonical'/fp.name)}}
    results={}; failures={}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(process,s):s for s in symbols}
        for future in as_completed(futures):
            symbol=futures[future]
            try:
                symbol,info=future.result(); results[symbol]=info
                print(symbol,info['status'],flush=True)
            except Exception as exc:
                failures[symbol]=f'{type(exc).__name__}: {exc}'; print(symbol,failures[symbol],flush=True)
    manifest={'retrieved_at':pd.Timestamp.now(tz='UTC').isoformat(),'end':end.isoformat(),
        'status':'COMPLETE' if not failures else 'INCOMPLETE_DO_NOT_BACKTEST',
        'validation':'closed REST plus stored overlap; latest REST is not yet daily-archive reconciled',
        'symbols':results,'failures':failures}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if failures: raise SystemExit('Incomplete dataset; failures recorded, no backtest authorized by this artifact.')


if __name__=='__main__': main()
