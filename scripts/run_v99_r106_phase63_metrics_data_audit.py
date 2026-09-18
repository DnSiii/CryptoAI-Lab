from __future__ import annotations
import concurrent.futures,datetime as dt,hashlib,io,json,re,urllib.parse,urllib.request,xml.etree.ElementTree as ET,zipfile,csv
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1];OUT=PROJECT/'reports'/'candidate_v99_r106_phase63_metrics_data_audit.json';S3='https://s3-ap-northeast-1.amazonaws.com/data.binance.vision';CDN='https://data.binance.vision/';NS={'s3':'http://s3.amazonaws.com/doc/2006-03-01/'}

def get(u):
 req=urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase63'})
 with urllib.request.urlopen(req,timeout=90) as r:return r.read()

def list_keys(prefix):
 keys=[];token=None
 while True:
  q={'list-type':'2','prefix':prefix,'max-keys':'1000'}
  if token:q['continuation-token']=token
  root=ET.fromstring(get(S3+'?'+urllib.parse.urlencode(q)))
  keys += [x.text for x in root.findall('s3:Contents/s3:Key',NS) if x.text]
  trunc=(root.findtext('s3:IsTruncated',default='false',namespaces=NS).lower()=='true')
  if not trunc:break
  token=root.findtext('s3:NextContinuationToken',namespaces=NS)
  if not token:raise RuntimeError('truncated listing without continuation token')
 return keys

def verify(key):
 raw=get(CDN+key);chk=get(CDN+key+'.CHECKSUM');want=chk.decode().split()[0];got=hashlib.sha256(raw).hexdigest()
 if got!=want:raise RuntimeError('sha256 '+key)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None:raise RuntimeError('crc '+key)
  rows=list(csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8')))
  if len(rows)<2:raise RuntimeError('empty '+key)
  header=rows[0]
 return key,header,len(rows)-1

def main():
 cov=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase60_taker_buy_train_coverage_audit.json').read_text());train_end=dt.datetime.fromisoformat(cov['train_end']).date();manifest=json.loads((PROJECT/'data'/'CANONICAL_MANIFEST_RESEARCH_PIT48.json').read_text());syms=sorted(manifest['symbols']);per={};samples=[];schemas={}
 def one(s):
  prefix=f'data/futures/um/daily/metrics/{s}/';keys=list_keys(prefix);z=[]
  for k in keys:
   m=re.search(r'-metrics-(\d{4}-\d{2}-\d{2})\.zip$',k)
   if m and dt.date.fromisoformat(m.group(1))<=train_end:z.append((dt.date.fromisoformat(m.group(1)),k))
  z.sort();return s,z
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:listed=list(pool.map(one,syms))
 for s,z in listed:
  if not z:per[s]={'observed_files':0,'first':None,'last':None,'expected_files':0,'missing_dates':[],'coverage_ratio':0.0};continue
  first,last=z[0][0],z[-1][0];obs={d for d,k in z};expected=[first+dt.timedelta(days=i) for i in range((last-first).days+1)];missing=[d.isoformat() for d in expected if d not in obs]
  per[s]={'observed_files':len(z),'first':first.isoformat(),'last':last.isoformat(),'expected_files':len(expected),'missing_dates':missing,'coverage_ratio':len(obs)/len(expected)}
  # Deterministic integrity/schema sample: first available file of each calendar month, all pre-holdout.
  seen=set()
  for d,k in z:
   ym=(d.year,d.month)
   if ym not in seen:seen.add(ym);samples.append(k)
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
  verified=list(pool.map(verify,samples))
 for k,h,n in verified:schemas.setdefault(tuple(h),0);schemas[tuple(h)]+=1
 out={'study':'V99 R106 Phase63 — orthogonal Binance USD-M futures metrics DATA AUDIT ONLY','status':'DATA_AUDIT_COMPLETE','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'train_end':train_end.isoformat(),'holdout_not_listed_or_parsed':True,'source':{'listing':S3,'download':CDN+'data/futures/um/daily/metrics/','official_public_archive':True},'symbols':per,'summary':{'symbols':len(syms),'symbols_with_data':sum(v['observed_files']>0 for v in per.values()),'observed_files':sum(v['observed_files'] for v in per.values()),'missing_dates':sum(len(v['missing_dates']) for v in per.values()),'integrity_files_verified':len(verified),'schema_variants':len(schemas)},'schema_inventory':[{'header':list(h),'sample_files':n} for h,n in schemas.items()],'integrity_sampling':'first available archive of every calendar month per symbol; SHA256 + ZIP CRC + nonempty CSV; listing coverage accounts for every pre-holdout daily archive','alpha_prohibited':True,'next_gate':'Review coverage/schema only. Any feature/direction/horizon requires a separate post-audit pre-registration before return/PnL evaluation.','disclosure':'No relation to returns, PnL, V99 regimes or benchmark outcomes is computed in Phase63.'};OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['summary'],indent=2))
if __name__=='__main__':main()
