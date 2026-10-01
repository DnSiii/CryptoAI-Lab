#!/usr/bin/env python3
"""V98 Independent Phase202: preregistered range-position reversal.
Training-only (<2026), causal t-1 features, fixed 8-spec grid, deterministic report.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

FOLDS={"2023":("2023-01-01","2024-01-01"),"2024":("2024-01-01","2025-01-01"),"2025":("2025-01-01","2026-01-01")}
STRESS={"base":20.0,"severe":35.0,"supersevere":55.0}
GRID=[(w,q,h) for w in (24,72) for q in (0.05,0.10) for h in (3,6)]

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1<<20),b''): h.update(x)
 return h.hexdigest()

def load(root,symbol):
 p=root/f"{symbol}_1h.csv"; x=pd.read_csv(p)
 t='open_time' if 'open_time' in x.columns else ('timestamp' if 'timestamp' in x.columns else x.columns[0])
 x[t]=pd.to_datetime(x[t],utc=True,errors='coerce'); x=x.dropna(subset=[t]).sort_values(t).drop_duplicates(t).set_index(t)
 x=x[x.index<pd.Timestamp('2026-01-01',tz='UTC')]
 for c in ('high','low','close','fundingRate'):
  if c in x: x[c]=pd.to_numeric(x[c],errors='coerce')
 if not {'high','low','close'}.issubset(x.columns): raise ValueError(f'{symbol}: missing high/low/close')
 return x

def positions(x,w,q,hold):
 # Feature observed at decision t uses only bars through t-1.
 hi=x.high.rolling(w,min_periods=w).max().shift(1); lo=x.low.rolling(w,min_periods=w).min().shift(1); prev=x.close.shift(1)
 width=(hi-lo).replace(0,np.nan); rp=(prev-lo)/width
 event=pd.Series(0.0,index=x.index); event[rp<=q]=1.; event[rp>=1-q]=-1.
 # Fixed hold, no pyramiding/re-entry until flat.
 pos=pd.Series(0.0,index=x.index); remaining=0; side=0.0
 for i,s in enumerate(event.to_numpy()):
  if remaining<=0:
   side=float(s); remaining=hold if side else 0
  pos.iat[i]=side if remaining>0 else 0.0
  if remaining>0:
   remaining-=1
   if remaining==0: side=0.0
 return pos

def pf(x):
 gp=x[x>0].sum(); gl=-x[x<0].sum(); return float(gp/gl) if gl>0 else (999.0 if gp>0 else 0.0)

def metrics(x):
 x=x.dropna(); eq=(1+x).cumprod(); dd=eq/eq.cummax()-1; wins=x[x>0]; losses=x[x<0]
 return {'return':float(eq.iloc[-1]-1) if len(eq) else 0.,'max_drawdown':float(dd.min()) if len(dd) else 0.,'profit_factor':pf(x),'payoff':float(wins.mean()/(-losses.mean())) if len(wins) and len(losses) else 0.,'win_rate':float((x>0).mean()) if len(x) else 0.,'n_hours':int(len(x))}

def evaluate(frames,spec,rtbps):
 w,q,h=spec; idx=pd.DatetimeIndex(sorted(set().union(*[set(x.index) for x in frames.values()])))
 raw=pd.DataFrame({s:positions(x,w,q,h).reindex(idx).fillna(0) for s,x in frames.items()},index=idx)
 denom=raw.abs().sum(axis=1).replace(0,np.nan); wt=raw.div(denom,axis=0).fillna(0)
 rets=pd.DataFrame({s:np.log(x.close).diff().reindex(idx).fillna(0) for s,x in frames.items()})
 gross=(wt.shift(1).fillna(0)*rets).sum(axis=1); turn=wt.diff().abs().sum(axis=1).fillna(0); cost=turn*(rtbps/10000.0)
 fund=pd.Series(0.,index=idx); fund_available=[]
 for s,x in frames.items():
  if 'fundingRate' in x:
   fund_available.append(s); fund += wt[s].shift(1).fillna(0)*x.fundingRate.reindex(idx).fillna(0)
 net=gross-cost-fund; daily=net.resample('1D').sum(); active=wt.abs().sum(axis=1)>0
 out={'metrics':metrics(net),'positive_days':float((daily>0).mean()) if len(daily) else 0.,'active_hours':int(active.sum()),'turnover':float(turn.sum()),'funding_symbols':fund_available}
 out['folds']={k:metrics(net[(net.index>=pd.Timestamp(a,tz='UTC'))&(net.index<pd.Timestamp(b,tz='UTC'))]) for k,(a,b) in FOLDS.items()}
 mkt=rets.mean(axis=1).rolling(24,min_periods=24).sum().shift(1); reg=pd.Series('sideways',index=idx); reg[mkt>0.02]='bull'; reg[mkt<-0.02]='bear'
 out['regimes']={r:metrics(net[reg==r]) for r in ('bull','bear','sideways')}
 losses=net[net<0].sort_values(); wins=net[net>0].sort_values(ascending=False)
 out['bottom10_loss_share']=float((-losses.head(10).sum())/(-losses.sum())) if len(losses) else 0.; out['top10_gain_share']=float(wins.head(10).sum()/wins.sum()) if len(wins) else 0.
 symp={s:float((wt[s].shift(1).fillna(0)*rets[s]-wt[s].diff().abs().fillna(0)*(rtbps/10000.0)).sum()) for s in frames}; out['symbol_pnl']=symp
 tot=sum(abs(v) for v in symp.values()); out['max_symbol_abs_share']=float(max([abs(v) for v in symp.values()]+[0])/tot) if tot else 0.
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data-root',default='data/canonical'); ap.add_argument('--config',default='config/v98_independent_phase050_data.json'); ap.add_argument('--output',default='reports/v98_independent_phase202_results.json'); a=ap.parse_args()
 cfg=json.load(open(a.config)); symbols=cfg.get('symbols',[]); root=Path(a.data_root); frames={s:load(root,s) for s in symbols}
 inv={'cutoff_ok':all(len(x)==0 or x.index.max()<pd.Timestamp('2026-01-01',tz='UTC') for x in frames.values()),'rows':{s:len(x) for s,x in frames.items()},'input_sha256':{s:sha(root/f'{s}_1h.csv') for s in symbols}}
 results={}
 for spec in GRID:
  key=f'w{spec[0]}_q{int(spec[1]*100):02d}_h{spec[2]}'; results[key]={k:evaluate(frames,spec,bps) for k,bps in STRESS.items()}
 def passes(v):
  b=v['base']; fs=b['folds']; return b['active_hours']>0 and all(fs[y]['return']>0 for y in FOLDS) and b['metrics']['profit_factor']>1.05 and b['metrics']['max_drawdown']>-0.35 and b['positive_days']>0.50 and b['max_symbol_abs_share']<0.60 and v['severe']['metrics']['return']>0 and v['supersevere']['metrics']['max_drawdown']>-0.60
 passing=[k for k,v in results.items() if passes(v)]
 report={'phase':202,'family':'range_position_reversal','preregistered_grid':[{'range_h':w,'extreme':q,'hold_h':h} for w,q,h in GRID],'stress_roundtrip_bps':STRESS,'invariants':inv,'results':results,'passing_specs':passing,'decision':'ADVANCE_TRAINING_CANDIDATE' if passing else 'REJECT_FAMILY_NO_RESCUE'}
 Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(report,sort_keys=True,separators=(',',':')),encoding='utf-8')
 print(json.dumps({'decision':report['decision'],'passing_specs':passing,'output':a.output},sort_keys=True))
if __name__=='__main__': main()
