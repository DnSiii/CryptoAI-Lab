from __future__ import annotations
import hashlib,json,math,sys,urllib.request
from pathlib import Path
import numpy as np,pandas as pd
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3
CFG=PROJECT/'config'/'v98_independent.json'
OUT=PROJECT/'reports'/'v98_independent_phase106_txcount_rotation.json'
POS=PROJECT/'reports'/'v98_independent_phase106_txcount_rotation_positions.csv'
PREREG='reports/v98_independent_phase106_txcount_rotation_prereg.md'
BASE='https://community-api.coinmetrics.io/v4/timeseries/asset-metrics'
MAP={'btc':'BTCUSDT','eth':'ETHUSDT'};GROSS=.75;LOOKBACK_DAYS=28

def metric(asset):
    url=f'{BASE}?assets={asset}&metrics=TxCnt&frequency=1d&start_time=2022-11-01&end_time=2025-12-31&page_size=10000'
    req=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'CryptoAI-Lab-V98-Phase106/1.0'})
    raw=urllib.request.urlopen(req,timeout=60).read();obj=json.loads(raw);rows=[]
    for x in obj.get('data',[]):
        try:
            ts=pd.to_datetime(x['time'],utc=True).normalize();v=float(x['TxCnt'])
            if math.isfinite(v) and v>0: rows.append((ts,v))
        except Exception: pass
    return pd.Series(dict(rows),dtype=float).sort_index(),raw,url

def build_targets(data,series):
    t=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns)
    events=t.index.hour==0
    cal=pd.date_range('2022-11-01','2025-12-31',freq='1D',tz='UTC')
    scores={}
    for asset in MAP:
        lag=series[asset].reindex(cal).shift(1)
        scores[asset]=np.log(lag.replace(0,np.nan)).diff(LOOKBACK_DAYS)
    for ts in t.index[events]:
        day=ts.normalize()
        vals={a:scores[a].get(day,np.nan) for a in MAP}
        if not all(np.isfinite(v) for v in vals.values()): continue
        if vals['btc']==vals['eth']: continue
        long_asset='btc' if vals['btc']>vals['eth'] else 'eth'
        short_asset='eth' if long_asset=='btc' else 'btc'
        t.loc[ts,MAP[long_asset]]=GROSS/2
        t.loc[ts,MAP[short_asset]]=-GROSS/2
    return t.where(pd.Series(events,index=t.index),np.nan).ffill().fillna(0.)

def ev(data,t,cfg,s):
    f=cfg['funding_stress'][s]
    return exact_fast(data,t,cost_per_side=cfg['costs'][f'{s}_per_side'],gross_guard_cap=GROSS,
                      funding_debit_multiplier=f['debit_multiplier'],funding_credit_multiplier=f['credit_multiplier'])

def tails(r,a,b):
    d=r.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna().sort_values()
    n=max(1,int(np.ceil(.05*len(d))));ad=d.abs().sort_values(ascending=False);den=float(d.abs().sum())
    return {'bottom_5pct_sum':float(d.iloc[:n].sum()),'top_5pct_sum':float(d.iloc[-n:].sum()),
            'top10_absolute_day_share':float(ad.head(10).sum()/den) if den else 0.}

def contribution(data,t,a,b):
    x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,list(MAP.values())].sum().fillna(0.)
    d=float(x.abs().sum())
    return {'pre_cost_position_return_sum':{k:float(v) for k,v in x.items()},
            'absolute_contribution_share':{k:(float(abs(v)/d) if d else 0.) for k,v in x.items()}}

def main():
    cfg=json.loads(CFG.read_text());data=load_data(PROJECT,cfg['data_config']);v=validate_data(data)
    if v['errors']: raise RuntimeError(str(v['errors'][:5]))
    series={};src={}
    for asset in MAP:
        series[asset],raw,url=metric(asset);src[asset]={'url':url,'raw_sha256':hashlib.sha256(raw).hexdigest()}
    a=cfg['folds'][0]['start'];b=cfg['training_end'];t=build_targets(data,series)
    rs={x:ev(data,t,cfg,x) for x in ('base','severe','supersevere')}
    base=rs['base'];train=p3.metrics(base,a,b)
    folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']}
    stress={x:p3.metrics(rs[x],a,b) for x in ('severe','supersevere')}
    con=contribution(data,t,a,b);tail=tails(base,a,b);fail=[]
    if train['total_return']<=0: fail.append('aggregate_return<=0')
    if train['profit_factor_daily']<=1.10: fail.append('aggregate_pf<=1.10')
    if train['max_drawdown']<-.35: fail.append('max_drawdown<-35%')
    if train['worst_day']<-.12: fail.append('worst_day<-12%')
    for n,m in folds.items():
        if m['total_return']<=0: fail.append(f'{n}_return<=0')
        if m['profit_factor_daily']<=1.02: fail.append(f'{n}_pf<=1.02')
    for x in ('severe','supersevere'):
        if stress[x]['total_return']<=0 or stress[x]['profit_factor_daily']<=1.0: fail.append(f'{x}_gate')
    if max(con['absolute_contribution_share'].values(),default=0)>0.60: fail.append('single_asset_contribution>60%')
    if tail['top10_absolute_day_share']>0.60: fail.append('top10_absolute_day_share>60%')
    rep={'engine':'V98 Independent','phase':'106',
         'hypothesis':'relative BTC-vs-ETH 28d transaction-throughput rotation',
         'preregistration':PREREG,
         'parameters':{'metric':'TxCnt','lookback_days':LOOKBACK_DAYS,'gross':GROSS,'assets':MAP,
                       'lag':'strict prior UTC day','rebalance':'daily 00:00 UTC',
                       'construction':'long higher 28d log TxCnt growth; short lower; equal absolute weights'},
         'source':src,'phase083_selection_use':False,'future_holdout_required':True,
         'training':train,'folds':folds,'stress_training':stress,
         'regimes_training':p3.regime_metrics(base,data,a,b,b),
         'concentration_training':p3.concentration_metrics(base,a,b),
         'asset_contribution_proxy':con,'tails_training':tail,
         'reproducibility':{'targets_sha256':hashlib.sha256(t.loc[a:b,list(MAP.values())].to_csv().encode()).hexdigest(),
                            'prereg_sha256':hashlib.sha256((PROJECT/PREREG).read_bytes()).hexdigest()},
         'training_gate':{'passed':not fail,'decision':'PASS_TRAINING' if not fail else 'REJECT_NO_RESCUE','failures':fail},
         'validation':None,'final_holdout':None,'v99_used':False,'v16_used':False,
         'parameter_search':False,'rescue_allowed':False}
    OUT.write_text(json.dumps(rep,indent=2,default=str)+'\n');base.positions.to_csv(POS)
    print(json.dumps({'phase':'106','training_gate':rep['training_gate'],'training':train,'folds':folds,
                      'stress':stress,'contribution':con,'tails':tail},indent=2,default=str))
if __name__=='__main__': main()
