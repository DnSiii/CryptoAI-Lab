#!/usr/bin/env python3
"""V98 Independent Phase200: preregistered volatility-compression breakout.
Training-only (<2026), causal t-1 features, fixed 8-spec grid, deterministic report.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd

FOLDS={"2023":("2023-01-01","2024-01-01"),"2024":("2024-01-01","2025-01-01"),"2025":("2025-01-01","2026-01-01")}
STRESS={"base":20.0,"severe":35.0,"supersevere":55.0}
GRID=[(c,b,h) for c in (72,168) for b in (24,72) for h in (8,24)]

def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1<<20),b''): h.update(x)
 return h.hexdigest()

def load(root,symbol):
 p=root/f"{symbol}_1h.csv"; d=pd.read_csv(p)
 t='open_time' if 'open_time' in d.columns else ('timestamp' if 'timestamp' in d.columns else d.columns[0])
 d[t]=pd.to_datetime(d[t],utc=True,errors='coerce'); d=d.dropna(subset=[t]).sort_values(t).drop_duplicates(t).set_index(t)
 d=d[d.index<pd.Timestamp('2026-01-01',tz='UTC')]
 for c in ('high','low','close','fundingRate'):
  if c in d: d[c]=pd.to_numeric(d[c],errors='coerce')
 if not {'high','low','close'}.issubset(d.columns): raise ValueError(f'{symbol}: missing OHLC columns')
 return d

def positions(d,cwin,bwin,hold):
 r=np.log(d.close).diff(); rv=r.rolling(24,min_periods=24).std()*math.sqrt(24)
 compressed=(rv.shift(1)<rv.shift(1).rolling(cwin,min_periods=cwin).median())
 prior_hi=d.high.shift(2).rolling(bwin,min_periods=bwin).max(); prior_lo=d.low.shift(2).rolling(bwin,min_periods=bwin).min(); px=d.close.shift(1)
 sig=pd.Series(0.0,index=d.index); sig[compressed & (px>prior_hi)]=1.; sig[compressed & (px<prior_lo)]=-1.
 active=sum(sig.shift(k).fillna(0) for k in range(hold)); return np.sign(active).fillna(0)

def pf(x):
 gp=x[x>0].sum(); gl=-x[x<0].sum(); return float(gp/gl) if gl>0 else (999.0 if gp>0 else 0.0)

def metrics(x):
 x=x.dropna(); eq=(1+x).cumprod(); dd=eq/eq.cummax()-1; wins=x[x>0]; losses=x[x<0]
 return {'return':float(eq.iloc[-1]-1) if len(eq) else 0.,'max_drawdown':float(dd.min()) if len(dd) else 0.,'profit_factor':pf(x),'payoff':float(wins.mean()/(-losses.mean())) if len(wins) and len(losses) else 0.,'win_rate':float((x>0).mean()) if len(x) else 0.,'n_hours':int(len(x))}

def evaluate(frames,spec,rtbps):
 c,b,h=spec; idx=sorted(set().union(*[set(x.index) for x in frames.values()])); idx=pd.DatetimeIndex(idx)
 raw=pd.DataFrame({s:positions(d,c,b,h).reindex(idx).fillna(0) for s,d in frames.items()},index=idx)
 denom=raw.abs().sum(axis=1).replace(0,np.nan); w=raw.div(denom,axis=0).fillna(0)
 rets=pd.DataFrame({s:np.log(d.close).diff().reindex(idx).fillna(0) for s,d in frames.items()})
 gross=(w.shift(1).fillna(0)*rets).sum(axis=1); turn=w.diff().abs().sum(axis=1).fillna(0); cost=turn*(rtbps/10000.0)
 fund=pd.Series(0.,index=idx); fund_available=[]
 for s,d in frames.items():
  if 'fundingRate' in d:
   fund_available.append(s); fund += w[s].shift(1).fillna(0)*d.fundingRate.reindex(idx).fillna(0)
 net=gross-cost-fund
 daily=net.resample('1D').sum(); active=(w.abs().sum(axis=1)>0)
 out={'metrics':metrics(net),'positive_days':float((daily>0).mean()) if len(daily) else 0.,'active_hours':int(active.sum()),'turnover':float(turn.sum()),'funding_symbols':fund_available}
 out['folds']={k:metrics(net[(net.index>=pd.Timestamp(a,tz='UTC'))&(net.index<pd.Timestamp(z,tz='UTC'))]) for k,(a,z) in FOLDS.items()}
 # Regimes from equal-weight market 24h return, causal.
 mkt=rets.mean(axis=1).rolling(24,min_periods=24).sum().shift(1); reg=pd.Series('sideways',index=idx); reg[mkt>0.02]='bull'; reg[mkt<-0.02]='bear'
 out['regimes']={r:metrics(net[reg==r]) for r in ('bull','bear','sideways')}
 # Tail and concentration diagnostics.
 losses=net[net<0].sort_values(); out['bottom10_loss_share']=float((-losses.head(10).sum())/(-losses.sum())) if len(losses) else 0.
 symp={s:float((w[s].shift(1).fillna(0)*rets[s]-w[s].diff().abs().fillna(0)*(rtbps/10000.0)).sum()) for s in frames}; out['symbol_pnl']=symp
 tot=sum(abs(v) for v in symp.values()); out['max_symbol_abs_share']=float(max([abs(v) for v in symp.values()]+[0])/tot) if tot else 0.
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data-root',default='data/canonical'); ap.add_argument('--config',default='config/v98_independent_phase050_data.json'); ap.add_argument('--output',default='reports/v98_independent_phase200_results.json'); a=ap.parse_args()
 cfg=json.load(open(a.config)); symbols=cfg.get('symbols',[]); root=Path(a.data_root); frames={s:load(root,s) for s in symbols}
 inv={'cutoff_ok':all((len(d)==0 or d.index.max()<pd.Timestamp('2026-01-01',tz='UTC')) for d in frames.values()),'symbols':symbols,'rows':{s:len(d) for s,d in frames.items()},'input_sha256':{s:sha(root/f'{s}_1h.csv') for s in symbols}}
 results={}
 for spec in GRID:
  key=f'c{spec[0]}_b{spec[1]}_h{spec[2]}'; results[key]={k:evaluate(frames,spec,bps) for k,bps in STRESS.items()}
 def passes(v):
  b=v['base']; fs=b['folds']; return b['active_hours']>0 and all(fs[y]['return']>0 for y in FOLDS) and b['metrics']['profit_factor']>1.05 and b['metrics']['max_drawdown']>-0.35 and b['positive_days']>0.50 and b['max_symbol_abs_share']<0.60 and v['severe']['metrics']['return']>0 and v['supersevere']['metrics']['max_drawdown']>-0.60
 passing=[k for k,v in results.items() if passes(v)]
 report={'phase':200,'family':'volatility_compression_breakout','preregistered_grid':[{'compression_h':c,'breakout_h':b,'hold_h':h} for c,b,h in GRID],'stress_roundtrip_bps':STRESS,'invariants':inv,'results':results,'passing_specs':passing,'decision':'ADVANCE_TRAINING_CANDIDATE' if passing else 'REJECT_FAMILY_NO_RESCUE'}
 Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(report,sort_keys=True,separators=(',',':')),encoding='utf-8')
 print(json.dumps({'decision':report['decision'],'passing_specs':passing,'output':a.output},sort_keys=True))
if __name__=='__main__': main()
