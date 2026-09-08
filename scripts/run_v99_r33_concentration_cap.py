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
REPORT=PROJECT/'reports'/'candidate_v99_r33_concentration_cap.json';H=(7,30,90,180,365)

def stats(e):
 e=e.dropna().astype(float)
 if len(e)<2:return {'return':0.,'max_drawdown':0.,'best_day':0.,'worst_day':0.,'positive_days':0.}
 n=e/e.iloc[0];dd=n/n.cummax()-1;d=n.resample('1D').last().pct_change(fill_method=None).dropna()
 return {'return':float(n.iloc[-1]-1),'max_drawdown':float(dd.min()),'best_day':float(d.max()) if len(d) else 0.,'worst_day':float(d.min()) if len(d) else 0.,'positive_days':float((d>0).mean()) if len(d) else 0.}
def sdata(data,start,end):return FuturesData(frames={k:v.loc[start:end].copy() for k,v in data.frames.items()},funding=data.funding.loc[start:end].copy(),symbols=data.symbols)
def cap_total(t,c):
 g=t.abs().sum(axis=1);f=(c/g.replace(0,np.nan)).clip(upper=1).fillna(1);return t.mul(f,axis=0)
def run(data,t,ex,cost,gross,guard):return exact_fast(data,t,cost_per_side=cost,maintenance_equity_fraction=ex['maintenance_equity_fraction'],gross_guard_cap=gross,drawdown_guard_threshold=guard['drawdown_threshold'],drawdown_guard_multiplier=guard['exposure_multiplier'],drawdown_guard_cooldown_hours=guard['cooldown_hours'])

def redistribute_row(row,max_share):
 w=np.asarray(row,dtype=float);gross=np.abs(w).sum()
 if gross<=1e-12:return w
 cap=max_share*gross;out=np.zeros_like(w)
 for sign in (1.,-1.):
  mask=(w*sign)>1e-12
  if not mask.any():continue
  orig=np.abs(w[mask]);side=float(orig.sum());x=np.minimum(orig,cap);left=side-float(x.sum())
  for _ in range(16):
   if left<=1e-12:break
   room=np.maximum(cap-x,0);eligible=room>1e-12
   if not eligible.any():break
   basis=np.where(eligible,orig,0);bs=basis.sum()
   if bs<=1e-12:basis=np.where(eligible,1.,0);bs=basis.sum()
   add=np.minimum(room,left*basis/bs);x+=add;newleft=side-float(x.sum())
   if abs(newleft-left)<1e-12:break
   left=newleft
  out[np.where(mask)[0]]=sign*x
 return out

def concentration_transform(raw,max_share,gross_multiplier,gross_cap):
 a=raw.to_numpy(dtype=float);z=np.empty_like(a)
 for i in range(len(a)):z[i]=redistribute_row(a[i],max_share)
 t=pd.DataFrame(z,index=raw.index,columns=raw.columns)*gross_multiplier
 return cap_total(t,gross_cap)

def concentration_metrics(t):
 a=t.abs();g=a.sum(axis=1).replace(0,np.nan);share=a.div(g,axis=0).fillna(0);top1=share.max(axis=1);arr=np.sort(share.to_numpy(),axis=1);top3=arr[:,-3:].sum(axis=1) if arr.shape[1]>=3 else arr.sum(axis=1)
 return {'top1_mean':float(top1.mean()),'top1_p95':float(top1.quantile(.95)),'top3_mean':float(np.mean(top3)),'gross_mean':float(a.sum(axis=1).mean())}
def slice_eval(data,raw,ex,guard,bg,cost,p,start,end):
 d=sdata(data,start,end);r=raw.reindex(index=d.close.index,columns=d.close.columns).fillna(0);t=concentration_transform(r,p['max_share'],p['gross_multiplier'],p['gross_cap']);a=run(d,t,ex,cost,p['gross_cap'],guard).equity;b=run(d,r,ex,cost,bg,guard).equity;return stats(a),stats(b)
