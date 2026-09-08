from __future__ import annotations
import itertools, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import screen
from paper_once_v15 import build_v15
from run_v99_r25_trisleeve_meta import stats,sdata,cap,run

REPORT=PROJECT/'reports'/'candidate_v99_r30_direct_hedge.json';H=(7,30,90,180,365)

def stress_mask(shadow,btc,p):
    dd=shadow/shadow.cummax()-1
    th=-abs(p['dd_trigger'])
    cross=(dd<=th)&(dd.shift(1).fillna(0)>th)
    r24=btc.pct_change(24,fill_method=None);r72=btc.pct_change(72,fill_method=None)
    if p['market_level']==1: shock=(r24<=-.025)|(r72<=-.05)
    elif p['market_level']==2: shock=(r24<=-.035)|(r72<=-.07)
    else: shock=(r24<=-.045)|(r72<=-.09)
    raw=(cross|shock.fillna(False)).astype(float)
    return raw.rolling(int(p['cooldown']),min_periods=1).max().gt(0)

def hedge_targets(raw,shadow,close,p):
    active=stress_mask(shadow,close['BTCUSDT'],p)
    net=raw.sum(axis=1)
    direction=-np.sign(net)
    direction=direction.where(net.abs()>=p['min_net'],0.0)
    out=raw.copy()
    if 'BTCUSDT' not in out.columns: raise RuntimeError('BTCUSDT missing from V15 universe')
    out['BTCUSDT']=out['BTCUSDT']+active.astype(float)*direction*p['hedge_size']
    return cap(out,p['gross_cap']),active,direction

def exact_candidate(data,raw,ex,guard,base_gross,cost,p):
    shadow=run(data,raw,ex,cost,base_gross,guard).equity
    targets,active,direction=hedge_targets(raw,shadow,data.close,p)
    eq=run(data,targets,ex,cost,p['gross_cap'],guard).equity
    return eq,shadow,targets,active,direction

def slice_eval(data,raw,ex,guard,base_gross,cost,p,start,end):
    d=sdata(data,start,end);r=raw.reindex(index=d.close.index,columns=d.close.columns).fillna(0.0)
    eq,sh,_,_,_=exact_candidate(d,r,ex,guard,base_gross,cost,p)
    return stats(eq),stats(sh)

