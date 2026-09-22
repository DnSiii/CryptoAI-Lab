from __future__ import annotations
# Namespaced Phase083 acquisition for the pre-registered incomplete current month.
# Price bars come from immutable Binance Vision daily archives. Binance Vision does
# not publish daily fundingRate archives, so realized funding events are fetched
# once from the official USD-M historical funding endpoint and snapshotted into
# the same CSV schema consumed by the canonical builder, with SHA256 provenance.
import csv,hashlib,io,json,urllib.error,urllib.parse,urllib.request,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
VISION='https://data.binance.vision/data/futures/um/daily'
FAPI='https://fapi.binance.com/fapi/v1/fundingRate'
SYMBOLS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT')
START=date(2026,9,1);END=date(2026,9,15)

def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-V98-independent/1'})
 try:
  with urllib.request.urlopen(req,timeout=45) as r:return r.read()
 except urllib.error.HTTPError as e:
  if e.code==404:return None
  raise

def ms(d, end=False):
 t=datetime(d.year,d.month,d.day,tzinfo=timezone.utc)
 if end:t+=timedelta(days=1,milliseconds=-1)
 return int(t.timestamp()*1000)

def snapshot_funding(sym):
 q=urllib.parse.urlencode({'symbol':sym,'startTime':ms(START),'endTime':ms(END,True),'limit':1000})
 url=FAPI+'?'+q; payload=fetch(url)
 if payload is None:raise RuntimeError(f'Phase083 funding endpoint missing: {url}')
 raw_sha=hashlib.sha256(payload).hexdigest(); records=json.loads(payload)
 if not isinstance(records,list) or not records:raise RuntimeError(f'Phase083 empty funding response for {sym}')
 lo,hi=ms(START),ms(END,True); seen=[]
 for r in records:
  ts=int(r['fundingTime']); rate=float(r['fundingRate'])
  if not lo<=ts<=hi:raise RuntimeError(f'Phase083 out-of-window funding event for {sym}: {ts}')
  if not (-0.05 < rate < 0.05):raise RuntimeError(f'Phase083 implausible funding rate for {sym}: {rate}')
  seen.append(ts)
 if seen!=sorted(set(seen)):raise RuntimeError(f'Phase083 duplicate/nonmonotone funding events for {sym}')
 buf=io.StringIO(); w=csv.writer(buf,lineterminator='\n');w.writerow(['calc_time','last_funding_rate','funding_interval_hours'])
 for r in records:w.writerow([int(r['fundingTime']),r['fundingRate'],8])
 csv_bytes=buf.getvalue().encode(); stem=f'{sym}-fundingRate-2026-09-01_2026-09-15'
 out=PROJECT/'data'/'raw'/'fundingRate'/sym;out.mkdir(parents=True,exist_ok=True)
 zip_path=out/(stem+'.zip')
 with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(stem+'.csv',csv_bytes)
 return {'kind':'fundingRate','symbol':sym,'start':START.isoformat(),'end':END.isoformat(),'events':len(records),'api_response_sha256':raw_sha,'snapshot_sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest(),'source_url':url}

def main():
 rows=[];d=START
 while d<=END:
  ds=d.isoformat()
  for sym in SYMBOLS:
   stem=f'{sym}-1h-{ds}';url=f'{VISION}/klines/{sym}/1h/{stem}.zip';payload=fetch(url)
   if payload is None:raise RuntimeError(f'Phase083 required daily holdout archive missing: {url}')
   chk=fetch(url+'.CHECKSUM')
   if chk is None:raise RuntimeError(f'Phase083 checksum missing: {url}')
   expected=chk.decode().split()[0];actual=hashlib.sha256(payload).hexdigest()
   if actual!=expected:raise RuntimeError(f'Phase083 checksum mismatch: {url}')
   with zipfile.ZipFile(io.BytesIO(payload)) as z:
    if z.testzip() is not None:raise RuntimeError(f'Phase083 CRC failure: {url}')
   out=PROJECT/'data'/'raw'/'klines'/sym;out.mkdir(parents=True,exist_ok=True)
   (out/(stem+'.zip')).write_bytes(payload);(out/(stem+'.zip.CHECKSUM')).write_bytes(chk)
   rows.append({'kind':'klines','symbol':sym,'date':ds,'sha256':actual,'bytes':len(payload),'source_url':url})
  d+=timedelta(days=1)
 for sym in SYMBOLS:rows.append(snapshot_funding(sym))
 manifest={'engine':'V98 Independent','phase':'083','price_source':VISION,'funding_source':FAPI,'start':START.isoformat(),'end':END.isoformat(),'files':rows}
 (PROJECT/'data'/'V98_INDEPENDENT_PHASE083_DAILY_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'phase':'083','price_archives':75,'funding_snapshots':5,'start':START.isoformat(),'end':END.isoformat()}))
if __name__=='__main__':main()
