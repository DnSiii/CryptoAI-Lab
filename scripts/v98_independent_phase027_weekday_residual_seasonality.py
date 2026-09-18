from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT/'src')); sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,point_in_time_liquid_view,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CONFIG_PATH=PROJECT/'config'/'v98_independent.json'; STATE_PATH=PROJECT/'state'/'v98_independent_state.json'; REPORT_PATH=PROJECT/'reports'/'v98_independent_phase027_weekday_residual_seasonality.json'; POSITIONS_PATH=PROJECT/'reports'/'v98_independent_phase027_weekday_residual_seasonality_positions.csv'
PHASE={'id':'phase_027_weekday_residual_seasonality','liquidity_top_n':10,'liquidity_lookback_hours':720,'minimum_history_hours':2160,'beta_lookback_hours':720,'same_weekday_observations':26,'minimum_same_weekday_observations':13,'rebalance_hours':24,'gross_target':0.75,'gross_cap':0.75}
def build_targets(data,membership):
    c=PHASE; close=data.close; lag=close.shift(1); eligible=(membership & close.notna()).copy(); eligible['BTCUSDT']=False
    hourly=lag.pct_change(fill_method=None); btc=hourly['BTCUSDT']; var=btc.rolling(c['beta_lookback_hours'],min_periods=360).var(); beta=hourly.rolling(c['beta_lookback_hours'],min_periods=360).cov(btc).div(var,axis=0)
    residual=hourly.sub(beta.mul(btc,axis=0)); daily_resid=residual.rolling(24,min_periods=24).sum()
    targets=pd.DataFrame(np.nan,index=close.index,columns=close.columns); events=(targets.index.hour==0); event_idx=targets.index[events]
    for ts in event_idx:
        hist_idx=event_idx[(event_idx<ts) & (event_idx.weekday==ts.weekday())][-c['same_weekday_observations']:]
        if len(hist_idx)<c['minimum_same_weekday_observations']: continue
        exp=daily_resid.loc[hist_idx].mean(axis=0); ok=eligible.loc[ts] & exp.notna() & beta.loc[ts].notna(); names=ok.index[ok]
        if len(names)<4: continue
        score=exp.loc[names].rank(pct=True).sub(0.5); y=score.to_numpy(float); b=beta.loc[ts,names].to_numpy(float); x=np.column_stack([np.ones(len(names)),b]); coef,*_=np.linalg.lstsq(x,y,rcond=None); neutral=y-x@coef; gross=float(np.abs(neutral).sum()); row=pd.Series(0.0,index=targets.columns)
        if np.isfinite(gross) and gross>1e-12: row.loc[names]=neutral*(c['gross_target']/gross)
        targets.loc[ts]=row
    targets=targets.ffill().fillna(0.0); gross=targets.abs().sum(axis=1); return targets.mul((c['gross_cap']/gross.replace(0,np.nan)).clip(upper=1).fillna(0),axis=0)
def ev(data,t,cfg,s):
    f=cfg['funding_stress'][s]; return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=PHASE['gross_cap'],funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def main():
    cfg=json.loads(CONFIG_PATH.read_text()); state=json.loads(STATE_PATH.read_text()); data=load_data(PROJECT,cfg['data_config']); v=validate_data(data)
    if v['errors']: raise RuntimeError(str(v['errors'][:5]))
    liquid,membership=point_in_time_liquid_view(data,top_n=PHASE['liquidity_top_n'],lookback_hours=PHASE['liquidity_lookback_hours'],minimum_history_hours=PHASE['minimum_history_hours']); t=build_targets(liquid,membership); r={s:ev(liquid,t,cfg,s) for s in ('base','severe','supersevere')}; a,b=cfg['research_start'],cfg['training_end']; train=p3.metrics(r['base'],a,b); folds={f['name']:p3.metrics(r['base'],f['start'],f['end']) for f in cfg['folds']}; sev=p3.metrics(r['severe'],a,b); sup=p3.metrics(r['supersevere'],a,b); conc=p3.concentration_metrics(r['base'],a,b); beta_n=p3.beta_neutrality_metrics(r['base'],liquid,a,b); regimes=p3.regime_metrics(r['base'],liquid,a,b,b); passed,failures=p3.training_gate(train,folds,sev,sup,conc)
    hyp='Same-UTC-weekday lagged residual return history may capture recurring cross-sectional flow seasonality with low turnover.'; report={'engine':'V98 Independent','phase':PHASE,'hypothesis':hyp,'preregistration':'reports/v98_independent_phase027_preregistration.md','selection_policy':'single fixed weekday-seasonality specification; no weekday/lookback/sign/cadence/regime/leverage search; validation only if training passes; final holdout untouched','training':train,'folds':folds,'stress_training':{'severe':sev,'supersevere':sup},'concentration_training':conc,'beta_neutrality_training':beta_n,'regimes_training':regimes,'training_gate':{'passed':passed,'failures':failures},'validation':None,'final_holdout':None}
    if passed:
        v0,v1=cfg['validation_start'],cfg['validation_end']; vb=p3.metrics(r['base'],v0,v1); vs=p3.metrics(r['severe'],v0,v1); vss=p3.metrics(r['supersevere'],v0,v1); vp,vf=p3.holdout_gate(vb,vs,vss); report['validation']={'base':vb,'severe':vs,'supersevere':vss,'gate':{'passed':vp,'failures':vf}}
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True); REPORT_PATH.write_text(json.dumps(report,indent=2,default=str)+'\n'); r['base'].positions.to_csv(POSITIONS_PATH); validation_pass=bool(passed and report['validation'] and report['validation']['gate']['passed']); state['phase']='phase_027_complete'; state['last_experiment']={'id':PHASE['id'],'hypothesis':hyp,'status':'frozen_pending_final_holdout' if validation_pass else ('training_passed_validation_rejected' if passed else 'training_rejected'),'parameters':'preregistered same-weekday last-26 residual observations, min 13; daily 00UTC rebalance; 0.75 gross; beta/dollar neutral','report':str(REPORT_PATH.relative_to(PROJECT)),'training_summary':train,'folds':folds,'stress_training':report['stress_training'],'training_gate':report['training_gate'],'validation':report['validation'],'final_holdout_opened':False}; state['champion']=PHASE['id'] if validation_pass else state.get('champion'); state['final_holdout_untouched']=True; state['next_action']='If Phase027 passes training+validation, freeze before one-shot final holdout. If rejected, close weekday seasonality without weekday/lookback/sign rescue and move to another orthogonal alpha.'; STATE_PATH.write_text(json.dumps(state,indent=2,default=str)+'\n'); print(json.dumps({'phase':PHASE['id'],'training_gate':report['training_gate'],'training':train,'folds':folds,'stress':report['stress_training'],'validation':report['validation'],'final_holdout':'UNTOUCHED'},indent=2,default=str))
if __name__=='__main__': main()
