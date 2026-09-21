from __future__ import annotations
# Namespaced Phase083 acquisition fallback for the pre-registered incomplete current month.
import hashlib,io,json,urllib.error,urllib.request,zipfile
from datetime import date,timedelta
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
BASE='https://data.binance.vision/data/futures/um/daily'
SYMBOLS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT')
START=date(2026,9,1);END=date(2026,9,15)

def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-V98-independent/1'})
 try:
  with urllib.request.urlopen(req,timeout=45) as r:return r.read()
 except urllib.error.HTTPError as e:
  if e.code==404:return None
  raise

def main():
 rows=[];d=START
 while d<=END:
  ds=d.isoformat()
  for sym in SYMBOLS:
   for kind in ('klines','fundingRate'):
    stem=f'{sym}-1h-{ds}' if kind=='klines' else f'{sym}-fundingRate-{ds}'
    url=f'{BASE}/{kind}/{sym}/'+(('1h/' if kind=='klines' else '')+stem+'.zip')
    payload=fetch(url)
    if payload is None: raise RuntimeError(f'Phase083 required daily holdout archive missing: {url}')
    chk=fetch(url+'.CHECKSUM')
    if chk is None: raise RuntimeError(f'Phase083 checksum missing: {url}')
    expected=chk.decode().split()[0];actual=hashlib.sha256(payload).hexdigest()
    if actual!=expected: raise RuntimeError(f'Phase083 checksum mismatch: {url}')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
     if z.testzip() is not None: raise RuntimeError(f'Phase083 CRC failure: {url}')
    out=PROJECT/'data'/'raw'/kind/sym;out.mkdir(parents=True,exist_ok=True)
    (out/(stem+'.zip')).write_bytes(payload);(out/(stem+'.zip.CHECKSUM')).write_bytes(chk)
    rows.append({'kind':kind,'symbol':sym,'date':ds,'sha256':actual,'bytes':len(payload)})
  d+=timedelta(days=1)
 manifest={'engine':'V98 Independent','phase':'083','source':BASE,'start':START.isoformat(),'end':END.isoformat(),'files':rows}
 (PROJECT/'data'/'V98_INDEPENDENT_PHASE083_DAILY_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'phase':'083','daily_files':len(rows),'start':START.isoformat(),'end':END.isoformat()}))
if __name__=='__main__':main()
