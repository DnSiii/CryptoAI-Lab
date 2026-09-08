from __future__ import annotations
import gc,itertools,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from run_v99_r25_trisleeve_meta import cap
import run_v99_r37_crash_shield as r37
r37.r36.cap=cap;r36=r37.r36
REPORT=PROJECT/'reports'/'candidate_v99_r44_direct_hedge_frontier2.json';H=(7,30,90,180,365);ALT=(14,21,45,60,120,240,540)

def build(data,raw,ex,guard,gross,cost,p):
 shadow=r36.run(data,raw,ex,cost,gross,guard).equity;targets,active=r37.r30_targets(raw,shadow,data.close,p);res=r36.run(data,targets,ex,cost,p['gross_cap'],guard);return res,shadow,active

def iso(data,raw,ex,guard,gross,cost,p,start,end):
 d=r36.sdata(data,start,end);rr=raw.reindex(index=d.close.index,columns=d.close.columns).fillna(0);a,b,_=build(d,rr,ex,guard,gross,cost,p);return r36.stats(a.equity),r36.stats(b)

def main():
 cand,data,raw,ex,guard,gross,q,meta=r36.v15_setup();bc=float(ex['base_cost_per_side']);sc=float(ex['severe_cost_per_side']);v15=r36.run(data,raw,ex,bc,gross,guard).equity;v15s=r36.run(data,raw,ex,sc,gross,guard).equity
 v13c,v13d,v13t,v13e,v13k=r36.build_v13_benchmark();v14c,v14d,v14t,v14e,v14k=r36.build_v14_benchmark();v16c,v16d,v16t,v16e,v16k=r36.build_v16_benchmark();bench={'v13':{'candidate':v13c,'data':v13d,'targets':v13t,'execution':v13e,'kwargs':v13k},'v14':{'candidate':v14c,'data':v14d,'targets':v14t,'execution':v14e,'kwargs':v14k},'v15':{'candidate':cand,'data':data,'targets':raw,'execution':ex,'kwargs':{'maintenance_equity_fraction':ex['maintenance_equity_fraction'],'gross_guard_cap':gross,'drawdown_guard_threshold':guard['drawdown_threshold'],'drawdown_guard_multiplier':guard['exposure_multiplier'],'drawdown_guard_cooldown_hours':guard['cooldown_hours']}},'v16':{'candidate':v16c,'data':v16d,'targets':v16t,'execution':v16e,'kwargs':v16k}}
 fb={n:r36.exact_benchmark(x,float(x['execution']['base_cost_per_side'])) for n,x in bench.items()};sb={n:r36.exact_benchmark(x,float(x['execution']['severe_cost_per_side'])) for n,x in bench.items()};fe=r36.envelope(fb);se=r36.envelope(sb);split=int(len(v15)*.6);hs=v15.index[min(split+1,len(v15)-1)];v15h=r36.stats(v15.loc[hs:]);rows=[]
 for hedge,cool,minnet in itertools.product((.40,.50,.60),(72,96,120),(.05,.10,.20)):
  p={'dd_trigger':.06,'hedge_size':hedge,'cooldown':cool,'market_level':1,'min_net':minnet,'gross_cap':1.90};res,_,active=build(data,raw,ex,guard,gross,bc,p);s=r36.stats(res.equity);hold=r36.stats(res.equity.loc[hs:]);rr=(1+s['return'])/max(1e-12,1+fe['return']);hr=(1+hold['return'])/max(1e-12,1+v15h['return']);dr=abs(s['max_drawdown'])/max(1e-12,fe['max_drawdown_abs']);worst=abs(s['worst_day'])/max(1e-12,fe['worst_day_abs']);score=10*np.log(max(rr,1e-12))+4*np.log(max(hr,1e-12))+18*max(0,1-dr)-22*max(0,dr-1)+14*max(0,1-worst)-18*max(0,worst-1);rows.append({'params':p,'summary':s,'holdout':hold,'return_ratio_to_full_envelope':float(rr),'holdout_wealth_ratio_to_v15':float(hr),'drawdown_ratio_to_full_envelope':float(dr),'worst_day_ratio_to_full_envelope':float(worst),'hedge_active_fraction':float(active.mean()),'score':float(score)});gc.collect()
 rows.sort(key=lambda z:z['score'],reverse=True);end=min(x['data'].close.index[-1] for x in bench.values());earliest=max(x['data'].close.index[0] for x in bench.values());final=[]
 for row in rows[:9]:
  p=row['params'];isol={};iv15={};ib={};envs={};wins={};mat={}
  for days in H:
   start=end-pd.Timedelta(days=days);c,b=iso(data,raw,ex,guard,gross,bc,p,start,end);br={n:r36.exact_benchmark(x,float(x['execution']['base_cost_per_side']),start,end) for n,x in bench.items()};ev=r36.envelope(br);k=str(days);isol[k]=c;iv15[k]=b;ib[k]=br;envs[k]=ev;wins[k]={'return':c['return']>=ev['return'],'drawdown':abs(c['max_drawdown'])<=ev['max_drawdown_abs'],'worst_day':abs(c['worst_day'])<=ev['worst_day_abs']};mat[k]={'return':c['return']>=ev['return']+r36.metric_margin(ev['return']),'drawdown':abs(c['max_drawdown'])<=ev['max_drawdown_abs']*.95,'worst_day':abs(c['worst_day'])<=ev['worst_day_abs']*.95}
  alt={}
  for days in ALT:
   start=end-pd.Timedelta(days=days)
   if start<earliest:continue
   c,b=iso(data,raw,ex,guard,gross,bc,p,start,end);br={n:r36.exact_benchmark(x,float(x['execution']['base_cost_per_side']),start,end) for n,x in bench.items()};ev=r36.envelope(br);alt[str(days)]={'candidate':c,'v15':b,'envelope':ev,'return_win':c['return']>=ev['return'],'drawdown_win':abs(c['max_drawdown'])<=ev['max_drawdown_abs'],'worst_day_win':abs(c['worst_day'])<=ev['worst_day_abs']}
  sv,_,sa=build(data,raw,ex,guard,gross,sc,p);ss=r36.stats(sv.equity);fr=row['summary']['return']>=fe['return'];fk=abs(row['summary']['max_drawdown'])<=fe['max_drawdown_abs'] and abs(row['summary']['worst_day'])<=fe['worst_day_abs'];sr=ss['return']>=se['return'];sk=abs(ss['max_drawdown'])<=se['max_drawdown_abs'] and abs(ss['worst_day'])<=se['worst_day_abs'];aw=all(all(v.values()) for v in wins.values());am=all(all(v.values()) for v in mat.values());aa=bool(alt) and all(x['return_win'] and x['drawdown_win'] and x['worst_day_win'] for x in alt.values());dominant=bool(am and aa and fr and fk and row['holdout_wealth_ratio_to_v15']>=1.05 and sr and sk);final.append({**row,'isolated':isol,'isolated_v15':iv15,'isolated_benchmarks':ib,'isolated_envelope':envs,'envelope_wins':wins,'material_envelope_wins':mat,'alternative_horizons':alt,'all_envelope_dimensions_won':aw,'all_material_envelope_dimensions_won':am,'all_alternative_envelopes_won':aa,'severe_cost':ss,'severe_hedge_active_fraction':float(sa.mean()),'full_return_pass':fr,'full_risk_pass':fk,'severe_return_pass':sr,'severe_risk_pass':sk,'dominant_gate_passed':dominant});gc.collect()
 final.sort(key=lambda z:(z['dominant_gate_passed'],z['all_material_envelope_dimensions_won'],z['all_envelope_dimensions_won'],sum(sum(v.values()) for v in z['material_envelope_wins'].values()),sum(sum(v.values()) for v in z['envelope_wins'].values()),z['all_alternative_envelopes_won'],z['full_return_pass'],z['full_risk_pass'],z['holdout_wealth_ratio_to_v15'],-z['drawdown_ratio_to_full_envelope']),reverse=True);sel=final[0] if final else None
 out={'study':'V99 R44 direct hedge frontier II','status':'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER','objective':'spend part of R30 excess historical return on a locally stronger and more persistent direct opposite-net BTC hedge, without adding a new signal family','grid_policy':'27 local predeclared combinations around the proven R30 frontier: hedge 0.40/0.50/0.60 x cooldown 72/96/120h x minimum net 0.05/0.10/0.20; dd trigger 6%, market level 1 and gross cap 1.9 fixed','grid_size':len(rows),'common_end':end.isoformat(),'full_benchmarks':fb,'full_envelope':fe,'severe_benchmarks':sb,'severe_envelope':se,'selected':sel,'finalists':final,'all_screened':rows,'disclosure':'Historical research only. Direct-hedge conditions use causal shadow equity and market data known by close t, with target changes applied to the next-open replay. No real-order path is enabled. Any historical winner requires frozen forward paper.','funding_quarantined_symbols':q,'v15_metadata':meta};REPORT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'study':out['study'],'full_envelope':fe,'selected':sel},indent=2),flush=True)
if __name__=='__main__':main()
