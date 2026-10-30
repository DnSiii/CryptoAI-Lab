from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
import v98_independent_phase111_stablecoin_peg_feasibility as p111
CFG=PROJECT/'config'/'v98_independent.json'; OUT=PROJECT/'reports'/'v98_independent_phase112_stablecoin_confidence_regime.json'; POS=PROJECT/'reports'/'v98_independent_phase112_stablecoin_confidence_regime_positions.csv'
PREREG='reports/v98_independent_phase112_stablecoin_confidence_regime_prereg.md'; GROSS=.75; THRESH=.005
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT']

def histories():
    ms,mraw,merr=p111.get(p111.META); hs,hraw,herr=p111.get(p111.HIST)
    if ms!=200 or hs!=200: raise RuntimeError(f'phase111 source unavailable: {ms}/{hs} {merr}/{herr}')
    meta=json.loads(mraw); hist=json.loads(hraw); assets=meta['peggedAssets']; out={}
    for sym in p111.SYMS:
        m=[x for x in assets if str(x.get('symbol','')).upper()==sym]
        if len(m)!=1 or not m[0].get('gecko_id'): raise RuntimeError(f'unresolved {sym}')
        df,parse=p111.canonical_history(hist,m[0]['gecko_id'])
        if not parse['schema_ok']: raise RuntimeError(f'schema failure {sym}')
        s=pd.Series(pd.to_numeric(df.price,errors='coerce').values,index=pd.to_datetime(df.date_norm,utc=True),name=sym).sort_index()
        out[sym]=s
    return out,{'metadata_sha256':hashlib.sha256(mraw).hexdigest(),'history_sha256':hashlib.sha256(hraw).hexdigest()}

def build_targets(data,h):
    daily=pd.concat(h,axis=1).sort_index(); stress=(daily.sub(1.).abs().max(axis=1)).shift(1)
    t=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns); events=t.index.hour==0
    regimes=[]
    for ts in t.index[events]:
        v=stress.get(ts.normalize(),np.nan)
        if not np.isfinite(v): continue
        side=1. if v<=THRESH else -1.; t.loc[ts,ASSETS]=side*GROSS/len(ASSETS); regimes.append((ts.normalize(),float(v),'healthy' if side>0 else 'stress'))
    return t.where(pd.Series(events,index=t.index),np.nan).ffill().fillna(0.),pd.DataFrame(regimes,columns=['date','lagged_stress','regime'])

def always_long(data):
    t=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns); events=t.index.hour==0; t.loc[events,ASSETS]=GROSS/len(ASSETS)
    return t.where(pd.Series(events,index=t.index),np.nan).ffill().fillna(0.)

def ev(data,t,cfg,s):
    f=cfg['funding_stress'][s]
    return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=GROSS,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])

def tails(r,a,b):
    d=r.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna(); den=float(d.abs().sum()); ad=d.abs().sort_values(ascending=False)
    return {'top10_absolute_day_share':float(ad.head(10).sum()/den) if den else 0.,'worst10_sum':float(d.nsmallest(10).sum()),'best10_sum':float(d.nlargest(10).sum())}

def contribution(data,t,a,b):
    x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,ASSETS].sum().fillna(0.); den=float(x.abs().sum())
    return {'pre_cost_position_return_sum':{k:float(v) for k,v in x.items()},'absolute_contribution_share':{k:(float(abs(v)/den) if den else 0.) for k,v in x.items()}}

def main():
    cfg=json.loads(CFG.read_text()); data=load_data(PROJECT,cfg['data_config']); v=validate_data(data)
    if v['errors']: raise RuntimeError(str(v['errors'][:5]))
    h,src=histories(); t,reg=build_targets(data,h); a=cfg['folds'][0]['start']; b=cfg['training_end']
    rr={s:ev(data,t,cfg,s) for s in ('base','severe','supersevere')}; base=rr['base']; train=p3.metrics(base,a,b); folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']}; stress={s:p3.metrics(rr[s],a,b) for s in ('severe','supersevere')}
    con=contribution(data,t,a,b); tail=tails(base,a,b); rg=reg[(reg.date>=pd.Timestamp(a))&(reg.date<=pd.Timestamp(b))].regime.value_counts().to_dict()
    op=base.open_positions.loc[a:b].abs().sum(axis=1) if base.open_positions is not None else pd.Series(dtype=float); maxopen=float(op.max()) if len(op) else 0.
    bench=ev(data,always_long(data),cfg,'base'); benchmark=p3.metrics(bench,a,b)
    fail=[]
    if train['total_return']<=0: fail.append('aggregate_return<=0')
    if train['profit_factor_daily']<=1.10: fail.append('aggregate_pf<=1.10')
    if train['max_drawdown']<-.35: fail.append('max_drawdown<-35%')
    if train['worst_day']<-.12: fail.append('worst_day<-12%')
    for n,m in folds.items():
        if m['total_return']<=0: fail.append(f'{n}_return<=0')
        if m['profit_factor_daily']<=1.02: fail.append(f'{n}_pf<=1.02')
    for s in ('severe','supersevere'):
        if stress[s]['total_return']<=0 or stress[s]['profit_factor_daily']<=1.: fail.append(f'{s}_gate')
    if max(con['absolute_contribution_share'].values(),default=0)>0.45: fail.append('single_asset_contribution>45%')
    if tail['top10_absolute_day_share']>0.60: fail.append('top10_absolute_day_share>60%')
    if maxopen>GROSS+1e-9: fail.append('max_open_gross>0.75')
    if rg.get('healthy',0)==0 or rg.get('stress',0)==0: fail.append('both_regimes_not_identified')
    rep={'engine':'V98 Independent','phase':'112','hypothesis':'stablecoin confidence regime','preregistration':PREREG,'parameters':{'threshold':THRESH,'gross':GROSS,'assets':ASSETS,'lag':'strict D-1 UTC','healthy':'long','stress':'short'},'source':src,'training':train,'folds':folds,'stress_training':stress,'regime_observation_counts':rg,'regimes_training':p3.regime_metrics(base,data,a,b,b),'concentration_training':p3.concentration_metrics(base,a,b),'asset_contribution_proxy':con,'tails_training':tail,'execution_guard_audit':{'max_open_gross':maxopen,'cap':GROSS},'always_long_context_benchmark':benchmark,'reproducibility':{'targets_sha256':hashlib.sha256(t.loc[a:b,ASSETS].to_csv().encode()).hexdigest(),'prereg_sha256':hashlib.sha256((PROJECT/PREREG).read_bytes()).hexdigest()},'training_gate':{'passed':not fail,'decision':'PASS_TRAINING' if not fail else 'REJECT_NO_RESCUE','failures':fail},'validation':None,'final_holdout':None,'phase083_selection_use':False,'future_holdout_required':True,'v99_used':False,'v16_used':False,'parameter_search':False,'rescue_allowed':False}
    OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n'); base.positions.to_csv(POS); print(json.dumps(rep,indent=2,default=str))
if __name__=='__main__': main()
