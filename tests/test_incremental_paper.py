import copy
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cryptoai_v13.paper_execution import exact_fast
from cryptoai_v13.data import FuturesData
from paper_continuation import resume_tail, merge_ledger


def market(n=60):
    idx=pd.date_range('2026-01-01',periods=n,freq='h',tz='UTC')
    close=pd.DataFrame({'BTCUSDT':100*np.cumprod(1+np.sin(np.arange(n))*0.016)},index=idx)
    opened=close.shift(1).fillna(close.iloc[0])*1.001
    frames={'open':opened,'close':close,'high':pd.concat([opened,close],axis=1).max(axis=1).to_frame('BTCUSDT')*1.01,
            'low':pd.concat([opened,close],axis=1).min(axis=1).to_frame('BTCUSDT')*.99}
    for k in ('volume','quote_volume','trades'):frames[k]=close*0+1
    return FuturesData(frames=frames,funding=close*0+.0001,symbols=('BTCUSDT',))


def trim(d,idx):
    return FuturesData(frames={k:v.loc[idx] for k,v in d.frames.items()},funding=d.funding.loc[idx],symbols=d.symbols)


@pytest.mark.parametrize('cut',[1,12,25,44])
def test_chunked_execution_equals_uninterrupted_including_costs_and_guard(cut):
    d=market(); t=d.close*0+.8
    t.iloc[15:30]=-.6
    params=dict(cost_per_side=.001,gross_guard_cap=1.1,drawdown_guard_threshold=.012,
                drawdown_guard_multiplier=.4,drawdown_guard_cooldown_hours=6)
    full=exact_fast(d,t,**params)
    first=exact_fast(trim(d,d.close.index[:cut+1]),t,**params)
    tail=resume_tail(d,t,full,first.execution_state)
    for key in ('equity','positions','fees','funding','asset_orders','asset_gross'):
        actual=getattr(tail,key).iloc[1:]
        expected=getattr(full,key).loc[actual.index]
        np.testing.assert_allclose(actual,expected,rtol=1e-12,atol=1e-12)


def test_revised_past_prices_do_not_change_saved_execution():
    d=market();t=d.close*0+.8
    full=exact_fast(d,t)
    first=exact_fast(trim(d,d.close.index[:26]),t)
    saved=first.execution_state
    expected=resume_tail(d,t,full,saved)
    altered=market()
    for frame in altered.frames.values():frame.iloc[:26]*=3
    actual=resume_tail(altered,t,full,saved)
    np.testing.assert_allclose(actual.equity,expected.equity)


def test_missing_hour_and_held_asset_block_publication():
    d=market();t=d.close*0+.8; full=exact_fast(d,t)
    first=exact_fast(trim(d,d.close.index[:26]),t)
    with pytest.raises(RuntimeError,match='Non-contiguous'):
        resume_tail(trim(d,d.close.index.delete(30)),t,full,first.execution_state)
    invalid=copy.deepcopy(first.execution_state);invalid['weights']['UNKNOWN']=.1
    with pytest.raises(ValueError,match='missing'):
        resume_tail(d,t,full,invalid)


def test_merge_preserves_old_points_and_decisions_exactly():
    old={'candidate':'a','mode':'PAPER_ONLY','base_capital_brl':10000,'paper_start_after_timestamp':'2026-01-01T00:00:00Z',
         'latest_data_timestamp':'2026-01-01T01:00:00Z','equity_curve':[{'timestamp':'2026-01-01T00:00:00Z','capital_brl':10000},
         {'timestamp':'2026-01-01T01:00:00Z','capital_brl':11000}], 'decisions':[{'timestamp':'2026-01-01T01:00:00Z','unchanged':True}],
         'opening_snapshot':{'positions':{}},'assets':{},'summary':{'current_capital_brl':11000,'net_result_brl':1000}}
    segment={'base_capital_brl':10000,'latest_data_timestamp':'2026-01-01T02:00:00Z','equity_curve':[
        {'timestamp':'2026-01-01T01:00:00Z','capital_brl':10000},{'timestamp':'2026-01-01T02:00:00Z','capital_brl':10100}],
        'summary':{'current_capital_brl':10100,'net_result_brl':100},'decisions':[],'assets':{}}
    new=merge_ledger(old,segment,{'timestamp':segment['latest_data_timestamp']})
    assert new['equity_curve'][:2]==old['equity_curve']
    assert new['decisions']==old['decisions']
    assert new['summary']['current_capital_brl']==11110
    assert new['summary']['net_result_brl']==1110


