from __future__ import annotations
import itertools,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import FuturesData
from paper_once_v15 import build_v15
REPORT=PROJECT/'reports'/'candidate_v99_r25_trisleeve_meta.json';H=(7,30,90,180,365)

def stats(e):
 e=e.dropna().astype(float)
 if len(e)<2:return {'return':0.,'max_drawdown':0.,'best_day':0.,'worst_day':0.,'positive_days':0.}
 n=e/e.iloc[0];dd=n/n.cummax()-1;d=n.resample('1D').last().pct_change(fill_method=None).dropna()
 return {'return':float(n.iloc[-1]-1),'max_drawdown':float(dd.min()),'best_day':float(d.max()) if len(d) else 0.,'worst_day':float(d.min()) if len(d) else 0.,'positive_days':float((d>0).mean()) if len(d) else 0.}
def sdata(data,start,end):return FuturesData(frames={k:v.loc[start:end].copy() for k,v in data.frames.items()},funding=data.funding.loc[start:end].copy(),symbols=data.symbols)
def cap(t,c):
 g=t.abs().sum(axis=1);f=(c/g.replace(0,np.nan)).clip(upper=1).fillna(1);return t.mul(f,axis=0)
def run(data,t,ex,cost,gross,guard=None,custom=None):
 kw={}
 if guard:kw={'drawdown_guard_threshold':guard['drawdown_threshold'],'drawdown_guard_multiplier':guard['exposure_multiplier'],'drawdown_guard_cooldown_hours':guard['cooldown_hours']}
 if custom:kw={'drawdown_guard_threshold':custom[0],'drawdown_guard_multiplier':custom[1],'drawdown_guard_cooldown_hours':custom[2]}
 return exact_fast(data,t,cost_per_side=cost,maintenance_equity_fraction=ex['maintenance_equity_fraction'],gross_guard_cap=gross,**kw)
def regime(eq,btc):
 r24=eq/eq.shift(24)-1;r7=eq/eq.shift(168)-1;r30=eq/eq.shift(720)-1;r90=eq/eq.shift(2160)-1;dd=eq/eq.cummax()-1
 b24=btc/btc.shift(24)-1;b72=btc/btc.shift(72)-1;b7=btc/btc.shift(168)-1;b30=btc/btc.shift(720)-1;ema=btc.ewm(span=336,adjust=False,min_periods=336).mean()
 strong=((r7>.025)&(r30>.055)&(r90>.075)&(dd>-.045)&(btc>ema)&(b7>0)&(b30>0)).fillna(False)
 stress=((dd<-.07)|(r24<-.035)|(b24<-.035)|(b72<-.065)|((r7<-.05)&(r30<0))).fillna(False);stress=stress.astype(float).rolling(48,min_periods=1).max().gt(0)
 return strong&~stress,stress
def attack_targets(raw,strong,scale,gross):return cap(raw.mul(strong.astype(float),axis=0)*scale,gross)
def vol(close,lb=72):return close.pct_change(fill_method=None).rolling(lb,min_periods=max(24,lb//2)).std()*np.sqrt(24*365)
def crash_targets(data,trigger24,trigger72,breadth_threshold,topn):
 close=data.close;r24=close.pct_change(24,fill_method=None);r72=close.pct_change(72,fill_method=None);breadth=(r24>0).mean(axis=1);stress=((r24['BTCUSDT']<=trigger24)|(r72['BTCUSDT']<=trigger72))&(breadth<=breadth_threshold);ema=close.ewm(span=168,adjust=False,min_periods=168).mean();eligible=close<ema;rank=r24.rank(axis=1,ascending=True,method='first');sel=eligible&(rank<=topn);raw=-sel.astype(float)*stress.astype(float).to_numpy()[:,None];iv=raw.div(vol(close,72).replace(0,np.nan));g=iv.abs().sum(axis=1).replace(0,np.nan);return iv.div(g,axis=0).fillna(0)
def combine(core,attack,hedge,strong,stress,p,cost=.001):
 idx=core.index.intersection(attack.index).intersection(hedge.index);rc=core.reindex(idx).pct_change(fill_method=None).fillna(0);ra=attack.reindex(idx).pct_change(fill_method=None).fillna(0);rh=hedge.reindex(idx).pct_change(fill_method=None).fillna(0);sg=strong.reindex(idx).fillna(False);st=stress.reindex(idx).fillna(False)
 wc=pd.Series(1.,index=idx);wa=pd.Series(0.,index=idx);wh=pd.Series(0.,index=idx);wc.loc[sg]=p['strong_core'];wa.loc[sg]=1-p['strong_core'];wc.loc[st]=p['stress_core'];wh.loc[st]=1-p['stress_core'];wc=wc.shift(1).fillna(1);wa=wa.shift(1).fillna(0);wh=wh.shift(1).fillna(0);turn=(wc.diff().abs()+wa.diff().abs()+wh.diff().abs()).fillna(0)/2
 net=wc*rc+wa*ra+wh*rh-turn*cost;f=(1+net).clip(lower=.001);return f.cumprod()
def slice_eval(data,raw,ex,g,bg,cost,ap,hp,pp,start,end):
 d=sdata(data,start,end);r=raw.reindex(index=d.close.index,columns=d.close.columns).fillna(0);core=run(d,r,ex,cost,bg,g).equity;strong,stress=regime(core,d.close['BTCUSDT']);at=attack_targets(r,strong,ap['scale'],ap['gross']);attack=run(d,at,ex,cost,ap['gross']+.1,None,(.10,.25,72)).equity;ht=crash_targets(d,hp['t24'],hp['t72'],hp['breadth'],hp['topn']);hedge=run(d,ht,ex,cost,1.1,None,(.12,.25,48)).equity;return stats(combine(core,attack,hedge,strong,stress,pp)),stats(core)
