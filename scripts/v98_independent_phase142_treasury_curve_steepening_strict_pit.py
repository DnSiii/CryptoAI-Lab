from __future__ import annotations
import csv,hashlib,io,json,math,sys,time
from datetime import date,datetime,timedelta
from decimal import Decimal,InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

import numpy as np
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'))
sys.path.insert(0,str(PROJECT/'scripts'))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data,validate_data
import v98_independent_phase003_dispersion_neutral as p3

CFG=PROJECT/'config'/'v98_independent.json'
OUT=PROJECT/'reports'/'v98_independent_phase142_treasury_curve_steepening_strict_pit.json'
PREREG='reports/v98_independent_phase142_treasury_curve_steepening_strict_pit_prereg.md'
PIT=PROJECT/'reports'/'v98_independent_phase140_t10y2y_full_pit_audit.json'

SERIES='T10Y2Y'
BASE='https://alfred.stlouisfed.org/graph/alfredgraph.csv'
START=date(2023,1,1);END=date(2025,12,31);YEARS=(2023,2024,2025)
BATCH_SIZE=12
VINTAGE_LAG_DAYS=1
PIT_USE_DAYS=2
LOOKBACK=20
ASSETS=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT']
TARGET_GROSS=.45
HARD_GROSS=.50

def weekdays(y:int):
    d=date(y,1,1);e=date(y,12,31);out=[]
    while d<=e:
        if d.weekday()<5:out.append(d)
        d+=timedelta(days=1)
    return out

def chunks(xs,n):
    for i in range(0,len(xs),n):yield xs[i:i+n]

def normalize(v:str):
    v=(v or '').strip()
    if v in ('','.','NA','NaN'):return None
    try:
        x=Decimal(v)
        if not x.is_finite():raise InvalidOperation
        return format(x.normalize(),'f')
    except (InvalidOperation,ValueError):
        raise RuntimeError('malformed ALFRED value')

def fetch_batch(pairs,retries=4):
    params={
        'id':','.join([SERIES]*len(pairs)),
        'vintage_date':','.join(v.isoformat() for _,v in pairs),
        'cosd':min(d for d,_ in pairs).isoformat(),
        'coed':max(d for d,_ in pairs).isoformat(),
    }
    url=BASE+'?'+urlencode(params);last=None
    for attempt,timeout in enumerate((45,65,85,105),start=1):
        try:
            req=Request(url,headers={
                'User-Agent':'CryptoAI-Lab-V98-Independent-Phase142/1.0',
                'Accept':'text/csv','Connection':'close'
            })
            with urlopen(req,timeout=timeout) as r:return r.read()
        except Exception as exc:
            last=exc
            if attempt<retries:time.sleep(min(8,2**(attempt-1)))
    raise RuntimeError(f'ALFRED transport failed: {type(last).__name__}') from last

def parse_batch(raw,pairs):
    rows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
    if not rows:raise RuntimeError('empty ALFRED CSV')
    header=rows[0]
    expected=[f"{SERIES}_{v.strftime('%Y%m%d')}" for _,v in pairs]
    if len(header)!=len(expected)+1 or header[0].strip().lower() not in ('date','observation_date') or header[1:]!=expected:
        raise RuntimeError('unexpected ALFRED PIT schema')
    by_date={}
    for row in rows[1:]:
        if len(row)!=len(header):continue
        try:d=datetime.strptime(row[0].strip(),'%Y-%m-%d').date()
        except Exception:continue
        by_date[d]=row[1:]
    accepted=[]
    for i,(obs,vintage) in enumerate(pairs):
        row=by_date.get(obs);value=None if row is None else normalize(row[i])
        if value is not None:accepted.append((obs,vintage,value))
    return accepted

