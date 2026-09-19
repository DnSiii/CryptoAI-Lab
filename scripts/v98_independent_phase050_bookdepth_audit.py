from __future__ import annotations
import hashlib, io, json, urllib.request, zipfile
from pathlib import Path
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'v98_independent_phase050_bookdepth_audit.json'
SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BNBUSDT')
DATES=('2023-01-15','2023-04-15','2023-07-15','2023-10-15','2024-01-15','2024-04-15','2024-07-15','2024-10-15','2025-01-15','2025-04-15','2025-07-15','2025-10-15')
BASE='https://data.binance.vision/data/futures/um/daily/bookDepth/{symbol}/{symbol}-bookDepth-{date}.zip'
EXPECTED=('timestamp','percentage','depth','notional')

def audit(symbol,date):
    url=BASE.format(symbol=symbol,date=date)
    try:
        with urllib.request.urlopen(url,timeout=30) as r: payload=r.read()
        digest=hashlib.sha256(payload).hexdigest()
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            names=[n for n in z.namelist() if n.lower().endswith('.csv')]
            if len(names)!=1: return {'ok':False,'error':f'csv_members:{len(names)}','sha256':digest}
            with z.open(names[0]) as f: df=pd.read_csv(f)
        cols=tuple(map(str,df.columns)); ts=pd.to_datetime(df['timestamp'],utc=True,errors='coerce') if 'timestamp' in df else pd.Series(dtype='datetime64[ns, UTC]')
        pct=pd.to_numeric(df.get('percentage'),errors='coerce'); depth=pd.to_numeric(df.get('depth'),errors='coerce'); notion=pd.to_numeric(df.get('notional'),errors='coerce')
        unique_ts=int(ts.nunique()); levels=sorted(pd.Series(pct.dropna().unique()).astype(float).tolist())
        bad_ts=int(ts.isna().sum()); bad_num=int((pct.isna()|depth.isna()|notion.isna()).sum()); nonpositive=int(((depth<=0)|(notion<=0)).sum())
        duplicated=int(df.duplicated(subset=['timestamp','percentage']).sum()) if set(('timestamp','percentage')).issubset(df.columns) else -1
        expected_rows=unique_ts*len(levels); complete_grid=(len(df)==expected_rows and duplicated==0)
        date_ok=bool(len(ts.dropna()) and (ts.dropna().dt.strftime('%Y-%m-%d')==date).all())
        signs=bool(any(x<0 for x in levels) and any(x>0 for x in levels))
        ok=cols==EXPECTED and bad_ts==0 and bad_num==0 and nonpositive==0 and duplicated==0 and complete_grid and date_ok and signs
        return {'ok':ok,'url':url,'bytes':len(payload),'sha256':digest,'rows':int(len(df)),'unique_timestamps':unique_ts,'levels':levels,'columns':list(cols),'bad_timestamps':bad_ts,'bad_numeric_rows':bad_num,'nonpositive_rows':nonpositive,'duplicate_timestamp_level':duplicated,'complete_timestamp_level_grid':complete_grid,'date_membership_ok':date_ok,'both_book_sides_present':signs,'first_timestamp':str(ts.min()),'last_timestamp':str(ts.max())}
    except Exception as e: return {'ok':False,'url':url,'error':f'{type(e).__name__}:{e}'}

def main():
    checks={f'{s}:{d}':audit(s,d) for s in SYMBOLS for d in DATES}
    passed=sum(int(v.get('ok',False)) for v in checks.values())
    schemas={tuple(v.get('columns',[])) for v in checks.values() if 'columns' in v}
    report={'engine':'V98 Independent','phase':'050','purpose':'book-depth historical integrity/coverage gate only; NO alpha scoring; NO validation; NO final holdout','symbols':list(SYMBOLS),'dates':list(DATES),'checks':checks,'summary':{'passed':passed,'total':len(checks),'all_pass':passed==len(checks),'schema_count':len(schemas),'schemas':[list(x) for x in sorted(schemas)]},'decision':'integrity_gate_pass' if passed==len(checks) and len(schemas)==1 else 'integrity_gate_fail_or_requires_review'}
    OUT.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2)); print(report['decision'])
if __name__=='__main__': main()
