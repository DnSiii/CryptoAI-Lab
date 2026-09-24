from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json';OUT=PROJECT/'reports'/'v98_independent_phase134_downside_jump_breadth_rebound.json';POS=PROJECT/'reports'/'v98_independent_phase134_downside_jump_breadth_rebound_positions.csv'
PREREG='reports/v98_independent_phase134_downside_jump_breadth_rebound_prereg.md';ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'];GROSS=.75;LOOKBACK_DAYS=28;MULT=3.;BREADTH=3

def build_targets(data):
    close=data.close[ASSETS].loc['2022-12-01':'2025-12-31 23:00:00'].astype(float);lr=np.log(close).diff();days=lr.index.normalize();shock=pd.DataFrame(False,index=lr.index,columns=ASSETS)
    scales={}
    for a in ASSETS:
        daily_abs=lr[a].abs().groupby(days).apply(lambda x: float(x.median()) if x.notna().sum()>=23 else np.nan)
        scale=daily_abs.rolling(LOOKBACK_DAYS,min_periods=LOOKBACK_DAYS).median().shift(1);scales[a]=scale
        mapped=pd.Series(days,index=lr.index).map(scale);shock[a]=lr[a] <= (-MULT*mapped.values)
    daily=shock.groupby(days).any();breadth=daily.sum(axis=1);signal=(breadth>=BREADTH).astype(float);activation=signal.copy();activation.index=activation.index+pd.Timedelta(days=1)
    t=pd.DataFrame(np.nan,index=data.close.index,columns=data.close.columns);events=t.index.hour==0
    for ts in t.index[events]:
        s=float(activation.get(ts.normalize(),0.));t.loc[ts,ASSETS]=s*GROSS/len(ASSETS)
    t=t.where(pd.Series(events,index=t.index),np.nan).ffill().fillna(0.);return t,activation

def ev(data,t,cfg,s):
    f=cfg['funding_stress'][s];return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=GROSS,funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])
def tails(r,a,b):
    d=r.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna();den=float(d.abs().sum());ad=d.abs().sort_values(ascending=False);return {'top10_absolute_day_share':float(ad.head(10).sum()/den) if den else 0.,'worst10_sum':float(d.nsmallest(10).sum()),'best10_sum':float(d.nlargest(10).sum())}
def contribution(data,t,a,b):
    x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,ASSETS].sum().fillna(0.);den=float(x.abs().sum());return {'pre_cost_position_return_sum':{k:float(v) for k,v in x.items()},'absolute_contribution_share':{k:(float(abs(v)/den) if den else 0.) for k,v in x.items()}}
def main():
    gate=json.loads((PROJECT/'reports'/'v98_independent_phase133_cross_asset_jump_breadth_data_only.json').read_text());assert gate['decision']=='PASS_DATA_ONLY' and gate['alpha_or_pnl_inspected'] is False
    cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data)
    if v['errors']:raise RuntimeError(str(v['errors'][:5]))
    t,activation=build_targets(data);a=cfg['folds'][0]['start'];b=cfg['training_end'];rr={z:ev(data,t,cfg,z) for z in ('base','severe','supersevere')};base=rr['base'];train=p3.metrics(base,a,b);folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']};stress={z:p3.metrics(rr[z],a,b) for z in ('severe','supersevere')};con=contribution(data,t,a,b);tail=tails(base,a,b);op=base.open_positions.loc[a:b].abs().sum(axis=1) if base.open_positions is not None else pd.Series(dtype=float);maxopen=float(op.max()) if len(op) else 0.;acts=int(activation.loc[pd.Timestamp(a,tz='UTC'):pd.Timestamp(b,tz='UTC')].sum())
    fail=[]
    if train['total_return']<=0:fail.append('aggregate_return<=0')
    if train['profit_factor_daily']<=1.10:fail.append('aggregate_pf<=1.10')
    if train['max_drawdown']<-.35:fail.append('max_drawdown<-35%')
    if train['worst_day']<-.12:fail.append('worst_day<-12%')
    for n,m in folds.items():
        if m['total_return']<=0:fail.append(f'{n}_return<=0')
        if m['profit_factor_daily']<=1.02:fail.append(f'{n}_pf<=1.02')
    for z in ('severe','supersevere'):
        if stress[z]['total_return']<=0 or stress[z]['profit_factor_daily']<=1.:fail.append(f'{z}_gate')
    if max(con['absolute_contribution_share'].values(),default=0)>0.45:fail.append('single_asset_contribution>45%')
    if tail['top10_absolute_day_share']>0.60:fail.append('top10_absolute_day_share>60%')
    if maxopen>GROSS+1e-9:fail.append('max_open_gross>0.75')
    if acts<20:fail.append('activation_days<20')
    rep={'engine':'V98 Independent','phase':'134','hypothesis':'broad downside hourly jumps mean-revert over next UTC day','preregistration':PREREG,'parameters':{'gross':GROSS,'assets':ASSETS,'scale_lookback_days':LOOKBACK_DAYS,'jump_multiple':MULT,'breadth_assets':BREADTH,'activation_lag':'completed UTC day +1 day 00:00 UTC','holding':'until next 00:00 decision','shock_state':'equal-weight long','otherwise':'flat'},'activation_days_training':acts,'training':train,'folds':folds,'stress_training':stress,'regimes_training':p3.regime_metrics(base,data,a,b,b),'concentration_training':p3.concentration_metrics(base,a,b),'asset_contribution_proxy':con,'tails_training':tail,'execution_guard_audit':{'max_open_gross':maxopen,'cap':GROSS},'reproducibility':{'activation_sha256':hashlib.sha256(activation.to_csv().encode()).hexdigest(),'targets_sha256':hashlib.sha256(t.loc[a:b,ASSETS].to_csv().encode()).hexdigest(),'prereg_sha256':hashlib.sha256((PROJECT/PREREG).read_bytes()).hexdigest()},'training_gate':{'passed':not fail,'decision':'PASS_TRAINING' if not fail else 'REJECT_NO_RESCUE','failures':fail},'validation':None,'final_holdout':None,'phase083_selection_use':False,'v99_used':False,'v16_used':False,'parameter_search':False,'rescue_allowed':False}
    OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');base.positions.to_csv(POS);print(json.dumps(rep,indent=2,default=str))
if __name__=='__main__':main()