def main():
    cand,data,raw,_,_,q,meta=build_v15();v14=json.loads((PROJECT/'config'/cand['parent_candidate_config']).read_text());fin=json.loads((PROJECT/'config'/v14['frozen_core_config']).read_text());base=json.loads((PROJECT/'config'/fin['base_candidate_config']).read_text());ex=base['execution'];guard=v14['circuit_breaker'];bg=float(v14['allocation']['gross_drift_guard_cap']);bc=float(ex['base_cost_per_side']);sc=float(ex['severe_cost_per_side'])
    core=run(data,raw,ex,bc,bg,guard).equity;coresev=run(data,raw,ex,sc,bg,guard).equity;v15=stats(core);v15sev=stats(coresev)
    base_screen=stats(screen(data,raw,cost_per_side=bc).equity);rows=[];cache={}
    for dd,hsize,cool,ml,minnet,gross in itertools.product((.06,.08,.10),(.25,.40,.55),(24,48,72),(1,2,3),(.10,.25),(1.90,2.20)):
        p={'dd_trigger':dd,'hedge_size':hsize,'cooldown':cool,'market_level':ml,'min_net':minnet,'gross_cap':gross}
        t,active,direction=hedge_targets(raw,core,data.close,p);eq=screen(data,t,cost_per_side=bc).equity;s=stats(eq);wr=(1+s['return'])/max(1e-12,1+base_screen['return']);dr=abs(s['max_drawdown'])/max(1e-12,abs(base_screen['max_drawdown']));worst=abs(s['worst_day'])/max(1e-12,abs(base_screen['worst_day']));score=4*np.log(max(wr,1e-12))+5*max(0,1-dr)-6*max(0,dr-1)-3*max(0,worst-1)
        key=f"d{dd:.2f}_h{hsize:.2f}_c{cool}_m{ml}_n{minnet:.2f}_g{gross:.1f}";rows.append({'key':key,'params':p,'screen':s,'screen_wealth_ratio':float(wr),'screen_drawdown_ratio':float(dr),'screen_worst_day_ratio':float(worst),'hedge_active_fraction':float(active.mean()),'screen_score':float(score)});cache[key]=t
    rows.sort(key=lambda z:z['screen_score'],reverse=True);split=int(len(core)*.6);hs=core.index[min(split+1,len(core)-1)];vh=stats(core.loc[hs:]);exact=[]
    for row in rows[:36]:
        p=row['params'];eq=run(data,cache[row['key']],ex,bc,p['gross_cap'],guard).equity;s=stats(eq);ho=stats(eq.loc[hs:]);wr=(1+s['return'])/max(1e-12,1+v15['return']);hr=(1+ho['return'])/max(1e-12,1+vh['return']);dr=abs(s['max_drawdown'])/max(1e-12,abs(v15['max_drawdown']));worst=abs(s['worst_day'])/max(1e-12,abs(v15['worst_day']));score=5*np.log(max(wr,1e-12))+4*np.log(max(hr,1e-12))+5*max(0,1-dr)-7*max(0,dr-1)-3*max(0,worst-1);exact.append({**row,'summary':s,'holdout':ho,'wealth_ratio_to_v15':float(wr),'holdout_wealth_ratio_to_v15':float(hr),'drawdown_ratio_to_v15':float(dr),'worst_day_ratio_to_v15':float(worst),'exact_score':float(score)})
    exact.sort(key=lambda z:z['exact_score'],reverse=True);final=[];end=data.close.index[-1]
    for row in exact[:8]:
        p=row['params'];iso={};iv={};rw={};dw={};ww={};pw={}
        for days in H:
            a,b=slice_eval(data,raw,ex,guard,bg,bc,p,end-pd.Timedelta(days=days),end);k=str(days);iso[k]=a;iv[k]=b;rw[k]=a['return']>=b['return'];dw[k]=abs(a['max_drawdown'])<=abs(b['max_drawdown']);ww[k]=abs(a['worst_day'])<=abs(b['worst_day']);pw[k]=a['positive_days']>=b['positive_days']
        sev,_,_,_,_=exact_candidate(data,raw,ex,guard,bg,sc,p);ss=stats(sev);sr=(1+ss['return'])/max(1e-12,1+v15sev['return']);gate=bool(all(rw.values()) and all(dw.values()) and all(ww.values()) and row['wealth_ratio_to_v15']>=1.50 and row['holdout_wealth_ratio_to_v15']>=1.25 and row['drawdown_ratio_to_v15']<=.70 and row['worst_day_ratio_to_v15']<=.75 and sr>=1.25);final.append({**row,'isolated':iso,'isolated_v15':iv,'isolated_return_wins_vs_v15':rw,'isolated_drawdown_wins_vs_v15':dw,'isolated_worst_day_wins_vs_v15':ww,'isolated_positive_days_wins_vs_v15':pw,'severe_cost':ss,'severe_wealth_ratio_to_v15':float(sr),'superior_gate_passed':gate})
    final.sort(key=lambda z:(z['superior_gate_passed'],sum(z['isolated_return_wins_vs_v15'].values()),sum(z['isolated_drawdown_wins_vs_v15'].values()),z['holdout_wealth_ratio_to_v15'],z['wealth_ratio_to_v15'],-z['drawdown_ratio_to_v15']),reverse=True);sel=final[0] if final else None
    out={'study':'V99 R30 direct net-beta hedge','status':'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER','objective':'preserve V15 positions while adding a temporary BTC hedge opposite net target exposure during causal stress events','screen_grid_size':len(rows),'exact_screen_size':len(exact),'v15':{'summary':v15,'severe_cost':v15sev},'selected':sel,'finalists':final,'top_exact':exact[:20],'top_screen':rows[:40],'disclosure':'Historical research only. Hedge decisions use only information known by close t and execute at the next open. Screen is ranking-only; exact replay, isolated horizons, holdout, and severe costs determine the gate.','funding_quarantined_symbols':q,'v15_metadata':meta};REPORT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'study':out['study'],'screen_grid_size':len(rows),'exact_screen_size':len(exact),'v15':out['v15'],'selected':sel},indent=2),flush=True)
if __name__=='__main__':main()