def main():
 cand,data,raw,_,_,q,meta=build_v15();v14=json.loads((PROJECT/'config'/cand['parent_candidate_config']).read_text());fin=json.loads((PROJECT/'config'/v14['frozen_core_config']).read_text());base=json.loads((PROJECT/'config'/fin['base_candidate_config']).read_text());ex=base['execution'];guard=v14['circuit_breaker'];bg=float(v14['allocation']['gross_drift_guard_cap']);bc=float(ex['base_cost_per_side']);sc=float(ex['severe_cost_per_side'])
 core=run(data,raw,ex,bc,bg,guard).equity;coresev=run(data,raw,ex,sc,bg,guard).equity;v15=stats(core);v15sev=stats(coresev);bs=stats(screen(data,raw,cost_per_side=bc).equity);rows=[];cache={}
 base_conc=concentration_metrics(raw)
 for ms,gm,gc in itertools.product((.35,.40,.45,.50,.55,.60,.70,.80),(1.0,1.05,1.10,1.15,1.20),(bg,1.90,2.10)):
  p={'max_share':ms,'gross_multiplier':gm,'gross_cap':gc};key=f's{ms:.2f}_m{gm:.2f}_g{gc:.3f}';t=concentration_transform(raw,ms,gm,gc);s=stats(screen(data,t,cost_per_side=bc).equity);wr=(1+s['return'])/max(1e-12,1+bs['return']);dr=abs(s['max_drawdown'])/max(1e-12,abs(bs['max_drawdown']));worst=abs(s['worst_day'])/max(1e-12,abs(bs['worst_day']));score=5*np.log(max(wr,1e-12))+5*max(0,1-dr)-6*max(0,dr-1)-3*max(0,worst-1);rows.append({'key':key,'params':p,'screen':s,'screen_wealth_ratio':float(wr),'screen_drawdown_ratio':float(dr),'screen_worst_day_ratio':float(worst),'concentration':concentration_metrics(t),'screen_score':float(score)});cache[key]=t
 rows.sort(key=lambda z:z['screen_score'],reverse=True);split=int(len(core)*.6);hs=core.index[min(split+1,len(core)-1)];vh=stats(core.loc[hs:]);exact=[]
 for row in rows[:36]:
  p=row['params'];eq=run(data,cache[row['key']],ex,bc,p['gross_cap'],guard).equity;s=stats(eq);ho=stats(eq.loc[hs:]);wr=(1+s['return'])/max(1e-12,1+v15['return']);hr=(1+ho['return'])/max(1e-12,1+vh['return']);dr=abs(s['max_drawdown'])/max(1e-12,abs(v15['max_drawdown']));worst=abs(s['worst_day'])/max(1e-12,abs(v15['worst_day']));score=6*np.log(max(wr,1e-12))+5*np.log(max(hr,1e-12))+6*max(0,1-dr)-8*max(0,dr-1)-4*max(0,worst-1);exact.append({**row,'summary':s,'holdout':ho,'wealth_ratio_to_v15':float(wr),'holdout_wealth_ratio_to_v15':float(hr),'drawdown_ratio_to_v15':float(dr),'worst_day_ratio_to_v15':float(worst),'exact_score':float(score)})
 exact.sort(key=lambda z:z['exact_score'],reverse=True);final=[];end=data.close.index[-1]
 for row in exact[:10]:
  p=row['params'];iso={};iv={};rw={};dw={};ww={};pw={}
  for days in H:
   a,b=slice_eval(data,raw,ex,guard,bg,bc,p,end-pd.Timedelta(days=days),end);k=str(days);iso[k]=a;iv[k]=b;rw[k]=a['return']>=b['return'];dw[k]=abs(a['max_drawdown'])<=abs(b['max_drawdown']);ww[k]=abs(a['worst_day'])<=abs(b['worst_day']);pw[k]=a['positive_days']>=b['positive_days']
  ss=stats(run(data,cache[row['key']],ex,sc,p['gross_cap'],guard).equity);sr=(1+ss['return'])/max(1e-12,1+v15sev['return']);gate=bool(all(rw.values()) and all(dw.values()) and all(ww.values()) and row['wealth_ratio_to_v15']>=1.50 and row['holdout_wealth_ratio_to_v15']>=1.25 and row['drawdown_ratio_to_v15']<=.70 and row['worst_day_ratio_to_v15']<=.75 and sr>=1.25);final.append({**row,'isolated':iso,'isolated_v15':iv,'isolated_return_wins_vs_v15':rw,'isolated_drawdown_wins_vs_v15':dw,'isolated_worst_day_wins_vs_v15':ww,'isolated_positive_days_wins_vs_v15':pw,'severe_cost':ss,'severe_wealth_ratio_to_v15':float(sr),'superior_gate_passed':gate})
 final.sort(key=lambda z:(z['superior_gate_passed'],sum(z['isolated_return_wins_vs_v15'].values()),sum(z['isolated_drawdown_wins_vs_v15'].values()),z['holdout_wealth_ratio_to_v15'],z['wealth_ratio_to_v15'],-z['drawdown_ratio_to_v15']),reverse=True);sel=final[0] if final else None
 out={'study':'V99 R33 same-side concentration cap','status':'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER','objective':'preserve V15 long/short gross budget while capping single-position concentration and redistributing excess only to already-active positions on the same side','grid_size':len(rows),'v15':{'summary':v15,'severe_cost':v15sev,'raw_concentration':base_conc},'selected':sel,'finalists':final,'top_exact':exact[:25],'top_screen':rows[:40],'disclosure':'Historical research only. The rule is generic and causal: it uses only the current requested target vector, not future returns or symbol-specific hindsight. Any winner requires an envelope comparison and fresh forward validation.','funding_quarantined_symbols':q,'v15_metadata':meta};REPORT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'study':out['study'],'grid_size':len(rows),'v15':out['v15'],'selected':sel},indent=2),flush=True)
if __name__=='__main__':main()
