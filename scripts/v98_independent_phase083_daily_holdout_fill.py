from __future__ import annotations
# Namespaced Phase083 acquisition for the pre-registered incomplete current month.
import csv,hashlib,html,io,json,re,urllib.error,urllib.parse,urllib.request,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1];VISION='https://data.binance.vision/data/futures/um/daily'
FAPI_HOSTS=('https://fapi.binance.com','https://fapi1.binance.com','https://fapi2.binance.com','https://fapi3.binance.com','https://fapi4.binance.com');MIRROR='https://pandabull.io/perpetuals-funding/binance'
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
def funding_records(sym):
 q=urllib.parse.urlencode({'symbol':sym,'startTime':ms(START),'endTime':ms(END,True),'limit':1000});errs=[]
 for host in FAPI_HOSTS:
  url=host+'/fapi/v1/fundingRate?'+q
  try:
   p=fetch(url,8)
   if p:return url,p,json.loads(p),'official_api'
  except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:errs.append(f'{host}:{type(e).__name__}:{getattr(e,"code","")}')
 # GitHub US runners can receive Binance HTTP 451. Use a read-only mirror that
 # explicitly labels the venue Binance; snapshot its raw HTML and require the
 # complete 3x/day 8h event grid before any holdout PnL is allowed.
 url=f'{MIRROR}/{sym}';p=fetch(url,30)
 if not p:raise RuntimeError('Phase083 funding unavailable; official errors='+';'.join(errs))
 text=html.unescape(re.sub(r'<[^>]+>',' ',p.decode('utf-8','replace')));text=re.sub(r'\s+',' ',text)
 pat=re.compile(r'(2026-09-(?:0[1-9]|1[0-5]))\s+(00:00|08:00|16:00)\s+UTC\s+([+-]?\d+(?:\.\d+)?)%\s+8')
 found={}
 for ds,hm,pct in pat.findall(text):
  ts=int(datetime.fromisoformat(ds+'T'+hm+':00+00:00').timestamp()*1000);found[ts]=float(pct)/100.0
 expected=[int(datetime(2026,9,d,h,tzinfo=timezone.utc).timestamp()*1000) for d in range(1,16) for h in (0,8,16)]
 missing=[x for x in expected if x not in found]
 if missing:raise RuntimeError(f'Phase083 mirror incomplete for {sym}: {len(missing)} funding events missing; official errors='+';'.join(errs))
 records=[{'fundingTime':x,'fundingRate':format(found[x],'.10f')} for x in expected]
 return url,p,records,'pandabull_binance_mirror'
def snapshot_funding(sym):
 url,payload,records,source=funding_records(sym);raw_sha=hashlib.sha256(payload).hexdigest();lo,hi=ms(START),ms(END,True);seen=[]
 if len(records)!=45:raise RuntimeError(f'Phase083 expected 45 funding events for {sym}, got {len(records)}')
 for r in records:
  ts=int(r['fundingTime']);rate=float(r['fundingRate'])
  if not lo<=ts<=hi or not(-0.05<rate<0.05):raise RuntimeError(f'Phase083 invalid funding event {sym}: {r}')
  seen.append(ts)
 if seen!=sorted(set(seen)):raise RuntimeError(f'Phase083 duplicate/nonmonotone funding events for {sym}')
 buf=io.StringIO();w=csv.writer(buf,lineterminator='\n');w.writerow(['calc_time','last_funding_rate','funding_interval_hours'])
 for r in records:w.writerow([int(r['fundingTime']),r['fundingRate'],8])
 stem=f'{sym}-fundingRate-2026-09-01_2026-09-15';out=PROJECT/'data'/'raw'/'fundingRate'/sym;out.mkdir(parents=True,exist_ok=True);zp=out/(stem+'.zip')
 with zipfile.ZipFile(zp,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(stem+'.csv',buf.getvalue().encode())
 return {'kind':'fundingRate','symbol':sym,'events':45,'source_kind':source,'raw_source_sha256':raw_sha,'snapshot_sha256':hashlib.sha256(zp.read_bytes()).hexdigest(),'source_url':url}
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
   out=PROJECT/'data'/'raw'/'klines'/sym;out.mkdir(parents=True,exist_ok=True);(out/(stem+'.zip')).write_bytes(p);(out/(stem+'.zip.CHECKSUM')).write_bytes(chk);rows.append({'kind':'klines','symbol':sym,'date':ds,'sha256':actual,'bytes':len(p),'source_url':url})
  d+=timedelta(days=1)
 for sym in SYMBOLS:rows.append(snapshot_funding(sym))
 manifest={'engine':'V98 Independent','phase':'083','price_source':VISION,'funding_policy':'official Binance USD-M API first; provenance-hashed Binance-labelled mirror only when GitHub runner geo-blocks official API; complete 45-event grid mandatory','start':START.isoformat(),'end':END.isoformat(),'files':rows}
 (PROJECT/'data'/'V98_INDEPENDENT_PHASE083_DAILY_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'phase':'083','price_archives':75,'funding_snapshots':5}))
if __name__=='__main__':main()
