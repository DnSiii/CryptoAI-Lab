# Phase123 preregistered aggressor-run imbalance; train-only, holdout prohibited.
from __future__ import annotations
import concurrent.futures,csv,hashlib,io,json,time,urllib.error,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase123_aggressor_run_imbalance_train_alpha.json'
BASE='https://data.binance.vision/data/futures/um/daily/aggTrades';ALPHA_GROSS=.20;N=12;MIN_ASSETS=8;TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC')

def get(u):
 last=None
 for attempt in range(6):
  try:
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase123'}),timeout=180) as r:return r.read()
  except (urllib.error.URLError,TimeoutError,ConnectionError) as e:last=e;time.sleep(min(32,2**attempt))
 raise last

def load(job):
 s,d=job;assert pd.Timestamp(d,tz='UTC')<TRAIN_END;stem=f'{s}-aggTrades-{d}.zip';u=f'{BASE}/{s}/{stem}';raw=get(u);chk=get(u+'.CHECKSUM').decode().split()[0]
 if hashlib.sha256(raw).hexdigest()!=chk:raise RuntimeError('checksum '+stem)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None:raise RuntimeError('crc '+stem)
  names=[n for n in z.namelist() if not n.endswith('/')]
  if len(names)!=1:raise RuntimeError('member '+stem)
  acc={};cur_h=None;cur_sign=0;run_len=0;buy_mass=sell_mass=0
  def flush_run():
   nonlocal run_len,buy_mass,sell_mass
   if run_len:
    if cur_sign>0:buy_mass+=run_len*run_len
    else:sell_mass+=run_len*run_len
    run_len=0
  def flush_hour():
   nonlocal buy_mass,sell_mass
   if cur_h is not None:
    flush_run();acc[cur_h]=(buy_mass,sell_mass);buy_mass=sell_mass=0
  for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding='utf-8')):
   if not row:continue
   try:ts=int(row[5]);bm=str(row[6]).strip().lower()
   except (ValueError,TypeError,IndexError):continue
   if bm not in ('true','false'):continue
   h=ts//3600000
   if h*3600000>=int(TRAIN_END.timestamp()*1000):raise RuntimeError('holdout timestamp encountered '+stem)
   sign=1 if bm=='false' else -1
   if cur_h is None:cur_h=h;cur_sign=sign;run_len=1;continue
   if h!=cur_h:
    flush_hour();cur_h=h;cur_sign=sign;run_len=1
   elif sign==cur_sign:run_len+=1
   else:flush_run();cur_sign=sign;run_len=1
  flush_hour()
 return s,[(h,b,sl) for h,(b,sl) in acc.items()]

def rz(x):
 n=x.notna().sum(axis=1);med=x.median(axis=1);dev=x.sub(med,axis=0);mad=dev.abs().median(axis=1);valid=(n>=MIN_ASSETS)&np.isfinite(mad)&(mad>1e-12);return dev.div(mad.where(valid),axis=0).where(valid,np.nan)

def main():
 assert (PROJECT/'research'/'v99_r106_phase123_aggressor_run_imbalance_prereg.md').exists()
 p121=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase121_large_trade_pressure_train_alpha.json').read_text());assert p121['status']=='TRAIN_ALPHA_REJECT'
 p119=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase119_aggtrades_integrity_probe.json').read_text());assert p119['status']=='INTEGRITY_PROBE_PASS' and p119['holdout_market_values_not_downloaded_or_parsed']
 av=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase118_aggtrades_availability_audit.json').read_text());assert av['status']=='AVAILABILITY_AUDIT_COMPLETE' and av['holdout_market_values_not_downloaded_or_parsed']
 selected=sorted(av['symbols'],key=lambda s:(int(av['symbols'][s]['listed_compressed_bytes']),s))[:N];jobs=[]
 for s in selected:
  v=av['symbols'][s];miss=set(v['missing_dates']);jobs += [(s,d.date().isoformat()) for d in pd.date_range(v['first'],'2024-01-17',freq='D') if d.date().isoformat() not in miss]
 assert jobs and all(pd.Timestamp(d,tz='UTC')<TRAIN_END for _,d in jobs)
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup();common=[s for s in selected if s in data.close.columns]
 if len(common)<MIN_ASSETS:raise RuntimeError(f'operational reject: only {len(common)} executable assets')
 # integer epoch-hour keys avoid per-trade Timestamp construction; scientific definition unchanged.
 x=pd.DataFrame(index=data.close.index,columns=common,dtype=float);epoch_to_index={int(t.timestamp()//3600):t for t in x.index if t<TRAIN_END}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for s,rows in pool.map(load,[(s,d) for s,d in jobs if s in common]):
   for h,b,sl in rows:
    den=b+sl;t=epoch_to_index.get(h)
    if den>0 and t is not None:x.at[t,s]=(b-sl)/den
 z=rz(x);sig=np.tanh(z).shift(1);sig=sig.where(sig.notna().sum(axis=1)>=MIN_ASSETS,0).fillna(0);targets=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns);targets.loc[:,common]=sig.div(sig.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
 result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),ALPHA_GROSS);d=p47.diag(result,data.close.index,max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC')),TRAIN_END);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase123 — AGGRESSOR RUN IMBALANCE TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase123_aggressor_run_imbalance_prereg.md','source':'official Binance USD-M daily aggTrades + CHECKSUM','feature':'hourly squared same-side aggressor run-mass imbalance; cross-sectional median/MAD z; tanh; entire alpha t-1; L1','direction':'continuation','selected_symbols':selected,'executable_symbols':common,'min_assets':MIN_ASSETS,'alpha_gross':ALPHA_GROSS,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_parsed':True,'missing_archives_not_filled':True},'train_end_exclusive':TRAIN_END.isoformat(),'archives_consumed':len([(s,d) for s,d in jobs if s in common]),'diagnostic':d,'selected_train_only':'aggressor_run_imbalance' if passed else None,'next_gate':'PASS freezes exact spec for folds/supersevere/regime/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'symbols':common,'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
