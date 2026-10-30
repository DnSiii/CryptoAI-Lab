from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT/'src')); sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,point_in_time_liquid_view,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CONFIG_PATH=PROJECT/'config'/'v98_independent.json'; STATE_PATH=PROJECT/'state'/'v98_independent_state.json'; REPORT_PATH=PROJECT/'reports'/'v98_independent_phase032_beta_convexity.json'; POSITIONS_PATH=PROJECT/'reports'/'v98_independent_phase032_beta_convexity_positions.csv'
PHASE={'id':'phase_032_beta_convexity','liquidity_top_n':10,'liquidity_lookback_hours':720,'minimum_history_hours':2160,'exposure_lookback_hours':720,'min_periods':360,'rebalance_hours':24,'gross_target':0.75,'gross_cap':0.75}
def build_targets(data,membership):
    c=PHASE; close=data.close; lag=close.shift(1); eligible=(membership & close.notna()).copy(); eligible['BTCUSDT']=False; ret=lag.pct_change(fill_method=None); btc=ret['BTCUSDT']; x2=btc.pow(2)-btc.pow(2).rolling(c['exposure_lookback_hours'],min_periods=c['min_periods']).mean(); var=btc.rolling(c['exposure_lookback_hours'],min_periods=c['min_periods']).var(); beta=ret.rolling(c['exposure_lookback_hours'],min_periods=c['min_periods']).cov(btc).div(var,axis=0)
    targets=pd.DataFrame(0.0,index=close.index,columns=close.columns); events=np.arange(len(targets))%c['rebalance_hours']==0
    for i,ts in enumerate(targets.index):
        if not events[i]: continue
        lo=max(0,i-c['exposure_lookback_hours']+1); idx=ret.index[lo:i+1]; names=eligible.columns[eligible.loc[ts] & beta.loc[ts].notna()]
        conv={}
        for n in names:
            z=pd.concat([ret.loc[idx,n],btc.loc[idx],x2.loc[idx]],axis=1).dropna()
            if len(z)<c['min_periods']: continue
            X=np.column_stack([np.ones(len(z)),z.iloc[:,1].to_numpy(float),z.iloc[:,2].to_numpy(float)]); y=z.iloc[:,0].to_numpy(float); coef,*_=np.linalg.lstsq(X,y,rcond=None); conv[n]=coef[2]
        if len(conv)<4: continue
        s=pd.Series(conv); y=(s.rank(pct=True)-0.5).to_numpy(float); b=beta.loc[ts,s.index].to_numpy(float); X=np.column_stack([np.ones(len(s)),b]); coef,*_=np.linalg.lstsq(X,y,rcond=None); neutral=y-X@coef; gross=float(np.abs(neutral).sum())
        if np.isfinite(gross) and gross>1e-12: targets.loc[ts,s.index]=neutral*(c['gross_target']/gross)
    targets=targets.where(pd.Series(events,index=targets.index),np.nan).ffill().fillna(0.0); gross=targets.abs().sum(axis=1); return targets.mul((c['gross_cap']/gross.replace(0,np.nan)).clip(upper=1).fillna(0),axis=0)
def ev(data,t,cfg,s):
    f=cfg['funding_stress'][s]; return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=PHASE['gross_cap'],funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def main():
    cfg=json.loads(CONFIG_PATH.read_text()); state=json.loads(STATE_PATH.read_text()); data=load_data(PROJECT,cfg['data_config']); v=validate_data(data)
    if v['errors']: raise RuntimeError(str(v['errors'][:5]))
    liquid,membership=point_in_time_liquid_view(data,top_n=PHASE['liquidity_top_n'],lookback_hours=PHASE['liquidity_lookback_hours'],minimum_history_hours=PHASE['minimum_history_hours']); t=build_targets(liquid,membership); r={s:ev(liquid,t,cfg,s) for s in ('base','severe','supersevere')}; a,b=cfg['research_start'],cfg['training_end']; train=p3.metrics(r['base'],a,b); folds={f['name']:p3.metrics(r['base'],f['start'],f['end']) for f in cfg['folds']}; sev=p3.metrics(r['severe'],a,b); sup=p3.metrics(r['supersevere'],a,b); conc=p3.concentration_metrics(r['base'],a,b); beta_n=p3.beta_neutrality_metrics(r['base'],liquid,a,b); regimes=p3.regime_metrics(r['base'],liquid,a,b,b); passed,failures=p3.training_gate(train,folds,sev,sup,conc)
    hyp='Lagged nonlinear BTC-return convexity may contain cross-sectional return information beyond linear beta after dollar and beta neutralization.'; report={'engine':'V98 Independent','phase':PHASE,'hypothesis':hyp,'preregistration':'reports/v98_independent_phase032_beta_convexity_preregistration.md','selection_policy':'single frozen causal beta-convexity specification; no sign/window/cadence/gross/threshold/regime search; validation only if training passes; final holdout untouched','training':train,'folds':folds,'stress_training':{'severe':sev,'supersevere':sup},'concentration_training':conc,'beta_neutrality_training':beta_n,'regimes_training':regimes,'training_gate':{'passed':passed,'failures':failures},'validation':None,'final_holdout':None}
    if passed:
        v0,v1=cfg['validation_start'],cfg['validation_end']; vb=p3.metrics(r['base'],v0,v1); vs=p3.metrics(r['severe'],v0,v1); vss=p3.metrics(r['supersevere'],v0,v1); vp,vf=p3.holdout_gate(vb,vs,vss); report['validation']={'base':vb,'severe':vs,'supersevere':vss,'gate':{'passed':vp,'failures':vf}}
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True); REPORT_PATH.write_text(json.dumps(report,indent=2,default=str)+'\n'); r['base'].positions.to_csv(POSITIONS_PATH); validation_pass=bool(passed and report['validation'] and report['validation']['gate']['passed']); state['phase']='phase_032_complete'; state['last_experiment']={'id':PHASE['id'],'hypothesis':hyp,'status':'frozen_pending_final_holdout' if validation_pass else ('training_passed_validation_rejected' if passed else 'training_rejected'),'parameters':'preregistered 720h lagged BTC quadratic exposure; 24h rebalance; 0.75 gross; beta/dollar neutral','report':str(REPORT_PATH.relative_to(PROJECT)),'training_summary':train,'folds':folds,'stress_training':report['stress_training'],'training_gate':report['training_gate'],'validation':report['validation'],'final_holdout_opened':False}; state['champion']=PHASE['id'] if validation_pass else state.get('champion'); state['final_holdout_untouched']=True; state['next_action']='If Phase032 passes training+validation, freeze before one-shot final holdout. If rejected, close beta-convexity without sign/window/cadence rescue and move to another orthogonal alpha.'; STATE_PATH.write_text(json.dumps(state,indent=2,default=str)+'\n'); print(json.dumps({'phase':PHASE['id'],'training_gate':report['training_gate'],'training':train,'folds':folds,'stress':report['stress_training'],'validation':report['validation'],'final_holdout':'UNTOUCHED'},indent=2,default=str))
if __name__=='__main__': main()