def test_v99_component_checkpoints_preserve_monthly_transfers(monkeypatch):
    from cryptoai_v13.v99_paper_execution import FrozenV99Result, combine_dynamic_results
    from paper_continuation import continue_frozen
    d=market(1600);pt=d.close*0+.8;st=d.close*0-.3
    params={'cost_per_side':.001}
    parent=exact_fast(d,pt,**params);sat=exact_fast(d,st,**params)
    desired=pd.Series(.1,index=d.close.index)
    eq,w,pos,cost=combine_dynamic_results(parent,sat,desired,transfer_cost_per_side=.001)
    frozen=FrozenV99Result(eq,pos,w,desired,desired*0+1,parent,sat,cost)
    cut=780
    prefix=trim(d,d.close.index[:cut+1])
    pc=exact_fast(prefix,pt,**params).execution_state
    sc=exact_fast(prefix,st,**params).execution_state
    old={'base_capital_brl':10000,'latest_data_timestamp':d.close.index[cut].isoformat(),
         'equity_curve':[{'timestamp':t.isoformat(),'capital_brl':float(v)*10000} for t,v in eq.iloc[:cut+1].items()],
         'composite':{'satellite_realized_weight':float(w.iloc[cut])},
         'execution_checkpoint':{'timestamp':d.close.index[cut].isoformat(),'parent':pc,'satellite':sc,
              'parent_capital':float(eq.iloc[cut]*(1-w.iloc[cut])),
              'satellite_capital':float(eq.iloc[cut]*w.iloc[cut]),'next_rebalance':1440-cut}}
    resumed=continue_frozen(d,frozen,old,{}, {'base_cost_per_side':.001})
    np.testing.assert_allclose(resumed.equity.iloc[cut:],eq.iloc[cut:],rtol=1e-12)
    np.testing.assert_allclose(resumed.positions.iloc[cut:],pos.iloc[cut:],rtol=1e-12,atol=1e-12)


def test_operational_executor_matches_frozen_strategy_before_checkpoint():
    from cryptoai_v13.backtest import exact_fast as frozen_exact
    d=market();t=d.close*0+.8;t.iloc[15:30]=-.6
    params=dict(cost_per_side=.001,gross_guard_cap=1.1,drawdown_guard_threshold=.012,
                drawdown_guard_multiplier=.4,drawdown_guard_cooldown_hours=6)
    reference=frozen_exact(d,t,**params);operational=exact_fast(d,t,**params)
    for key in ('equity','positions','fees','funding','asset_orders','asset_gross'):
        np.testing.assert_array_equal(getattr(operational,key),getattr(reference,key))


def test_ledger_append_is_idempotent_and_reconciles_asset_attribution(tmp_path,monkeypatch):
    import paper_continuation as continuation
    monkeypatch.setattr(continuation, "PROJECT", tmp_path)
    from paper_once_v13_incremental import build_ledger
    d=market();t=d.close*0+.8
    first_data=trim(d,d.close.index[:26]);first=exact_fast(first_data,t)
    old=build_ledger(first_data,t,first,first_data.close.index[0],'test')
    old['execution_checkpoint']=first.execution_state
    path=tmp_path/'paper_v13_ledger.json'
    import json
    path.write_text(json.dumps(old))
    replay=exact_fast(d,t)
    result=continuation.continue_paper(d,t,replay,path,{'candidate':'test'})
    new=build_ledger(d,t,result,d.close.index[0],'test')
    assert new['equity_curve'][:len(old['equity_curve'])]==old['equity_curve']
    assert new['decisions'][:len(old['decisions'])]==old['decisions']
    assert abs(new['summary']['current_capital_brl']-10000*replay.equity.iloc[-1])<.02
    assert abs(sum(a['net_result_brl'] for a in new['assets'].values())-new['summary']['net_result_brl'])<.02
    path.write_text(json.dumps(new))
    repeated=continuation.continue_paper(d,t,replay,path,{'candidate':'test'})
    again=build_ledger(d,t,repeated,d.close.index[0],'test')
    assert again['equity_curve']==new['equity_curve']
    assert again['summary']==new['summary']