def load_audited_pit():
    pit=json.loads(PIT.read_text())
    assert pit['decision']=='PASS_PIT_DATA_ONLY'
    assert pit['mode']=='DATA_ONLY_FULL_PIT_AUDIT'
    assert pit['values_exposed'] is False
    assert pit['crypto_data_accessed'] is False and pit['alpha_or_pnl_inspected'] is False
    expected_hash=pit['first_acquisition']['normalized_pit_sha256']

    pairs=[(d,d+timedelta(days=VINTAGE_LAG_DAYS)) for y in YEARS for d in weekdays(y)]
    accepted=[]
    for batch in chunks(pairs,BATCH_SIZE):
        accepted.extend(parse_batch(fetch_batch(batch),batch))
    canonical='\n'.join(f'{obs.isoformat()},{vintage.isoformat()},{value}' for obs,vintage,value in accepted).encode()
    digest=hashlib.sha256(canonical).hexdigest()
    if digest!=expected_hash:
        raise RuntimeError('Phase142 PIT reacquisition hash mismatch vs governing Phase140 audit')
    index=pd.DatetimeIndex([pd.Timestamp(obs,tz='UTC') for obs,_,_ in accepted])
    values=pd.Series([float(v) for _,_,v in accepted],index=index,dtype=float)
    assert values.index.is_unique and values.index.is_monotonic_increasing
    return values,digest,len(accepted)

def build_targets(data,macro):
    delta=macro-macro.shift(LOOKBACK)
    signal=(delta>0).astype(float)
    # Observation d is public in accepted ALFRED vintage d+1; Phase142 reserves
    # one more full calendar day and can use it only from d+2 00:00 UTC.
    activation=signal.copy()
    activation.index=activation.index+pd.Timedelta(days=PIT_USE_DAYS)

    t=pd.DataFrame(np.nan,index=data.close.index,columns=data.close.columns)
    decision=t.index.hour==0
    state=activation.reindex(t.index[decision],method='ffill').fillna(0.)
    for ts,v in state.items():
        t.loc[ts,ASSETS]=float(v)*TARGET_GROSS/len(ASSETS)
    return t.where(pd.Series(decision,index=t.index),np.nan).ffill().fillna(0.),activation

def ev(data,t,cfg,stress):
    f=cfg['funding_stress'][stress]
    return exact_fast(
        data,t,
        cost_per_side=cfg['costs'][f'{stress}_per_side'],
        gross_guard_cap=HARD_GROSS,
        funding_debit_multiplier=f['debit_multiplier'],
        funding_credit_multiplier=f['credit_multiplier'],
    )

def daily(result,a,b):
    return result.equity.loc[a:b].resample('1D').last().pct_change(fill_method=None).dropna()

def asset_positive_contribution(data,t,a,b):
    x=(t.shift(1)*data.close.pct_change(fill_method=None)).loc[a:b,ASSETS].sum().fillna(0.)
    pos=x.clip(lower=0);den=float(pos.sum())
    return {k:(float(v/den) if den else 0.) for k,v in pos.items()}

