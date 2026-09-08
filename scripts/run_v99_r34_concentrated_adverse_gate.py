from __future__ import annotations
import itertools,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast,screen
from cryptoai_v13.data import FuturesData
from paper_once_v15 import build_v15
REPORT=PROJECT/'reports'/'candidate_v99_r34_concentrated_adverse_gate.json';H=(7,30,90,180,365)

def stats(e):
 e=e.dropna().astype(float)
 if len(e)<2:return {'return':0.,'max_drawdown':0.,'best_day':0.,'worst_day':0.,'positive_days':0.}
 n=e/e.iloc[0];dd=n/n.cummax()-1;d=n.resample('1D').last().pct_change(fill_method=None).dropna()
 return {'return':float(n.iloc[-1]-1),'max_drawdown':float(dd.min()),'best_day':float(d.max()) if len(d) else 0.,'worst_day':float(d.min()) if len(d) else 0.,'positive_days':float((d>0).mean()) if len(d) else 0.}
def sdata(data,start,end):return FuturesData(frames={k:v.loc[start:end].copy() for k,v in data.frames.items()},funding=data.funding.loc[start:end].copy(),symbols=data.symbols)
def cap_total(t,c):
 g=t.abs().sum(axis=1);f=(c/g.replace(0,np.nan)).clip(upper=1).fillna(1);return t.mul(f,axis=0)
def run(data,t,ex,cost,gross,guard):return exact_fast(data,t,cost_per_side=cost,maintenance_equity_fraction=ex['maintenance_equity_fraction'],gross_guard_cap=gross,drawdown_guard_threshold=guard['drawdown_threshold'],drawdown_guard_multiplier=guard['exposure_multiplier'],drawdown_guard_cooldown_hours=guard['cooldown_hours'])

def transform(raw,close,p):
 gross=raw.abs().sum(axis=1).replace(0,np.nan);share=raw.abs().div(gross,axis=0).fillna(0);sgn=np.sign(raw)
 r24=close.pct_change(24,fill_method=None);r72=close.pct_change(72,fill_method=None)
 signed24=sgn*r24;signed72=sgn*r72
 concentrated=share>=p['share_trigger'];bad=concentrated&((signed24<=-p['adverse24'])|(signed72<=-p['adverse72']))
 if p['cooldown']>1:bad=bad.astype(float).rolling(p['cooldown'],min_periods=1).max().gt(0)
 factor=pd.DataFrame(1.0,index=raw.index,columns=raw.columns).mask(bad,p['cut_scale'])
 t=raw*factor*p['gross_multiplier'];return cap_total(t,p['gross_cap']),bad,share

def slice_eval(data,t,raw,ex,guard,cg,bg,cost,start,end):
 d=sdata(data,start,end);tt=t.reindex(index=d.close.index,columns=d.close.columns).fillna(0);rr=raw.reindex(index=d.close.index,columns=d.close.columns).fillna(0);return stats(run(d,tt,ex,cost,cg,guard).equity),stats(run(d,rr,ex,cost,bg,guard).equity)
