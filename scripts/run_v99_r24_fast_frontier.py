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
REPORT=PROJECT/'reports'/'candidate_v99_r24_fast_frontier.json'; H=(7,30,90,180,365)

def stats(e):
 e=e.dropna().astype(float)
 if len(e)<2:return {'return':0.,'max_drawdown':0.,'best_day':0.,'worst_day':0.,'positive_days':0.}
 n=e/e.iloc[0];dd=n/n.cummax()-1;d=n.resample('1D').last().pct_change(fill_method=None).dropna()
 return {'return':float(n.iloc[-1]-1),'max_drawdown':float(dd.min()),'best_day':float(d.max()) if len(d) else 0.,'worst_day':float(d.min()) if len(d) else 0.,'positive_days':float((d>0).mean()) if len(d) else 0.}
def sdata(data,start,end):return FuturesData(frames={k:v.loc[start:end].copy() for k,v in data.frames.items()},funding=data.funding.loc[start:end].copy(),symbols=data.symbols)
def cap(t,c):
 g=t.abs().sum(axis=1);f=(c/g.replace(0,np.nan)).clip(upper=1).fillna(1);return t.mul(f,axis=0)
def run(data,t,ex,cost,gross,guard=None):
 kw={}
 if guard:kw={'drawdown_guard_threshold':guard['drawdown_threshold'],'drawdown_guard_multiplier':guard['exposure_multiplier'],'drawdown_guard_cooldown_hours':guard['cooldown_hours']}
 return exact_fast(data,t,cost_per_side=cost,maintenance_equity_fraction=ex['maintenance_equity_fraction'],gross_guard_cap=gross,**kw)
def gf(eq,g):
 out=np.ones(len(eq));peak=1.;active=False;until=-1;v=eq.to_numpy(float)
 for i,x in enumerate(v):
  if active and i>=until:active=False;peak=x
  dd=x/peak-1 if peak else -1
  if not active and dd<=-abs(g['drawdown_threshold']):active=True;until=i+g['cooldown_hours']
  out[i]=g['exposure_multiplier'] if active else 1.;peak=max(peak,x)
 return pd.Series(out,index=eq.index)
def features(eq,btc):
 r7=eq/eq.shift(168)-1;r30=eq/eq.shift(720)-1;r90=eq/eq.shift(2160)-1;dd=eq/eq.cummax()-1;r24=eq/eq.shift(24)-1
 b7=btc/btc.shift(168)-1;b30=btc/btc.shift(720)-1;ema=btc.ewm(span=336,adjust=False,min_periods=336).mean();rv7=btc.pct_change(fill_method=None).rolling(168,min_periods=48).std();rv30=btc.pct_change(fill_method=None).rolling(720,min_periods=168).std()
 votes=pd.concat([(r7>0.015),(r30>0.04),(r90>0.07),(btc>ema),(b30>0)],axis=1).sum(axis=1)
 stress=((dd<-0.06)|(r24<-0.035)|((r7<-0.05)&(r30<0))|((rv7>1.5*rv30)&(r7<0))).fillna(False);stress=stress.astype(float).rolling(72,min_periods=1).max().gt(0)
 return votes,stress,r7,r30,b7,b30
def scale_from(feat,p):
 votes,stress,r7,r30,b7,b30=feat;s=pd.Series(1.,index=votes.index);strong=(votes>=p['strong_votes'])&(r7>p['r7_min'])&(r30>p['r30_min']);moderate=(votes>=p['mid_votes'])&~strong
 s.loc[moderate]=p['mid_scale'];s.loc[strong]=p['strong_scale'];s.loc[stress]=p['defense_scale'];s=s.ewm(span=p['smooth'],adjust=False).mean();return s.clip(lower=.1,upper=p['max_scale'])
def approx(eq,scale,gross,cost):
 r=eq.pct_change(fill_method=None).fillna(0);applied=scale.shift(1).fillna(1);extra=(applied.diff().abs().fillna(0)*gross.reindex(eq.index).fillna(0)*cost);f=1+applied*r-extra;f=f.clip(lower=.001);return f.cumprod()
def build_targets(raw,shadow,g,p,feat):return cap(raw.mul(gf(shadow,g)*scale_from(feat,p),axis=0),p['gross_cap'])
def eval_slice(data,raw,ex,g,bg,cost,p,start,end):
 d=sdata(data,start,end);r=raw.reindex(index=d.close.index,columns=d.close.columns).fillna(0);sh=run(d,r,ex,cost,bg,g).equity;ft=features(sh,d.close['BTCUSDT']);t=build_targets(r,sh,g,p,ft);return stats(run(d,t,ex,cost,p['gross_cap'],None).equity),stats(sh)
