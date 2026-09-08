"""Fixed V16 relative-book experiment, with all losing trials retained."""
from dataclasses import replace
from pathlib import Path
import argparse
import hashlib
import json
import time
import numpy as np
import pandas as pd
from evaluate_v16_recent import PROJECT,hashes,subset,windows
from cryptoai_v13.data import load_data
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.v16_relative import RelativeSpec,relative_targets


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--market-root',type=Path,required=True)
    p.add_argument('--forecast-batch',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args(); out=a.output_dir
    if out.resolve().is_relative_to(a.market_root.resolve()): raise ValueError('protected market input')
    if (out/'protocol.json').exists(): raise ValueError('refusing to overwrite earlier evidence')
    out.mkdir(parents=True,exist_ok=True)
    models=[f'{m}_{h}_relative' for m in ('ridge','boosting') for h in (12,24)]
    menu={f'{n}_{mode}':RelativeSpec(balance='dollar' if mode=='dollar' else 'beta',
          retain_rank_buffer=mode=='beta_buffer',rebalance_hours=int(n.split('_')[1]))
          for n in models for mode in ('dollar','beta','beta_buffer')}
    end=pd.Timestamp('2026-08-31T23:00Z')
    protocol={'registered_at':pd.Timestamp.now(tz='UTC').isoformat(),
        'hypothesis':'Relative forecasts require a balanced book; directional signs alone are not market-neutral.',
        'models':models,'menu':{k:v.to_dict() for k,v in menu.items()},
        'end':end.isoformat(),'code_sha256':hashlib.sha256((PROJECT/'src/cryptoai_v13/v16_relative.py').read_bytes()).hexdigest(),
        'forecast_protocol':json.loads((a.forecast_batch/'protocol.json').read_text()),
        'forecast_files_sha256':{n:hashlib.sha256((a.forecast_batch/f'{n}_forecasts.csv').read_bytes()).hexdigest() for n in models},
        'evaluation_previously_seen':True,'never_auto_promote':True,
        'limitations':['Betas are estimates, updated at rebalances; intervening exposure drifts.',
            'Basket stops use signal-close marks and execute next open.',
            'OHLC data cannot establish live capacity or exact liquidation paths.'],
        'gates':{'1Y':.50,'6M':.15,'3M':.05,'30D':0.,'7D':0.,'max_drawdown':-.20}}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    protected=hashes(a.market_root)
    data=subset(load_data(a.market_root,'research_pit48.json'),'2025-01-01',end)
    forecasts={n:pd.read_csv(a.forecast_batch/f'{n}_forecasts.csv',index_col=0,parse_dates=True).reindex_like(data.close) for n in models}
    records={}; targets={}
    for name,spec in menu.items():
        n=name.rsplit('_',1)[0] if not name.endswith('_beta_buffer') else name[:-len('_beta_buffer')]
        target,diag=relative_targets(data,forecasts[n],spec)
        targets[name]=target
        diag.to_csv(out/f'{name}_diagnostics.csv',index_label='timestamp')
    # Equal model weighting is fixed independently of which model earned most.
    for mode in ('dollar','beta','beta_buffer'):
        targets[f'equal_models_{mode}']=sum(targets[f'{n}_{mode}'] for n in models)/len(models)
    for name,target in targets.items():
        started=time.monotonic(); scenarios={}
        for label,kw,shift in [('base',{},0),('severe_cost',{'cost_per_side':.0012},0),
             ('delay_3h',{},2),('adverse_funding',{'funding_debit_multiplier':2.,'funding_credit_multiplier':.5},0),
             ('zero_execution_cost_diagnostic',{'cost_per_side':0.},0)]:
            r=exact_fast(data,target.shift(shift).fillna(0),gross_guard_cap=2.,**kw)
            w=windows(r.equity,end); start=pd.Timestamp(w['1Y']['start'])
            base=float(r.equity.loc[r.equity.index<start].iloc[-1])
            missing=data.close.isna()|data.frames['open'].isna()
            scenarios[label]={'windows':w,'ruin':r.ruin,
                'annual_fees_fraction':float(r.fees.loc[start:].sum()/base),
                'annual_funding_cost_fraction':float(r.funding.loc[start:].sum()/base),
                'exposed_missing_price_hours':int((r.positions.shift(1).abs().gt(1e-8)&missing).sum().sum())}
            if label=='base':
                r.equity.to_csv(out/f'{name}_equity.csv',index_label='timestamp',header=['equity'])
                long_gross=r.asset_gross.where(r.open_positions.gt(0),0).loc[start:].sum().sum()/base
                short_gross=r.asset_gross.where(r.open_positions.lt(0),0).loc[start:].sum().sum()/base
                # Diagnostic grouping uses intrabar sign; reversals mix overnight P&L.
                scenarios[label]['gross_grouped_by_intrabar_side']={'long':long_gross,'short':short_gross}
                scenarios[label]['mean_realized_net_dollars']=float(r.positions.loc[start:].sum(axis=1).mean())
        b=scenarios['base']['windows']; g=protocol['gates']
        checks={k:b[k]['return']>g[k] for k in ('1Y','6M','3M','30D','7D')}
        checks.update(drawdown=b['1Y']['max_drawdown']>=g['max_drawdown'],
            return_drawdown=(b['1Y']['return_over_drawdown'] or 0)>=2.5,
            without_best3=b['1Y']['without_best_3_days']>0,
            no_invalid_execution=all(v['exposed_missing_price_hours']==0 and not v['ruin'] for v in scenarios.values()),
            stress_positive=all(v['windows']['1Y']['return']>0 and v['windows']['6M']['return']>0
                for k,v in scenarios.items() if k!='zero_execution_cost_diagnostic'))
        records[name]={'scenarios':scenarios,'checks':checks,'research_gate_passed':all(checks.values()),'status':'NOT_APPROVED'}
        (out/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
        print(name,{k:round(v['return']*100,2) for k,v in b.items()},'DD',round(b['1Y']['max_drawdown']*100,2),
              'pass',all(checks.values()),'seconds',round(time.monotonic()-started,1),flush=True)
    if protected!=hashes(a.market_root): raise RuntimeError('protected market source changed')
    verdict={'status':'RESEARCH_COMPLETE_NOT_APPROVED','tested':len(records),'source_preserved':True,
        'passes':[n for n,r in records.items() if r['research_gate_passed']]}
    (out/'verdict.json').write_text(json.dumps(verdict,indent=2)+'\n')
    print(json.dumps(verdict),flush=True)


if __name__=='__main__': main()
