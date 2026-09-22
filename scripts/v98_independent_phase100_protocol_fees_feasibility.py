#!/usr/bin/env python3
"""V98 Independent Phase100: aggregate protocol-fees feasibility only. NO alpha/PnL/prices."""
import hashlib,json,math,os,sys
from datetime import datetime,timezone,date
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
URL='https://api.llama.fi/overview/fees?excludeTotalDataChartBreakdown=true&excludeTotalDataChart=false';START,END=date(2023,1,1),date(2025,12,31);EXPECTED=1096;OUT='reports/v98_independent_phase100_protocol_fees_feasibility.json'
def day(v):
 if isinstance(v,(int,float)):
  if v>1e12:v/=1000
  return datetime.fromtimestamp(v,tz=timezone.utc).date()
 s=str(v).strip().replace('Z','+00:00');d=datetime.fromisoformat(s)
 if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
 return d.astimezone(timezone.utc).date()
def main():
 rep={'phase':'100','mode':'DATA_ONLY_NO_ALPHA_NO_PNL','source':'DefiLlama','dataset':'overview/fees.totalDataChart','url':URL,'window':[START.isoformat(),END.isoformat()],'generated_at':datetime.now(timezone.utc).isoformat(),'gate':'FAIL_DATA_NO_ALPHA'}
 try:
  req=Request(URL,headers={'Accept':'application/json','User-Agent':'CryptoAI-Lab-V98-Phase100/1.0'});raw=urlopen(req,timeout=60).read();obj=json.loads(raw);chart=obj.get('totalDataChart',[]) if isinstance(obj,dict) else [];parsed=[];invalid=0;bad=0
  for i,x in enumerate(chart):
   try:
    if isinstance(x,(list,tuple)) and len(x)>=2:d=day(x[0]);v=float(x[1])
    elif isinstance(x,dict):d=day(x.get('date',x.get('timestamp')));v=float(x.get('totalFees',x.get('fees',x.get('value'))))
    else:raise ValueError('schema')
    if not math.isfinite(v) or v<0:bad+=1;continue
    if START<=d<=END:parsed.append((d,i,v))
   except Exception:invalid+=1
  parsed.sort(key=lambda z:(z[0],z[1]));by={}
  for d,i,v in parsed:by.setdefault(d,(i,v))
  days=sorted(by);dups=len(parsed)-len(days);cov=len(days)/EXPECTED;first=days[0].isoformat() if days else None;last=days[-1].isoformat() if days else None;mono=all(a<b for a,b in zip(days,days[1:]));passed=bool(days and first<='2023-01-07' and last>='2025-12-24' and cov>=.95 and invalid==0 and bad==0 and dups==0 and mono)
  rep.update({'http_status':200,'raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_bytes':len(raw),'chart_rows':len(chart),'in_window_rows':len(parsed),'unique_days':len(days),'duplicate_days':dups,'invalid_rows':invalid,'invalid_values':bad,'coverage_fraction':cov,'first':first,'last':last,'strictly_monotonic':mono,'gate':'PASS_DATA_ONLY' if passed else 'FAIL_DATA_NO_ALPHA'})
 except HTTPError as e:
  body=e.read();rep.update({'error':f'HTTP {e.code}','body_sha256':hashlib.sha256(body).hexdigest(),'body_preview':body[:300].decode('utf-8','replace')})
 except (URLError,TimeoutError,ValueError,json.JSONDecodeError) as e:rep.update({'error':type(e).__name__,'detail':str(e)[:300]})
 os.makedirs(os.path.dirname(OUT),exist_ok=True);json.dump(rep,open(OUT,'w'),indent=2,sort_keys=True);print(json.dumps(rep,indent=2,sort_keys=True));return 0
if __name__=='__main__':sys.exit(main())
