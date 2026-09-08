from __future__ import annotations
import itertools,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import screen
from paper_once_v15 import build_v15
from run_v99_r25_trisleeve_meta import stats,sdata,cap,run
REPORT=PROJECT/'reports'/'candidate_v99_r31_risk_contribution.json';H=(7,30,90,180,365)

def build_targets(raw,close,p):
    vol=close.pct_change(fill_method=None).rolling(int(p['lookback']),min_periods=max(24,int(p['lookback'])//3)).std()*np.sqrt(24*365)
    active=raw.abs()>1e-12
    med=vol.where(active).median(axis=1).replace(0,np.nan)
    ratio=vol.rdiv(med,axis=0).pow(float(p['alpha'])).clip(lower=p['floor'],upper=p['ceiling']).fillna(1.0)
    scaled=raw*ratio
    oldg=raw.abs().sum(axis=1);newg=scaled.abs().sum(axis=1).replace(0,np.nan)
    scaled=scaled.mul((oldg/newg).replace([np.inf,-np.inf],np.nan).fillna(1.0),axis=0)
    scaled*=float(p['gross_multiplier'])
    return cap(scaled,p['gross_cap']),ratio

def slice_eval(data,targets,raw,ex,guard,cand_gross,base_gross,cost,start,end):
    d=sdata(data,start,end);t=targets.reindex(index=d.close.index,columns=d.close.columns).fillna(0.0);r=raw.reindex(index=d.close.index,columns=d.close.columns).fillna(0.0)
    return stats(run(d,t,ex,cost,cand_gross,guard).equity),stats(run(d,r,ex,cost,base_gross,guard).equity)

def main():
    cand,data,raw,_,_,q,meta=build_v15();v14=json.loads((PROJECT/'config'/cand['parent_candidate_config']).read_text());fin=json.loads((PROJECT/'config'/v14['frozen_core_config']).read_text());base=json.loads((PROJECT/'config'/fin['base_candidate_config']).read_text());ex=base['execution'];guard=v14['circuit_breaker'];bg=float(v14['allocation']['gross_drift_guard_cap']);bc=float(ex['base_cost_per_side']);sc=float(ex['severe_cost_per_side'])
    core=run(data,raw,ex,bc,bg,guard).equity;coresev=run(data,raw,ex,sc,bg,guard).equity;v15=stats(core);v15sev=stats(coresev);basescreen=stats(screen(data,raw,cost_per_side=bc).equity)
    rows=[];cache={};bounds=((.5,1.5),(.4,1.8),(.6,1.4))
    for lb,alpha,(floor,ceil),gm,gross in itertools.product((48,72,168,336),(.25,.50,.75,1.0),bounds,(1.0,1.10,1.20),(bg,1.90,2.10)):
        p={'lookback':lb,'alpha':alpha,'floor':floor,'ceiling':ceil,'gross_multiplier':gm,'gross_cap':gross};t,ratio=build_targets(raw,data.close,p);s=stats(screen(data,t,cost_per_side=bc).equity);wr=(1+s['return'])/max(1e-12,1+basescreen['return']);dr=abs(s['max_drawdown'])/max(1e-12,abs(basescreen['max_drawdown']));worst=abs(s['worst_day'])/max(1e-12,abs(basescreen['worst_day']));score=4*np.log(max(wr,1e-12))+5*max(0,1-dr)-6*max(0,dr-1)-2*max(0,worst-1);key=f"l{lb}_a{alpha:.2f}_f{floor:.1f}_c{ceil:.1f}_m{gm:.2f}_g{gross:.3f}";rows.append({'key':key,'params':p,'screen':s,'screen_wealth_ratio':float(wr),'screen_drawdown_ratio':float(dr),'screen_worst_day_ratio':float(worst),'mean_abs_risk_scale':float((ratio-1).abs().where(raw.abs()>1e-12).stack().mean()),'screen_score':float(score)});cache[key]=t
    rows.sort(key=lambda z:z['screen_score'],reverse=True);split=int(len(core)*.6);hs=core.index[min(split+1,len(core)-1)];vh=stats(core.loc[hs:]);exact=[]
    for row in rows[:40]:
        p=row['params'];eq=run(data,cache[row['key']],ex,bc,p['gross_cap'],guard).equity;s=stats(eq);ho=stats(eq.loc[hs:]);wr=(1+s['return'])/max(1e-12,1+v15['return']);hr=(1+ho['return'])/max(1e-12,1+vh['return']);dr=abs(s['max_drawdown'])/max(1e-12,abs(v15['max_drawdown']));worst=abs(s['worst_day'])/max(1e-12,abs(v15['worst_day']));score=5*np.log(max(wr,1e-12))+4*np.log(max(hr,1e-12))+5*max(0,1-dr)-7*max(0,dr-1)-3*max(0,worst-1);exact.append({**row,'summary':s,'holdout':ho,'wealth_ratio_to_v15':float(wr),'holdout_wealth_ratio_to_v15':float(hr),'drawdown_ratio_to_v15':float(dr),'worst_day_ratio_to_v15':float(worst),'exact_score':float(score)})
    exact.sort(key=lambda z:z['exact_score'],reverse=True);final=[];end=data.close.index[-1]
    for row in exact[:10]:
        p=row['params'];t=cache[row['key']];iso={};iv={};rw={};dw={};ww={};pw={}
        for days in H:
            a,b=slice_eval(data,t,raw,ex,guard,p['gross_cap'],bg,bc,end-pd.Timedelta(days=days),end);k=str(days);iso[k]=a;iv[k]=b;rw[k]=a['return']>=b['return'];dw[k]=abs(a['max_drawdown'])<=abs(b['max_drawdown']);ww[k]=abs(a['worst_day'])<=abs(b['worst_day']);pw[k]=a['positive_days']>=b['positive_days']
        ss=stats(run(data,t,ex,sc,p['gross_cap'],guard).equity);sr=(1+ss['return'])/max(1e-12,1+v15sev['return']);gate=bool(all(rw.values()) and all(dw.values()) and all(ww.values()) and row['wealth_ratio_to_v15']>=1.50 and row['holdout_wealth_ratio_to_v15']>=1.25 and row['drawdown_ratio_to_v15']<=.70 and row['worst_day_ratio_to_v15']<=.75 and sr>=1.25);final.append({**row,'isolated':iso,'isolated_v15':iv,'isolated_return_wins_vs_v15':rw,'isolated_drawdown_wins_vs_v15':dw,'isolated_worst_day_wins_vs_v15':ww,'isolated_positive_days_wins_vs_v15':pw,'severe_cost':ss,'severe_wealth_ratio_to_v15':float(sr),'superior_gate_passed':gate})
    final.sort(key=lambda z:(z['superior_gate_passed'],sum(z['isolated_return_wins_vs_v15'].values()),sum(z['isolated_drawdown_wins_vs_v15'].values()),z['holdout_wealth_ratio_to_v15'],z['wealth_ratio_to_v15'],-z['drawdown_ratio_to_v15']),reverse=True);sel=final[0] if final else None
    out={'study':'V99 R31 cross-sectional risk contribution rebalance','status':'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER','objective':'redistribute the same V15 gross budget away from extremely volatile active positions and toward lower-volatility active positions, with modest gross scaling only when risk balance supports it','screen_grid_size':len(rows),'exact_screen_size':len(exact),'v15':{'summary':v15,'severe_cost':v15sev},'selected':sel,'finalists':final,'top_exact':exact[:25],'top_screen':rows[:50],'disclosure':'Historical research only. Volatility estimates use trailing data available at close t; targets execute at open t+1. Screen is ranking-only; exact replay, isolated windows, holdout and severe costs control promotion.','funding_quarantined_symbols':q,'v15_metadata':meta};REPORT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'study':out['study'],'screen_grid_size':len(rows),'exact_screen_size':len(exact),'v15':out['v15'],'selected':sel},indent=2),flush=True)
if __name__=='__main__':main()
