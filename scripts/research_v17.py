"""Explicit V17 research runner. Never invokes or publishes a V16 paper run."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
from evaluate_v17_recent import PROJECT,subset,windows,hashes
from cryptoai_v13.data import load_data
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.v17_walkforward import ForecastSpec,walkforward_forecasts
from cryptoai_v13.v17_relative import RelativeSpec,relative_targets


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--market-root',type=Path,required=True)
    p.add_argument('--end',required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    if a.output_dir.resolve().is_relative_to(a.market_root.resolve()): raise ValueError('protected input')
    if a.output_dir.exists(): raise ValueError('new evidence folder required')
    manifest=a.market_root/'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text()).get('status')!='COMPLETE':
        raise ValueError('input dataset not complete; do not fill unknown funding with zero')
    cfg=json.loads((PROJECT/'config/candidate_v17_research.json').read_text())
    if cfg['mode']!='RESEARCH_ONLY' or cfg['real_orders'] or cfg['paper_enabled']:
        raise ValueError('research runner cannot place or publish orders')
    end=pd.Timestamp(a.end,tz='UTC')+pd.Timedelta(hours=23)
    a.output_dir.mkdir(parents=True)
    protocol={'engine':'V17','config':cfg,'end':end.isoformat(),'not_a_pristine_holdout':True,
        'automatic_promotion':False,'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (PROJECT/'src/cryptoai_v13').glob('v17_*.py')}}
    (a.output_dir/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    protected=hashes(a.market_root)
    data=subset(load_data(a.market_root,'research_pit48.json'),'2025-01-01',end)
    if data.close.index[-1]!=end: raise ValueError('incomplete final price hour')
    forecasts,folds=walkforward_forecasts(data,ForecastSpec(**cfg['forecast']),
        progress=lambda r:print('V17 fitted',r['fit_at'],flush=True))
    target,diag=relative_targets(data,forecasts,RelativeSpec(**cfg['portfolio']))
    result={}
    for name,kwargs,delay in [('base',{},0),('severe_cost',{'cost_per_side':.0012},0),
        ('delay_3h',{},2),('adverse_funding',{'funding_debit_multiplier':2.,'funding_credit_multiplier':.5},0)]:
        r=exact_fast(data,target.shift(delay).fillna(0),gross_guard_cap=2.,**kwargs)
        result[name]={'windows':windows(r.equity,end),'ruin':r.ruin,
            'exposed_missing_price_hours':int((r.positions.shift(1).abs().gt(1e-8)&(data.close.isna()|data.frames['open'].isna())).sum().sum())}
        r.equity.to_csv(a.output_dir/f'{name}_equity.csv',index_label='timestamp')
    if hashes(a.market_root)!=protected: raise RuntimeError('protected input source changed')
    report={'engine':'V17','version':cfg['version'],'status':'NOT_APPROVED',
        'comparison_status':'BLOCKED_UNRECONCILED_BENCHMARKS','frozen_v16_unchanged':True,
        'monthly_fits':folds,'scenarios':result}
    (a.output_dir/'results.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'engine':'V17','status':report['status'],
        'returns':{k:round(v['return']*100,2) for k,v in result['base']['windows'].items()}}),flush=True)


if __name__=='__main__': main()
