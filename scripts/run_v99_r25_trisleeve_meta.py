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
 b24=btc/btc.shift(24)-1;b72=btc/btc.shift(72)-1;b7=btc/btc.shift(168)-1;b30=btc/btc.shift(720)-1;ema=btc.ewm(span=336,adjust=False,min_periods=336).mean();breadth=None
 strong=((r7>.025)&(r30>.055)&(r90>.075)&(dd>-.045)&(btc>ema)&(b7>0)&(b30>0)).fillna(False)
 stress=((dd<-.07)|(r24<-.035)|(b24<-.035)|(b72<-.065)|((r7<-.05)&(r30<0))).fillna(False);stress=stress.astype(float).rolling(48,min_periods=1).max().gt(0)
 return strong&~stress,stress
def attack_targets(raw,strong,scale,gross):return cap(raw.mul(strong.astype(float),axis=0)*scale,gross)
def vol(close,lb=72):return close.pct_change(fill_method=None).rolling(lb,min_periods=max(24,lb//2)).std()*np.sqrt(24*365)
def crash_targets(data,trigger24,trigger72,breadth_threshold,topn):
 close=data.close;r24=close.pct_change(24,fill_method=None);r72=close.pct_change(72,fill_method=None);breadth=(r24>0).mean(axis=1);stress=((r24['BTCUSDT']<=trigger24)|(r72['BTCUSDT']<=trigger72))&(breadth<=breadth_threshold);ema=close.ewm(span=168,adjust=False,min_periods=168).mean();eligible=close<ema;rank=r24.rank(axis=1,ascending=True,method='first');sel=eligible&(rank<=topn);raw=-sel.astype(float)*stress.astype(float).to_numpy()[:,None];iv=raw.div(vol(close,72).replace(0,np.nan));g=iv.abs().sum(axis=1).replace(0,np.nan);return iv.div(g,axis=0).fillna(0)
def combine(core,attack,hedge,strong,stress,p,cost=.001):
 idx=core.index.intersection(attack.index).intersection(hedge.index);rc=core.reindex(idx).pct_change(fill_method=None).fillna(0);ra=attack.reindex(idx).pct_change(fill_method=None).fillna(0);rh=hedge.reindex(idx).pct_change(fill_method=None).fillna(0);sg=strong.reindex(idx).fillna(False);st=stress.reindex(idx).fillna(False)
 wc=pd.Series(1.,index=idx);wa=pd.Series(0.,index=idx);wh=pd.Series(0.,index=idx);wc.loc[sg]=p['strong_core'];wa.loc[sg]=1-p['strong_core'];wc.loc[st]=p['stress_core'];wh.loc[st]=1-p['stress_core'];# decisions at close t apply to next hour
 wc=wc.shift(1).fillna(1);wa=wa.shift(1).fillna(0);wh=wh.shift(1).fillna(0);turn=(wc.diff().abs()+wa.diff().abs()+wh.diff().abs()).fillna(0)/2
 net=wc*rc+wa*ra+wh*rh-turn*cost;f=(1+net).clip(lower=.001);return f.cumprod()
def slice_eval(data,raw,ex,g,bg,cost,ap,hp,pp,start,end):
 d=sdata(data,start,end);r=raw.reindex(index=d.close.index,columns=d.close.columns).fillna(0);core=run(d,r,ex,cost,bg,g).equity;strong,stress=regime(core,d.close['BTCUSDT']);at=attack_targets(r,strong,ap['scale'],ap['gross']);attack=run(d,at,ex,cost,ap['gross']+.1,None,(.10,.25,72)).equity;ht=crash_targets(d,hp['t24'],hp['t72'],hp['breadth'],hp['topn']);hedge=run(d,ht,ex,cost,1.1,None,(.12,.25,48)).equity;return stats(combine(core,attack,hedge,strong,stress,pp)),stats(core)
def main():
 cand,data,raw,_,_,q,meta=build_v15();v14=json.loads((PROJECT/'config'/cand['parent_candidate_config']).read_text());fin=json.loads((PROJECT/'config'/v14['frozen_core_config']).read_text());base=json.loads((PROJECT/'config'/fin['base_candidate_config']).read_text());ex=base['execution'];g=v14['circuit_breaker'];bg=float(v14['allocation']['gross_drift_guard_cap']);bc=float(ex['base_cost_per_side']);sc=float(ex['severe_cost_per_side']);core=run(data,raw,ex,bc,bg,g).equity;coresev=run(data,raw,ex,sc,bg,g).equity;v15=stats(core);v15sev=stats(coresev);strong,stress=regime(core,data.close['BTCUSDT'])
 attacks={};
 for scale,gross in itertools.product((1.5,2.,2.5,3.),(1.8,2.2,2.6)):
  key=f'x{scale:.1f}_g{gross:.1f}';t=attack_targets(raw,strong,scale,gross);attacks[key]=(run(data,t,ex,bc,gross+.1,None,(.10,.25,72)).equity,run(data,t,ex,sc,gross+.1,None,(.10,.25,72)).equity,{'scale':scale,'gross':gross})
 hedges={}
 for t24,t72,br,topn in itertools.product((-.025,-.035,-.045),(-.05,-.07),(.30,.40),(2,3)):
  key=f'h{t24:.3f}_{t72:.3f}_{br:.2f}_{topn}';t=crash_targets(data,t24,t72,br,topn);hedges[key]=(run(data,t,ex,bc,1.1,None,(.12,.25,48)).equity,run(data,t,ex,sc,1.1,None,(.12,.25,48)).equity,{'t24':t24,'t72':t72,'breadth':br,'topn':topn})
 split=int(len(core)*.6);hs=core.index[min(split+1,len(core)-1)];rows=[]
 for ak,(ae,asev,ap),hk,(he,hsev,hp),strong_core,stress_core in itertools.product(attacks.items(),hedges.items(),(.65,.75,.85),(.40,.55,.70)):
  pp={'strong_core':strong_core,'stress_core':stress_core};eq=combine(core,ae,he,strong,stress,pp);s=stats(eq);hold=stats(eq.loc[hs:]);hv=stats(core.loc[hs:]);wr=(1+s['return'])/(1+v15['return']);hr=(1+hold['return'])/(1+hv['return']);dr=abs(s['max_drawdown'])/abs(v15['max_drawdown']);worst=abs(s['worst_day'])/abs(v15['worst_day']);score=4*np.log(max(wr,1e-12))+3*np.log(max(hr,1e-12))+3*max(0,1-dr)-4*max(0,dr-1)-2*max(0,worst-1);rows.append({'attack_key':ak,'hedge_key':hk,'attack_params':ap,'hedge_params':hp,'portfolio_params':pp,'summary':s,'wealth_ratio_to_v15':float(wr),'holdout_wealth_ratio':float(hr),'drawdown_ratio_to_v15':float(dr),'worst_day_ratio_to_v15':float(worst),'score':float(score)})
 rank=sorted(rows,key=lambda z:z['score'],reverse=True);final=[];end=data.close.index[-1]
 for row in rank[:8]:
  iso={};iv={};wins={};ddw={}
  for d in H:
   a,b=slice_eval(data,raw,ex,g,bg,bc,row['attack_params'],row['hedge_params'],row['portfolio_params'],end-pd.Timedelta(days=d),end);iso[str(d)]=a;iv[str(d)]=b;wins[str(d)]=a['return']>=b['return'];ddw[str(d)]=abs(a['max_drawdown'])<=abs(b['max_drawdown'])
  ae,asev,_=attacks[row['attack_key']];he,hsev,_=hedges[row['hedge_key']];sev=stats(combine(coresev,asev,hsev,strong,stress,row['portfolio_params']));sr=(1+sev['return'])/(1+v15sev['return']);gate=bool(all(wins.values()) and row['wealth_ratio_to_v15']>=1.30 and row['drawdown_ratio_to_v15']<=.70 and row['worst_day_ratio_to_v15']<=.75 and row['holdout_wealth_ratio']>=1.20 and sr>=1.15);final.append({**row,'isolated':iso,'isolated_v15':iv,'isolated_return_wins_vs_v15':wins,'isolated_drawdown_wins_vs_v15':ddw,'severe_cost':sev,'severe_wealth_ratio_to_v15':float(sr),'superior_gate_passed':gate})
 final.sort(key=lambda z:(z['superior_gate_passed'],sum(z['isolated_return_wins_vs_v15'].values()),z['holdout_wealth_ratio'],z['wealth_ratio_to_v15'],-z['drawdown_ratio_to_v15']),reverse=True);sel=final[0] if final else None;out={'study':'V99 R25 tri-sleeve meta portfolio','status':'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER','architecture':'untouched V15 core + separately governed strong-regime attack sleeve + separately governed crash-short hedge, with causal capital rotation and transfer friction','v15':{'summary':v15,'severe_cost':v15sev},'selected':sel,'finalists':final,'top_screen':rank[:30],'screen_count':len(rows),'disclosure':'Historical research only. Separate sleeve state prevents hedge/attack from tripping the core circuit breaker. Any winner still needs freezing and independent forward validation.','funding_quarantined_symbols':q,'v15_metadata':meta};REPORT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'study':out['study'],'screen_count':len(rows),'v15':out['v15'],'selected':sel},indent=2),flush=True)
if __name__=='__main__':main()