def main():
 cand,data,raw,_,_,q,meta=build_v15();v14=json.loads((PROJECT/'config'/cand['parent_candidate_config']).read_text());fin=json.loads((PROJECT/'config'/v14['frozen_core_config']).read_text());base=json.loads((PROJECT/'config'/fin['base_candidate_config']).read_text());ex=base['execution'];g=v14['circuit_breaker'];bg=float(v14['allocation']['gross_drift_guard_cap']);bc=float(ex['base_cost_per_side']);sc=float(ex['severe_cost_per_side'])
 shadow=run(data,raw,ex,bc,bg,g).equity;v15=stats(shadow);v15sev=stats(run(data,raw,ex,sc,bg,g).equity);feat=features(shadow,data.close['BTCUSDT']);gross=raw.abs().sum(axis=1);split=int(len(shadow)*.6);te=shadow.index[split];hs=shadow.index[min(split+1,len(shadow)-1)]
 screened=[]
 for strong,mid,ss,ms,ds,r7m,r30m,smooth,gcap in itertools.product((4,5),(3,4),(1.20,1.35,1.50,1.70),(1.00,1.10,1.20),(.25,.45,.65),(.005,.02),(.025,.05),(3,12,24),(2.0,2.3,2.6)):
  if mid>=strong:continue
  p={'strong_votes':strong,'mid_votes':mid,'strong_scale':ss,'mid_scale':ms,'defense_scale':ds,'r7_min':r7m,'r30_min':r30m,'smooth':smooth,'max_scale':ss,'gross_cap':gcap};s=scale_from(feat,p);ap=approx(shadow,s,gross,bc);full=stats(ap);hold=stats(ap.loc[hs:]);holdv=stats(shadow.loc[hs:]);wr=(1+full['return'])/(1+v15['return']);hr=(1+hold['return'])/(1+holdv['return']);dr=abs(full['max_drawdown'])/abs(v15['max_drawdown']);worst=abs(full['worst_day'])/abs(v15['worst_day']);score=4*np.log(max(wr,1e-12))+3*np.log(max(hr,1e-12))+2*max(0,1-dr)-3*max(0,dr-1)-1.5*max(0,worst-1);screened.append({'params':p,'approx':full,'approx_wealth_ratio':float(wr),'approx_holdout_wealth_ratio':float(hr),'approx_dd_ratio':float(dr),'score':float(score)})
 screen=sorted(screened,key=lambda z:z['score'],reverse=True);exact=[];cache={}
 for row in screen[:16]:
  p=row['params'];t=build_targets(raw,shadow,g,p,feat);eq=run(data,t,ex,bc,p['gross_cap'],None).equity;s=stats(eq);hold=stats(eq.loc[hs:]);holdv=stats(shadow.loc[hs:]);wr=(1+s['return'])/(1+v15['return']);hr=(1+hold['return'])/(1+holdv['return']);dr=abs(s['max_drawdown'])/abs(v15['max_drawdown']);worst=abs(s['worst_day'])/abs(v15['worst_day']);key=json.dumps(p,sort_keys=True);exact.append({**row,'summary':s,'wealth_ratio_to_v15':float(wr),'holdout_wealth_ratio':float(hr),'drawdown_ratio_to_v15':float(dr),'worst_day_ratio_to_v15':float(worst),'key':key});cache[key]=t
 exact.sort(key=lambda z:(z['holdout_wealth_ratio'],z['wealth_ratio_to_v15'],-z['drawdown_ratio_to_v15']),reverse=True);final=[];end=data.close.index[-1]
 for row in exact[:8]:
  p=row['params'];iso={};iv={};wins={};ddw={}
  for d in H:
   a,b=eval_slice(data,raw,ex,g,bg,bc,p,end-pd.Timedelta(days=d),end);iso[str(d)]=a;iv[str(d)]=b;wins[str(d)]=a['return']>=b['return'];ddw[str(d)]=abs(a['max_drawdown'])<=abs(b['max_drawdown'])
  sev=stats(run(data,cache[row['key']],ex,sc,p['gross_cap'],None).equity);sr=(1+sev['return'])/(1+v15sev['return']);gate=bool(all(wins.values()) and row['wealth_ratio_to_v15']>=1.30 and row['drawdown_ratio_to_v15']<=.75 and row['worst_day_ratio_to_v15']<=.80 and row['holdout_wealth_ratio']>=1.20 and sr>=1.15);final.append({**row,'isolated':iso,'isolated_v15':iv,'isolated_return_wins_vs_v15':wins,'isolated_drawdown_wins_vs_v15':ddw,'severe_cost':sev,'severe_wealth_ratio_to_v15':float(sr),'superior_gate_passed':gate})
 final.sort(key=lambda z:(z['superior_gate_passed'],sum(z['isolated_return_wins_vs_v15'].values()),z['holdout_wealth_ratio'],z['wealth_ratio_to_v15'],-z['drawdown_ratio_to_v15']),reverse=True);sel=final[0] if final else None;out={'study':'V99 R24 fast causal exposure frontier','status':'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER','screen_count':len(screened),'exact_count':len(exact),'v15':{'summary':v15,'severe_cost':v15sev},'selected':sel,'finalists':final,'top_approx':screen[:30],'disclosure':'Fast approximation is used only for screening; all finalists are rerun with exact execution. Historical research is not forward proof.','funding_quarantined_symbols':q,'v15_metadata':meta};REPORT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'study':out['study'],'screen_count':len(screened),'v15':out['v15'],'selected':sel},indent=2),flush=True)
if __name__=='__main__':main()
