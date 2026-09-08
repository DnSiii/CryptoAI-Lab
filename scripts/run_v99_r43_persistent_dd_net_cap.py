from __future__ import annotations

import gc,itertools,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from run_v99_r25_trisleeve_meta import cap
import run_v99_r42_adaptive_net_neutralizer as r42
r37=r42.r37;r36=r42.r36;r37.r36.cap=cap
REPORT=PROJECT/'reports'/'candidate_v99_r43_persistent_dd_net_cap.json';H=(7,30,90,180,365);ALT=(14,21,45,60,120,240,540)

def persistent_state(equity,p):
 eq=equity.astype(float);dd=eq/eq.cummax()-1;r24=eq.pct_change(24,fill_method=None).fillna(0);r72=eq.pct_change(72,fill_method=None).fillna(0);active=pd.Series(False,index=eq.index);on=False
 for i,t in enumerate(eq.index):
  if not on:
   if dd.iloc[i]<=-p['enter_dd'] and (r24.iloc[i]<=p['enter_r24'] or r72.iloc[i]<=p['enter_r72']):on=True
  else:
   if dd.iloc[i]>=-p['exit_dd'] and r24.iloc[i]>=0:on=False
  active.iloc[i]=on
 return active,{'active_fraction':float(active.mean()),'episodes':int((active.astype(int).diff().fillna(active.astype(int)).eq(1)).sum()),'minimum_shadow_dd':float(dd.min())}

def build_candidate(data,raw,ex,guard,gross,cost,p):
 base,bt,_=r37.build_r30(data,raw,ex,guard,gross,cost);active,diag=persistent_state(base.equity,p);net=bt.sum(axis=1);excess=(net.abs()-p['target_net']).clip(lower=0,upper=p['max_extra']);hedge=-np.sign(net)*excess*active.astype(float);targets=bt.copy();targets['BTCUSDT']=targets['BTCUSDT']+hedge;targets=cap(targets,p['gross_cap']);res=r36.run(data,targets,ex,cost,p['gross_cap'],guard);diag['mean_extra_hedge']=float(hedge.abs().mean());diag['p95_extra_hedge']=float(hedge.abs().quantile(.95));diag['max_extra_hedge']=float(hedge.abs().max());return res,base,active,diag

def iso(data,raw,ex,guard,gross,cost,p,start,end):
 d=r36.sdata(data,start,end);rr=raw.reindex(index=d.close.index,columns=d.close.columns).fillna(0);a,b,_,_=build_candidate(d,rr,ex,guard,gross,cost,p);return r36.stats(a.equity),r36.stats(b.equity)