def main():
    prereg=PROJECT/PREREG
    assert prereg.exists()
    txt=prereg.read_text()
    assert '20 accepted observations' in txt
    assert 'delta > 0 => risk-on long' in txt
    assert 'd+2 00:00 UTC' in txt
    assert '**0.45**' in txt and '**0.50 gross**' in txt

    macro,pit_hash,pit_count=load_audited_pit()

    cfg=json.loads(CFG.read_text())
    data=load_data(PROJECT,cfg['data_config'])
    v=validate_data(data)
    assert not v['errors'],v['errors'][:5]

    t,activation=build_targets(data,macro)
    a=cfg['folds'][0]['start'];b=cfg['training_end']
    results={s:ev(data,t,cfg,s) for s in ('base','severe','supersevere')}
    base=results['base']
    train=p3.metrics(base,a,b)
    folds={f['name']:p3.metrics(base,f['start'],f['end']) for f in cfg['folds']}
    stress={s:p3.metrics(results[s],a,b) for s in ('severe','supersevere')}

    d=daily(base,a,b)
    positive=d[d>0]
    top10=float(positive.nlargest(10).sum()/positive.sum()) if float(positive.sum())>0 else 0.
    shares=asset_positive_contribution(data,t,a,b)
    open_gross=base.open_positions.loc[a:b].abs().sum(axis=1)
    max_open=float(open_gross.max())
    max_close=float(base.positions.loc[a:b].abs().sum(axis=1).max())

    failures=[]
    if train['total_return']<=0:failures.append('aggregate_return<=0')
    if train['profit_factor_daily']<1.05:failures.append('aggregate_pf<1.05')
    if train['max_drawdown']<-.35:failures.append('max_drawdown<-35%')
    for name,m in folds.items():
        if m['total_return']<=0:failures.append(f'{name}_return<=0')
        if m['profit_factor_daily']<1.02:failures.append(f'{name}_pf<1.02')
    if stress['severe']['total_return']<=0 or stress['severe']['profit_factor_daily']<1.02:
        failures.append('severe_gate')
    if stress['supersevere']['total_return']<=0 or stress['supersevere']['profit_factor_daily']<1.00:
        failures.append('supersevere_gate')
    if max(shares.values(),default=0)>0.45:failures.append('single_asset_positive_contribution>45%')
    if top10>=.35:failures.append('top10_positive_day_share>=35%')
    if max_open>HARD_GROSS+1e-12:failures.append('max_open_gross>0.50')

    report={
        'engine':'V98 Independent','phase':'142',
        'hypothesis':'strict-PIT 20-observation T10Y2Y steepening as causal risk-on permission for equal-weight crypto',
        'preregistration':PREREG,
        'pit_dependency':{
            'report':'reports/v98_independent_phase140_t10y2y_full_pit_audit.json',
            'decision':'PASS_PIT_DATA_ONLY',
            'normalized_pit_sha256':pit_hash,
            'valid_pit_observations':pit_count,
            'reacquisition_hash_verified':True,
        },
        'signal_contract':{
            'series':SERIES,'lookback_accepted_observations':LOOKBACK,
            'direction':'delta>0 => long; else flat',
            'accepted_vintage_lag_days':VINTAGE_LAG_DAYS,
            'economic_use_lag_days':PIT_USE_DAYS,
            'economic_use':'observation d may affect state from d+2 00:00 UTC',
            'target_gross':TARGET_GROSS,'hard_gross_cap':HARD_GROSS,
            'assets':ASSETS,
        },
        'training':train,'folds':folds,'stress_training':stress,
        'regimes_training':p3.regime_metrics(base,data,a,b,b),
        'concentration_training':p3.concentration_metrics(base,a,b),
        'asset_positive_contribution_share':shares,
        'tails_training':{
            'top10_positive_day_share':top10,
            'worst10_sum':float(d.nsmallest(10).sum()),
            'best10_sum':float(d.nlargest(10).sum()),
            'worst_day':float(d.min()),'best_day':float(d.max()),
        },
        'signal_observations_training':int(activation.loc[pd.Timestamp(a):pd.Timestamp(b)].notna().sum()),
        'active_signal_observations_training':int(activation.loc[pd.Timestamp(a):pd.Timestamp(b)].sum()),
        'execution_guard_audit':{
            'target_gross':TARGET_GROSS,'hard_cap':HARD_GROSS,
            'max_open_gross':max_open,'max_close_gross':max_close,
            'open_cap_passed':bool(max_open<=HARD_GROSS+1e-12),
        },
        'reproducibility':{
            'pit_input_sha256':pit_hash,
            'activation_sha256':hashlib.sha256(activation.to_csv().encode()).hexdigest(),
            'targets_sha256':hashlib.sha256(t.loc[a:b,ASSETS].to_csv().encode()).hexdigest(),
            'prereg_sha256':hashlib.sha256(prereg.read_bytes()).hexdigest(),
        },
        'training_gate':{
            'passed':not failures,
            'decision':'PASS_TRAINING' if not failures else 'REJECT_NO_RESCUE',
            'failures':failures,
        },
        'validation':None,'final_holdout':None,
        'phase083_selection_use':False,'v99_used':False,'v16_used':False,
        'phase141_result_used':False,'parameter_search':False,'rescue_allowed':False,
    }
    OUT.write_text(json.dumps(report,indent=2,default=str)+'\n')
    print(json.dumps({
        'phase':'142','gate':report['training_gate'],
        'training':train,'folds':folds,'stress':stress,
        'max_open_gross':max_open,'max_close_gross':max_close,
        'pit_input_verified':True,
    },indent=2,default=str))

if __name__=='__main__':
    main()
