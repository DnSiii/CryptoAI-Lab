from __future__ import annotations
import concurrent.futures, csv, datetime as dt, hashlib, io, json, urllib.error, urllib.request, zipfile
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase60_taker_buy_train_coverage_audit.json'
BASE='https://data.binance.vision/data/futures/um/monthly/klines'

def month_iter(a,b):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield f'{y:04d}-{m:02d}'; m+=1
        if m==13: y,m=y+1,1

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'CryptoAI-research-v99-r106/60'})
    try:
        with urllib.request.urlopen(req,timeout=60) as r:return r.read()
    except urllib.error.HTTPError as e:
        if e.code==404:return None
        raise

def audit_job(job):
    symbol,month,first_ms,train_end_ms=job; stem=f'{symbol}-1h-{month}.zip'; url=f'{BASE}/{symbol}/1h/{stem}'
    raw=get(url)
    if raw is None:return {'symbol':symbol,'month':month,'status':'missing'}
    chk=get(url+'.CHECKSUM')
    if chk is None:return {'symbol':symbol,'month':month,'status':'checksum_missing'}
    expected=chk.decode().split()[0]; actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected:return {'symbol':symbol,'month':month,'status':'checksum_fail'}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:return {'symbol':symbol,'month':month,'status':'crc_fail'}
        names=z.namelist()
        if len(names)!=1:return {'symbol':symbol,'month':month,'status':'member_fail'}
        reader=csv.reader(io.TextIOWrapper(z.open(names[0]),encoding='utf-8'))
        seen=[]; inv=True
        for r in reader:
            if not r or r[0] in ('open_time','open_time_ms'):continue
            if len(r)<12:return {'symbol':symbol,'month':month,'status':'schema_fail'}
            ot=int(r[0])
            # Strictly do not inspect feature values beyond the frozen train cutoff.
            if ot>train_end_ms:continue
            if ot<first_ms:continue
            vol=float(r[5]); qv=float(r[7]); tb=float(r[9]); tbq=float(r[10])
            inv &= (0<=tb<=vol+1e-12 and 0<=tbq<=qv+1e-9)
            seen.append(ot)
    if not inv:return {'symbol':symbol,'month':month,'status':'invariant_fail'}
    if seen!=sorted(set(seen)):return {'symbol':symbol,'month':month,'status':'order_or_duplicate_fail'}
    return {'symbol':symbol,'month':month,'status':'ok','rows_train':len(seen),'first_train_ms':seen[0] if seen else None,'last_train_ms':seen[-1] if seen else None,'sha256':actual}

def main():
    manifest=json.loads((PROJECT/'data'/'CANONICAL_MANIFEST_RESEARCH_PIT48.json').read_text())
    p47=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase47_downside_semivariance_alpha_audit.json').read_text())
    train_end=dt.datetime.fromisoformat(p47['data']['train_end']); train_end_ms=int(train_end.timestamp()*1000)
    jobs=[]; expected={}
    for symbol,meta in manifest['symbols'].items():
        first=dt.datetime.fromisoformat(meta['first']); first_ms=int(first.timestamp()*1000); expected[symbol]=(first_ms,train_end_ms)
        jobs += [(symbol,m,first_ms,train_end_ms) for m in month_iter(first,train_end)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
        results=list(pool.map(audit_job,jobs))
    by_symbol={}; gate=True
    for symbol,(first_ms,end_ms) in expected.items():
        rs=[r for r in results if r['symbol']==symbol]; bad=[r for r in rs if r['status']!='ok']; rows=sum(r.get('rows_train',0) for r in rs)
        times=[]
        for r in rs:
            if r.get('first_train_ms') is not None:times += [r['first_train_ms'],r['last_train_ms']]
        # Archive-level completeness gate: no missing/bad monthly file and boundary coverage.
        boundary=bool(times and min(times)==first_ms and max(times)<=end_ms and max(times)>=end_ms-3_600_000)
        passed=not bad and boundary and rows>0; gate &= passed
        by_symbol[symbol]={'months':len(rs),'rows_train':rows,'bad_files':bad,'boundary_coverage_pass':boundary,'pass':passed}
    out={'study':'V99 R106 phase 60 — PIT48 full train-only taker-buy coverage/provenance audit','status':'TRAIN_COVERAGE_PASS' if gate else 'TRAIN_COVERAGE_FAIL_NO_ALPHA',
         'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'train_end':train_end.isoformat(),
         'precommitment':{'integrity_only':True,'feature_values_after_train_end_not_parsed':True,'no_returns':True,'no_alpha_direction':True,'no_parameter_search':True,'no_holdout_inspection':True,'no_proxy':True},
         'source':'Binance USD-M monthly 1h klines; every consumed archive SHA256 checked against exchange CHECKSUM and ZIP CRC tested',
         'jobs':len(results),'symbols':len(by_symbol),'symbols_pass':sum(v['pass'] for v in by_symbol.values()),'all_train_coverage_pass':gate,'by_symbol':by_symbol,
         'next_gate':'Only if all_train_coverage_pass: pre-register one economically motivated taker-flow transform/direction using train-only logic, then build t-1 feature. Otherwise repair data coverage without alpha evaluation.',
         'disclosure':'No holdout feature values, returns, candidate selection, or strategy mutation occur in phase60.'}
    OUT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps({'status':out['status'],'jobs':out['jobs'],'symbols_pass':out['symbols_pass'],'symbols':out['symbols']},indent=2))
if __name__=='__main__':main()
