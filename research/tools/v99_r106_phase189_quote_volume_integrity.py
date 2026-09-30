#!/usr/bin/env python3
"""Phase189 source audit: Binance Spot quoteAssetVolume, TRAIN-only; no PnL."""
import json,urllib.parse,urllib.request,hashlib
from pathlib import Path
START_MS=1638316800000
CUTOFF_MS=1705536000000
BASE='https://api.binance.com/api/v3/klines'
def fetch(symbol):
 out=[]; start=START_MS
 while start<CUTOFF_MS:
  q=urllib.parse.urlencode({'symbol':symbol,'interval':'1h','startTime':start,'endTime':CUTOFF_MS-1,'limit':1000})
  with urllib.request.urlopen(BASE+'?'+q,timeout=30) as r: batch=json.load(r)
  if not batch: break
  for x in batch:
   t=int(x[0])
   if t>=CUTOFF_MS: raise AssertionError('holdout row parsed')
   out.append((t,float(x[5]),float(x[7])))
  nxt=int(batch[-1][0])+3600000
  if nxt<=start: raise AssertionError('non advancing pagination')
  start=nxt
 return out
def audit(rows):
 assert rows and all(q>=0 and b>=0 for _,b,q in rows)
 ts=[x[0] for x in rows]; assert len(ts)==len(set(ts)) and ts==sorted(ts)
 digest=hashlib.sha256('\n'.join(f'{t},{b:.17g},{q:.17g}' for t,b,q in rows).encode()).hexdigest()
 return {'rows':len(rows),'first_open_ms':ts[0],'last_open_ms':ts[-1],'non_1h_gaps':sum((b-a)!=3600000 for a,b in zip(ts,ts[1:])),'positive_quote_volume_rows':sum(q>0 for _,_,q in rows),'sha256':digest}
def main():
 btc=fetch('BTCUSDT'); eth=fetch('ETHUSDT'); a={'BTCUSDT':audit(btc),'ETHUSDT':audit(eth)}
 assert [x[0] for x in btc]==[x[0] for x in eth], 'pair timestamp mismatch'
 for rows in (btc,eth): assert any(abs(b-q)>1e-9 for _,b,q in rows if b>0 and q>0)
 out={'study':'V99 R106 Phase189 quote-volume source integrity','source':'Binance Spot GET /api/v3/klines field 7 quoteAssetVolume','train_end_exclusive':'2024-01-18T00:00:00+00:00','holdout_market_values_parsed':False,'audit':a,'status':'SOURCE_SEMANTICS_PASS'}
 Path('reports').mkdir(exist_ok=True); Path('reports/v99_r106_phase189_quote_volume_integrity.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps(out,sort_keys=True,indent=2))
if __name__=='__main__': main()