def main():
 cand,data,raw,ex,guard,gross,q,meta=r36.v15_setup();bc=float(ex['base_cost_per_side']);sc=float(ex['severe_cost_per_side']);r30,_,r30active=r37.build_r30(data,raw,ex,guard,gross,bc);r30s,_,_=r37.build_r30(data,raw,ex,guard,gross,sc);rs=r36.stats(r30.equity);rss=r36.stats(r30s.equity)
 v13c,v13d,v13t,v13e,v13k=r36.build_v13_benchmark();v14c,v14d,v14t,v14e,v14k=r36.build_v14_benchmark();v16c,v16d,v16t,v16e,v16k=r36.build_v16_benchmark();bench={'v13':{'candidate':v13c,'data':v13d,'targets':v13t,'execution':v13e,'kwargs':v13k},'v14':{'candidate':v14c,'data':v14d,'targets':v14t,'execution':v14e,'kwargs':v14k},'v15':{'candidate':cand,'data':data,'targets':raw,'execution':ex,'kwargs':{'maintenance_equity_fraction':ex['maintenance_equity_fraction'],'gross_guard_cap':gross,'drawdown_guard_threshold':guard['drawdown_threshold'],'drawdown_guard_multiplier':guard['exposure_multiplier'],'drawdown_guard_cooldown_hours':guard['cooldown_hours']}},'v16':{'candidate':v16c,'data':v16d,'targets':v16t,'execution':v16e,'kwargs':v16k}}
 fb={n:r36.exact_benchmark(x,float(x['execution']['base_cost_per_side'])) for n,x in bench.items()};sb={n:r36.exact_benchmark(x,float(x['execution']['severe_cost_per_side'])) for n,x in bench.items()};fe=r36.envelope(fb);se=r36.envelope(sb);split=int(len(r30.equity)*.6);hs=r30.equity.index[min(split+1,len(r30.equity)-1)];rh=r36.stats(r30.equity.loc[hs:]);rows=[]
 for enter,target,max_extra in itertools.product((.06,.08,.10),(.40,.60,.80),(.30,.50,.70)):
  p={'enter_dd':enter,'exit_dd':enter*.45,'enter_r24':-.01,'enter_r72':-.02,'target_net':target,'max_extra':max_extra,'gross_cap':1.90};res,_,active,diag=build_candidate(data,raw,ex,guard,gross,bc,p);s=r36.stats(res.equity);hold=r36.stats(res.equity.loc[hs:]);wr=(1+s['return'])/max(1e-12,1+rs['return']);hr=(1+hold['return'])/max(1e-12,1+rh['return']);rr=(1+s['return'])/max(1e-12,1+fe['return']);dr=abs(s['max_drawdown'])/max(1e-12,fe['max_drawdown_abs']);worst=abs(s['worst_day'])/max(1e-12,fe['worst_day_abs']);score=9*np.log(max(rr,1e-12))+5*np.log(max(hr,1e-12))+16*max(0,1-dr)-20*max(0,dr-1)+10*max(0,1-worst)-14*max(0,worst-1);rows.append({'params':p,'summary':s,'holdout':hold,'wealth_ratio_to_r30':float(wr),'holdout_wealth_ratio_to_r30':float(hr),'return_ratio_to_full_envelope':float(rr),'drawdown_ratio_to_full_envelope':float(dr),'worst_day_ratio_to_full_envelope':float(worst),'active_fraction':float(active.mean()),'state_diagnostics':diag,'score':float(score)});gc.collect()
 rows.sort(key=lambda z:z['score'],reverse=True);end=min(x['data'].close.index[-1] for x in bench.values());earliest=max(x['data'].close.index[0] for x in bench.values());final=[]
 for row in rows[:9]:
  p=row['params'];isol={};ir30={};ib={};envs={};wins={};mat={}
  for days in H:
   start=end-pd.Timedelta(days=days);c,rb=iso(data,raw,ex,guard,gross,bc,p,start,end);br={n:r36.exact_benchmark(x,float(x['execution']['base_cost_per_side']),start,end) for n,x in bench.items()};ev=r36.envelope(br);k=str(days);isol[k]=c;ir30[k]=rb;ib[k]=br;envs[k]=ev;wins[k]={'return':c['return']>=ev['return'],'drawdown':abs(c['max_drawdown'])<=ev['max_drawdown_abs'],'worst_day':abs(c['worst_day'])<=ev['worst_day_abs']};mat[k]={'return':c['return']>=ev['return']+r36.metric_margin(ev['return']),'drawdown':abs(c['max_drawdown'])<=ev['max_drawdown_abs']*.95,'worst_day':abs(c['worst_day'])<=ev['worst_day_abs']*.95}
  alt={}
  for days in ALT:
   start=end-pd.Timedelta(days=days)
   if start<earliest:continue
   c,rb=iso(data,raw,ex,guard,gross,bc,p,start,end);br={n:r36.exact_benchmark(x,float(x['execution']['base_cost_per_side']),start,end) for n,x in bench.items()};ev=r36.envelope(br);alt[str(days)]={'candidate':c,'r30':rb,'envelope':ev,'return_win':c['return']>=ev['return'],'drawdown_win':abs(c['max_drawdown'])<=ev['max_drawdown_abs'],'worst_day_win':abs(c['worst_day'])<=ev['worst_day_abs']}
  sv,_,sa,sd=build_candidate(data,raw,ex,guard,gross,sc,p);ss=r36.stats(sv.equity);fr=row['summary']['return']>=fe['return'];fk=abs(row['summary']['max_drawdown'])<=fe['max_drawdown_abs'] and abs(row['summary']['worst_day'])<=fe['worst_day_abs'];sr=ss['return']>=se['return'];sk=abs(ss['max_drawdown'])<=se['max_drawdown_abs'] and abs(ss['worst_day'])<=se['worst_day_abs'];aw=all(all(v.values()) for v in wins.values());am=all(all(v.values()) for v in mat.values());aa=bool(alt) and all(x['return_win'] and x['drawdown_win'] and x['worst_day_win'] for x in alt.values());dominant=bool(am and aa and fr and fk and row['holdout_wealth_ratio_to_r30']>=1.02 and sr and sk);final.append({**row,'isolated':isol,'isolated_r30':ir30,'isolated_benchmarks':ib,'isolated_envelope':envs,'envelope_wins':wins,'material_envelope_wins':mat,'alternative_horizons':alt,'all_envelope_dimensions_won':aw,'all_material_envelope_dimensions_won':am,'all_alternative_envelopes_won':aa,'severe_cost':ss,'severe_active_fraction':float(sa.mean()),'severe_state_diagnostics':sd,'full_return_pass':fr,'full_risk_pass':fk,'severe_return_pass':sr,'severe_risk_pass':sk,'dominant_gate_passed':dominant});gc.collect()
 final.sort(key=lambda z:(z['dominant_gate_passed'],z['all_material_envelope_dimensions_won'],z['all_envelope_dimensions_won'],sum(sum(v.values()) for v in z['material_envelope_wins'].values()),sum(sum(v.values()) for v in z['envelope_wins'].values()),z['all_alternative_envelopes_won'],z['full_return_pass'],z['full_risk_pass'],z['holdout_wealth_ratio_to_r30'],-z['drawdown_ratio_to_full_envelope']),reverse=True);sel=final[0] if final else None
 out={'study':'V99 R43 persistent drawdown net cap','status':'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER','objective':'retain fixed defensive R30 and, only when its shadow equity enters a persistent drawdown with negative 24h/72h momentum, maintain a hysteretic opposite-net BTC adjustment until partial recovery so long loss sequences cannot carry excessive beta','r41_basis':'R30 maximum drawdown lasted 3318h with existing R30 hedge active ~71%; second major episode lasted 1428h with hedge active ~56%, indicating sequence risk rather than one-day crash risk','grid_policy':'27 predeclared combinations = 3 drawdown entries x 3 target net caps x 3 maximum adaptive hedge bounds; exit hysteresis fixed at 45% of entry DD','r30_fixed_base':r37.R30_BASE,'r30_base_summary':rs,'r30_base_severe':rss,'r30_hedge_active_fraction':float(r30active.mean()),'grid_size':len(rows),'common_end':end.isoformat(),'full_benchmarks':fb,'full_envelope':fe,'severe_benchmarks':sb,'severe_envelope':se,'selected':sel,'finalists':final,'all_screened':rows,'disclosure':'Historical research only. Shadow-equity drawdown and momentum use information available at close t and change only next-open requested targets. State is independent of candidate realized equity to avoid reflexive look-ahead. No real-order path is enabled. Any historical winner requires frozen forward paper.','funding_quarantined_symbols':q,'v15_metadata':meta};REPORT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'study':out['study'],'r30':rs,'full_envelope':fe,'selected':sel},indent=2),flush=True)
if __name__=='__main__':main()