def main():
 cand,data,raw,_,_,q,meta=build_v15();v14=json.loads((PROJECT/'config'/cand['parent_candidate_config']).read_text());fin=json.loads((PROJECT/'config'/v14['frozen_core_config']).read_text());base=json.loads((PROJECT/'config'/fin['base_candidate_config']).read_text());ex=base['execution'];guard=v14['circuit_breaker'];bg=float(v14['allocation']['gross_drift_guard_cap']);bc=float(ex['base_cost_per_side']);sc=float(ex['severe_cost_per_side'])
 core=run(data,raw,ex,bc,bg,guard).equity;coresev=run(data,raw,ex,sc,bg,guard).equity;v15=stats(core);v15sev=stats(coresev);bs=stats(screen(data,raw,cost_per_side=bc).equity);rows=[];cache={}
 for share,(a24,a72),cut,cool,gm,gc in itertools.product((.45,.55,.65),((.02,.04),(.03,.06),(.04,.08)),(.25,.50,.75),(6,12,24),(1.0,1.05),(bg,1.90)):
  p={'share_trigger':share,'adverse24':a24,'adverse72':a72,'cut_scale':cut,'cooldown':cool,'gross_multiplier':gm,'gross_cap':gc};key=f's{share:.2f}_a{a24:.2f}_{a72:.2f}_c{cut:.2f}_h{cool}_m{gm:.2f}_g{gc:.3f}';t,bad,sh=transform(raw,data.close,p);s=stats(screen(data,t,cost_per_side=bc).equity);wr=(1+s['return'])/max(1e-12,1+bs['return']);dr=abs(s['max_drawdown'])/max(1e-12,abs(bs['max_drawdown']));worst=abs(s['worst_day'])/max(1e-12,abs(bs['worst_day']));event=float(bad.to_numpy(dtype=float).mean());score=5*np.log(max(wr,1e-12))+6*max(0,1-dr)-7*max(0,dr-1)-4*max(0,worst-1)-max(0,event-.10)*2;rows.append({'key':key,'params':p,'screen':s,'screen_wealth_ratio':float(wr),'screen_drawdown_ratio':float(dr),'screen_worst_day_ratio':float(worst),'gate_event_fraction':event,'screen_score':float(score)});cache[key]=t
 rows.sort(key=lambda z:z['screen_score'],reverse=True);split=int(len(core)*.6);hs=core.index[min(split+1,len(core)-1)];vh=stats(core.loc[hs:]);exact=[]
 for row in rows[:40]:
  p=row['params'];eq=run(data,cache[row['key']],ex,bc,p['gross_cap'],guard).equity;s=stats(eq);ho=stats(eq.loc[hs:]);wr=(1+s['return'])/max(1e-12,1+v15['return']);hr=(1+ho['return'])/max(1e-12,1+vh['return']);dr=abs(s['max_drawdown'])/max(1e-12,abs(v15['max_drawdown']));worst=abs(s['worst_day'])/max(1e-12,abs(v15['worst_day']));score=6*np.log(max(wr,1e-12))+5*np.log(max(hr,1e-12))+7*max(0,1-dr)-9*max(0,dr-1)-5*max(0,worst-1);exact.append({**row,'summary':s,'holdout':ho,'wealth_ratio_to_v15':float(wr),'holdout_wealth_ratio_to_v15':float(hr),'drawdown_ratio_to_v15':float(dr),'worst_day_ratio_to_v15':float(worst),'exact_score':float(score)})
 exact.sort(key=lambda z:z['exact_score'],reverse=True);final=[];end=data.close.index[-1]
 for row in exact[:10]:
  p=row['params'];t=cache[row['key']];iso={};iv={};rw={};dw={};ww={};pw={}
  for days in H:
   a,b=slice_eval(data,t,raw,ex,guard,p['gross_cap'],bg,bc,end-pd.Timedelta(days=days),end);k=str(days);iso[k]=a;iv[k]=b;rw[k]=a['return']>=b['return'];dw[k]=abs(a['max_drawdown'])<=abs(b['max_drawdown']);ww[k]=abs(a['worst_day'])<=abs(b['worst_day']);pw[k]=a['positive_days']>=b['positive_days']
  ss=stats(run(data,t,ex,sc,p['gross_cap'],guard).equity);sr=(1+ss['return'])/max(1e-12,1+v15sev['return']);gate=bool(all(rw.values()) and all(dw.values()) and all(ww.values()) and row['wealth_ratio_to_v15']>=1.50 and row['holdout_wealth_ratio_to_v15']>=1.25 and row['drawdown_ratio_to_v15']<=.70 and row['worst_day_ratio_to_v15']<=.75 and sr>=1.25);final.append({**row,'isolated':iso,'isolated_v15':iv,'isolated_return_wins_vs_v15':rw,'isolated_drawdown_wins_vs_v15':dw,'isolated_worst_day_wins_vs_v15':ww,'isolated_positive_days_wins_vs_v15':pw,'severe_cost':ss,'severe_wealth_ratio_to_v15':float(sr),'superior_gate_passed':gate})
 final.sort(key=lambda z:(z['superior_gate_passed'],sum(z['isolated_return_wins_vs_v15'].values()),sum(z['isolated_drawdown_wins_vs_v15'].values()),z['holdout_wealth_ratio_to_v15'],z['wealth_ratio_to_v15'],-z['drawdown_ratio_to_v15']),reverse=True);sel=final[0] if final else None
 out={'study':'V99 R34 concentrated adverse-move gate','status':'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER','objective':'leave V15 unchanged unless a highly concentrated requested position develops materially adverse trailing movement, then temporarily cut only that position','grid_size':len(rows),'v15':{'summary':v15,'severe_cost':v15sev},'selected':sel,'finalists':final,'top_exact':exact[:25],'top_screen':rows[:50],'disclosure':'Historical research only. Concentration and adverse-move conditions use only information available at close t and execute at open t+1. Isolated replays retain only pre-start causal lookback context; capital and execution state reset. Any winner requires envelope validation and fresh forward paper.','funding_quarantined_symbols':q,'v15_metadata':meta};REPORT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'study':out['study'],'grid_size':len(rows),'v15':out['v15'],'selected':sel},indent=2),flush=True)
if __name__=='__main__':main()
