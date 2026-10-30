from __future__ import annotations
import io,json,urllib.request,zipfile
from pathlib import Path
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'v98_independent_external_metrics_probe.json'
SYMBOLS=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','ADAUSDT','LINKUSDT','LTCUSDT','DOGEUSDT','SOLUSDT','AVAXUSDT')
DATES=('2023-01-15','2024-01-15','2025-01-15','2026-01-15')
BASE='https://data.binance.vision/data/futures/um/daily/metrics/{symbol}/{symbol}-metrics-{date}.zip'
def fetch(symbol,date):
 url=BASE.format(symbol=symbol,date=date)
 try:
  with urllib.request.urlopen(url,timeout=30) as r: payload=r.read()
  with zipfile.ZipFile(io.BytesIO(payload)) as z:
   names=[n for n in z.namelist() if n.lower().endswith('.csv')]
   if len(names)!=1: raise RuntimeError(f'csv members={names}')
   with z.open(names[0]) as f: df=pd.read_csv(f)
  return {'ok':True,'url':url,'rows':int(len(df)),'columns':list(map(str,df.columns)),'first':df.iloc[0].astype(str).to_dict() if len(df) else None}
 except Exception as e: return {'ok':False,'url':url,'error':f'{type(e).__name__}: {e}'}
def main():
 checks={f'{s}:{d}':fetch(s,d) for s in SYMBOLS for d in DATES}
 oks=[v for v in checks.values() if v['ok']]; column_sets=sorted({tuple(v['columns']) for v in oks}); required=all('sum_open_interest' in v['columns'] for v in oks)
 report={'engine':'V98 Independent','purpose':'external orthogonal data-source feasibility probe only; no alpha selection and no validation/final-holdout access','source':'Binance public USD-M daily metrics archive','symbols':SYMBOLS,'dates':DATES,'checks':checks,'ok_count':len(oks),'total_count':len(checks),'column_sets':[list(x) for x in column_sets],'required_sum_open_interest_present':required and bool(oks),'decision':'usable_for_preregistered_phase047' if len(oks)==len(checks) and len(column_sets)==1 and required else 'do_not_start_phase047'}
 OUT.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'ok_count':len(oks),'total_count':len(checks),'column_sets':report['column_sets'],'required_sum_open_interest_present':report['required_sum_open_interest_present'],'decision':report['decision']},indent=2))
if __name__=='__main__': main()
