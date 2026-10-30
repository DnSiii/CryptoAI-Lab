from __future__ import annotations
import hashlib,io,json,urllib.request,zipfile
from pathlib import Path
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1]; OUT=PROJECT/'reports'/'v98_independent_phase050_bookdepth_probe.json'
SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BNBUSDT'); DATES=('2023-01-15','2024-01-15','2025-01-15')
BASE='https://data.binance.vision/data/futures/um/daily/bookDepth/{symbol}/{symbol}-bookDepth-{date}.zip'

def probe(symbol,date):
 url=BASE.format(symbol=symbol,date=date)
 try:
  with urllib.request.urlopen(url,timeout=25) as r: payload=r.read()
  digest=hashlib.sha256(payload).hexdigest()
  with zipfile.ZipFile(io.BytesIO(payload)) as z:
   names=[n for n in z.namelist() if n.lower().endswith('.csv')]
   if len(names)!=1:return {'ok':False,'url':url,'error':f'csv_members:{len(names)}','sha256':digest}
   with z.open(names[0]) as f: df=pd.read_csv(f)
  sample=df.head(3).astype(str).to_dict('records'); return {'ok':True,'url':url,'bytes':len(payload),'sha256':digest,'rows':int(len(df)),'columns':list(map(str,df.columns)),'sample':sample}
 except Exception as e:return {'ok':False,'url':url,'error':f'{type(e).__name__}:{e}'}

def main():
 checks={f'{s}:{d}':probe(s,d) for s in SYMBOLS for d in DATES}; oks=sum(int(v['ok']) for v in checks.values()); schemas={tuple(v.get('columns',[])) for v in checks.values() if v['ok']}; report={'engine':'V98 Independent','purpose':'orthogonal book-depth source feasibility/integrity probe only; NO alpha scoring, NO validation access, NO final-holdout access','source':'Binance public USD-M daily bookDepth archive','symbols':list(SYMBOLS),'dates':list(DATES),'checks':checks,'summary':{'passed':oks,'total':len(checks),'schema_count':len(schemas),'all_pass':oks==len(checks),'schemas':[list(x) for x in sorted(schemas)]},'decision':'feasible_for_preregistration' if oks==len(checks) and len(schemas)==1 else 'not_yet_feasible'}; OUT.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report['summary'],indent=2)); print(report['decision'])
if __name__=='__main__':main()
