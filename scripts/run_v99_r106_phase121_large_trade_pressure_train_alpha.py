# Phase121 preregistered causal large-trade pressure; train-only, holdout prohibited.
from __future__ import annotations
import csv,hashlib,io,json,time,urllib.error,urllib.request,zipfile
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
from v99_r106_exact_rolling_quantile import ExactRollingQuantile
PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'reports'/'candidate_v99_r106_phase121_large_trade_pressure_train_alpha.json'
BASE='https://data.binance.vision/data/futures/um/daily/aggTrades'; TRAIN_END=pd.Timestamp('2024-01-18',tz='UTC'); N=12; MIN_ASSETS=8; GROSS=.20; WINDOW_MS=30*24*3600*1000; Q=.90

def get(u):
 last=None
 for attempt in range(6):
  try:
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'CryptoAI-v99-r106-phase121'}),timeout=180) as r:return r.read()
  except (urllib.error.URLError,TimeoutError,ConnectionError) as e:last=e;time.sleep(min(32,2**attempt))
 raise last

def raw_rows(s,d):
 assert pd.Timestamp(d,tz='UTC')<TRAIN_END
 stem=f'{s}-aggTrades-{d}.zip';u=f'{BASE}/{s}/{stem}';raw=get(u);chk=get(u+'.CHECKSUM').decode().split()[0]
 if hashlib.sha256(raw).hexdigest()!=chk:raise RuntimeError('checksum '+stem)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None:raise RuntimeError('crc '+stem)
  names=[n for n in z.namelist() if not n.endswith('/')]
  if len(names)!=1:raise RuntimeError('member '+stem)
  for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding='utf-8')):
   if not row:continue
   try:q=float(row[2]);ts=int(row[5]);bm=str(row[6]).strip().lower()
   except (ValueError,TypeError,IndexError):continue
   if not np.isfinite(q) or q<=0 or bm not in ('true','false'):continue
   if pd.Timestamp(ts,unit='ms',tz='UTC')>=TRAIN_END:raise RuntimeError('holdout timestamp encountered '+stem)
   yield ts,q,bm

def jobs_for(s,av):
 v=av['symbols'][s];miss=set(v['missing_dates'])
 return [d.date().isoformat() for d in pd.date_range(v['first'],'2024-01-17',freq='D') if d.date().isoformat() not in miss]

def build_symbol(s,dates,index):
 # Pass 1 freezes exact finite TRAIN support only. Support coordinates do not set thresholds.
 support=set();n=0
 for d in dates:
  for _,q,_ in raw_rows(s,d):support.add(q);n+=1
 if not support:return pd.Series(index=index,dtype=float),n
 rq=ExactRollingQuantile(support,WINDOW_MS,Q);out={};cur_h=None;buy=sell=0.;hour_rows=[]
 # Pass 2 is chronological. Crucially query() occurs once at hour boundary BEFORE any trade from that hour is added.
 for d in dates:
  for ts,q,bm in raw_rows(s,d):
   h=pd.Timestamp(ts,unit='ms',tz='UTC').floor('1h')
   if cur_h is None:cur_h=h;thr=rq.query(ts)
   elif h!=cur_h:
    if buy+sell>0:out[cur_h]=(buy-sell)/(buy+sell)
    for ets,eq in hour_rows:rq.add(ets,eq)
    cur_h=h;buy=sell=0.;hour_rows=[];thr=rq.query(ts)
   if thr is not None and q>thr:
    if bm=='false':buy+=q
    else:sell+=q
   hour_rows.append((ts,q))
 if cur_h is not None:
  if buy+sell>0:out[cur_h]=(buy-sell)/(buy+sell)
  for ets,eq in hour_rows:rq.add(ets,eq)
 return pd.Series(out,index=index,dtype=float),n

def rz(x):
 n=x.notna().sum(axis=1);med=x.median(axis=1);dev=x.sub(med,axis=0);mad=dev.abs().median(axis=1);valid=(n>=MIN_ASSETS)&np.isfinite(mad)&(mad>1e-12);return dev.div(mad.where(valid),axis=0).where(valid,np.nan)

def main():
 assert (PROJECT/'research'/'v99_r106_phase121_large_trade_pressure_prereg.md').exists()
 p120=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase120_raw_taker_imbalance_train_alpha.json').read_text());assert p120['status']=='TRAIN_ALPHA_REJECT','Phase121 may run only after Phase120 decision'
 p119=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase119_aggtrades_integrity_probe.json').read_text());assert p119['status']=='INTEGRITY_PROBE_PASS' and p119['holdout_market_values_not_downloaded_or_parsed']
 av=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase118_aggtrades_availability_audit.json').read_text());assert av['status']=='AVAILABILITY_AUDIT_COMPLETE'
 # Same precommitted resource universe rule as Phase120; no return/PnL enters membership.
 selected=sorted(av['symbols'],key=lambda s:(int(av['symbols'][s]['listed_compressed_bytes']),s))[:N]
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup();common=[s for s in selected if s in data.close.columns]
 if len(common)<MIN_ASSETS:raise RuntimeError(f'operational reject: only {len(common)} executable assets')
 x=pd.DataFrame(index=data.close.index,columns=common,dtype=float);counts={};archives=0
 for s in common:
  dates=jobs_for(s,av);archives+=len(dates);x[s],counts[s]=build_symbol(s,dates,data.close.index);print('built',s,'trades',counts[s],flush=True)
 z=rz(x);sig=np.tanh(z).shift(1);sig=sig.where(sig.notna().sum(axis=1)>=MIN_ASSETS,0).fillna(0)
 targets=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns);targets.loc[:,common]=sig.div(sig.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
 result=p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),GROSS);d=p47.diag(result,data.close.index,max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC')),TRAIN_END);passed=bool(d['stable_train'])
 out={'study':'V99 R106 Phase121 — CAUSAL LARGE-TRADE PRESSURE TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase121_large_trade_pressure_prereg.md','source':'official Binance USD-M aggTrades + CHECKSUM','feature':'qty > strict-prior 30d exact q90; hourly aggressive large-trade qty imbalance; cross-sectional median/MAD z; tanh; entire alpha t-1; L1','quantile':'nearest-rank exact empirical q90','direction':'continuation','selected_symbols':selected,'executable_symbols':common,'min_assets':MIN_ASSETS,'alpha_gross':GROSS,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_parsed':True,'missing_archives_not_filled':True},'train_end_exclusive':TRAIN_END.isoformat(),'archives_consumed_per_pass':archives,'two_pass_train_only':True,'train_trade_counts':counts,'diagnostic':d,'selected_train_only':'large_trade_pressure' if passed else None,'next_gate':'PASS freezes exact spec for supersevere/regime/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'symbols':common,'archives_per_pass':archives,'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
