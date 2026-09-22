from __future__ import annotations
# Namespaced Phase083 acquisition for the pre-registered incomplete current month.
import csv,hashlib,io,json,urllib.error,urllib.parse,urllib.request,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
VISION='https://data.binance.vision/data/futures/um/daily'
FAPI_HOSTS=('https://fapi.binance.com','https://fapi1.binance.com','https://fapi2.binance.com','https://fapi3.binance.com','https://fapi4.binance.com')
SYMBOLS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT');START=date(2026,9,1);END=date(2026,9,15)
def fetch(url,timeout=45):
 req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-V98-independent/1'})
 try:
  with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
 except urllib.error.HTTPError as e:
  if e.code==404:return None
  raise
def ms(d,end=False):
 t=datetime(d.year,d.month,d.day,tzinfo=timezone.utc)
 if end:t+=timedelta(days=1,milliseconds=-1)
 return int(t.timestamp()*1000)
def funding_payload(sym):
 q=urllib.parse.urlencode({'symbol':sym,'startTime':ms(START),'endTime':ms(END,True),'limit':1000});errs=[]
 for host in FAPI_HOSTS:
  url=host+'/fapi/v1/fundingRate?'+q
  try:
   p=fetch(url,12)
   if p:return url,p
  except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:errs.append(f'{host}:{type(e).__name__}:{getattr(e,"code","")}')
 raise RuntimeError('Phase083 all official USD-M funding endpoints unavailable: '+';'.join(errs))
def snapshot_funding(sym):
 url,payload=funding_payload(sym);raw_sha=hashlib.sha256(payload).hexdigest();records=json.loads(payload)
 if not isinstance(records,list) or not records:raise RuntimeError(f'Phase083 empty funding response for {sym}')
 lo,hi=ms(START),ms(END,True);seen=[]
 for r in records:
  ts=int(r['fundingTime']);rate=float(r['fundingRate'])
  if not lo<=ts<=hi:raise RuntimeError(f'Phase083 out-of-window funding event for {sym}: {ts}')
  if not (-0.05<rate<0.05):raise RuntimeError(f'Phase083 implausible funding rate for {sym}: {rate}')
  seen.append(ts)
 if seen!=sorted(set(seen)):raise RuntimeError(f'Phase083 duplicate/nonmonotone funding events for {sym}')
 buf=io.StringIO();w=csv.writer(buf,lineterminator='\n');w.writerow(['calc_time','last_funding_rate','funding_interval_hours'])
 for r in records:w.writerow([int(r['fundingTime']),r['fundingRate'],8])
 stem=f'{sym}-fundingRate-2026-09-01_2026-09-15';out=PROJECT/'data'/'raw'/'fundingRate'/sym;out.mkdir(parents=True,exist_ok=True);zp=out/(stem+'.zip')
 with zipfile.ZipFile(zp,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(stem+'.csv',buf.getvalue().encode())
 return {'kind':'fundingRate','symbol':sym,'events':len(records),'api_response_sha256':raw_sha,'snapshot_sha256':hashlib.sha256(zp.read_bytes()).hexdigest(),'source_url':url}
def main():
 rows=[];d=START
 while d<=END:
  ds=d.isoformat()
  for sym in SYMBOLS:
   stem=f'{sym}-1h-{ds}';url=f'{VISION}/klines/{sym}/1h/{stem}.zip';p=fetch(url);chk=fetch(url+'.CHECKSUM')
   if p is None or chk is None:raise RuntimeError(f'Phase083 daily price archive/checksum missing: {url}')
   expected=chk.decode().split()[0];actual=hashlib.sha256(p).hexdigest()
   if actual!=expected:raise RuntimeError(f'Phase083 checksum mismatch: {url}')
   with zipfile.ZipFile(io.BytesIO(p)) as z:
    if z.testzip() is not None:raise RuntimeError(f'Phase083 CRC failure: {url}')
   out=PROJECT/'data'/'raw'/'klines'/sym;out.mkdir(parents=True,exist_ok=True);(out/(stem+'.zip')).write_bytes(p);(out/(stem+'.zip.CHECKSUM')).write_bytes(chk)
   rows.append({'kind':'klines','symbol':sym,'date':ds,'sha256':actual,'bytes':len(p),'source_url':url})
  d+=timedelta(days=1)
 for sym in SYMBOLS:rows.append(snapshot_funding(sym))
 manifest={'engine':'V98 Independent','phase':'083','price_source':VISION,'funding_source':'official Binance USD-M historical funding endpoint (resolved host recorded per symbol)','start':START.isoformat(),'end':END.isoformat(),'files':rows}
 (PROJECT/'data'/'V98_INDEPENDENT_PHASE083_DAILY_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'phase':'083','price_archives':75,'funding_snapshots':5}))
if __name__=='__main__':main()
