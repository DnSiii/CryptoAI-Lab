"""Append execution from a durable checkpoint, never from a revised replay balance."""
from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
import json

import numpy as np
import pandas as pd
from cryptoai_v13.paper_execution import exact_fast
from cryptoai_v13.data import FuturesData

PROJECT = Path(__file__).resolve().parents[1]


def baseline(path: Path) -> dict | None:
    frozen = PROJECT / 'reports' / 'published_baseline' / path.name
    source = frozen if frozen.exists() else path
    return json.loads(source.read_text()) if source.exists() else None


def migrate_checkpoint(old: dict, original, data, previous: dict) -> dict:
    """One explicit migration: legacy files did not persist guard internals."""
    cutoff = pd.Timestamp(old['latest_data_timestamp'])
    curve = old['equity_curve']
    capital = float(curve[-1]['capital_brl']) / float(old['base_capital_brl'])
    weights = previous.get('current_simulated_positions') or {
        s: a.get('current_weight', 0.0) for s, a in old.get('assets', {}).items()
        if abs(a.get('current_weight', 0.0)) > 1e-12
    }
    params = original.execution_parameters
    peak = float(curve[0]['capital_brl']) / float(old['base_capital_brl'])
    active, until = False, -1
    threshold = params.get('drawdown_guard_threshold')
    cooldown = params.get('drawdown_guard_cooldown_hours')
    for i in range(1, len(curve)):
        prior = float(curve[i-1]['capital_brl']) / float(old['base_capital_brl'])
        if threshold is not None:
            if cooldown is not None and active and i >= until:
                active, peak = False, prior
            recovery = params.get('drawdown_guard_recovery')
            recovery = threshold / 2 if recovery is None else recovery
            dd = prior / peak - 1
            if cooldown is None and active and dd >= -abs(recovery):
                active = False
            elif not active and dd <= -abs(threshold):
                active = True
                if cooldown is not None:
                    until = i + cooldown
        peak = max(peak, float(curve[i]['capital_brl']) / float(old['base_capital_brl']))
    # Reconstruct last executed targets from the immutable order log.
    requested = dict(old.get('opening_snapshot', {}).get('positions', weights))
    for decision in old.get('decisions', []):
        for adjustment in decision.get('adjustments', []):
            requested[adjustment['symbol']] = float(adjustment['new_weight'])
    prices = {s: float(a['current_price']) for s, a in old.get('assets', {}).items()
              if a.get('current_price') is not None and np.isfinite(a['current_price'])}
    return {'timestamp': cutoff.isoformat(), 'equity': capital, 'peak_equity': peak,
            'weights': weights, 'last_requested_target': requested,
            'drawdown_guard_active': active, 'guard_remaining_hours': max(0, until-len(curve)+1),
            'ruined': capital <= 0, 'last_prices': prices,
            'migration': 'Legacy capital and positions restored; guard state reconstructed from published paper curve, not a revised replay.'}


def resume_tail(data, targets, original, checkpoint, previous_target=None):
    if checkpoint.get('execution_parameters') is not None and checkpoint['execution_parameters'] != original.execution_parameters:
        raise RuntimeError('Execution parameters changed across a frozen checkpoint')
    cutoff = pd.Timestamp(checkpoint['timestamp'])
    if cutoff not in data.close.index:
        raise RuntimeError('Durable execution hour is missing from market data')
    index = data.close.index[data.close.index >= cutoff]
    expected = pd.date_range(index[0], index[-1], freq='h')
    if not index.equals(expected):
        raise RuntimeError('Non-contiguous market hours; refusing to skip an execution hour')
    tail_data = FuturesData(frames={k: v.loc[index].copy() for k,v in data.frames.items()},
                            funding=data.funding.loc[index].copy(), symbols=data.symbols)
    tail_targets = targets.reindex(index=index, columns=data.close.columns).fillna(0.0).copy()
    if previous_target is not None:
        tail_targets.loc[cutoff] = pd.Series(previous_target).reindex(tail_targets.columns).fillna(0.0)
    return exact_fast(tail_data, tail_targets, **original.execution_parameters, initial_state=checkpoint)


def pad_result(data, result, old):
    """Only published equity is used for the display prefix; execution stays in tail."""
    index = data.close.index
    values = {pd.Timestamp(p['timestamp']): float(p['capital_brl']) / old['base_capital_brl']
              for p in old['equity_curve']}
    equity = pd.Series(values).reindex(index).fillna(1.0)
    equity.loc[result.equity.index] = result.equity
    fields = {'equity': equity, 'paper_baseline': old}
    for key in ('positions', 'turnover', 'fees', 'funding', 'gross_exposure', 'open_positions',
                'asset_gross', 'asset_fees', 'asset_funding', 'asset_orders', 'asset_order_notional'):
        value = getattr(result, key)
        if value is not None:
            fields[key] = value.reindex(index=index, fill_value=0.0)
    return replace(result, **fields)


def continue_paper(data, targets, original, ledger_path, previous=None):
    old = baseline(ledger_path)
    if old is None or not old.get('equity_curve'):
        return original
    if previous and old['candidate'] != previous.get('candidate', old['candidate']):
        raise RuntimeError('Paper candidate identity changed')
    previous = previous or {}
    checkpoint = old.get('execution_checkpoint') or migrate_checkpoint(old, original, data, previous)
    saved_parameters = checkpoint.get('execution_parameters')
    if saved_parameters is not None and saved_parameters != original.execution_parameters:
        raise RuntimeError('Execution parameters changed across a frozen paper checkpoint')
    tail = resume_tail(data, targets, original, checkpoint, previous.get('target_for_next_open') or checkpoint.get('next_target'))
    tail.execution_state['execution_parameters'] = original.execution_parameters
    tail.execution_state['next_target'] = {s:float(v) for s,v in targets.iloc[-1].items() if abs(v)>1e-12}
    if 'migration' in checkpoint:
        tail.execution_state['migration'] = checkpoint['migration']
    return pad_result(data, tail, old)


def merge_ledger(old, segment, execution_state):
    new = copy.deepcopy(segment)
    cutoff = old['latest_data_timestamp']
    factor = old['equity_curve'][-1]['capital_brl'] / segment['base_capital_brl']
    def scaled(row):
        row = copy.deepcopy(row)
        for key, value in list(row.items()):
            if key.endswith('_brl') and isinstance(value, (int, float)):
                row[key] = round(value * factor, 2)
        if 'adjustments' in row:
            row['adjustments'] = [scaled(r) for r in row['adjustments']]
        if 'capital_brl' in row:
            row['equity_multiple'] = round(row['capital_brl']/old['base_capital_brl'], 10)
        return row
    new['equity_curve'] = copy.deepcopy(old['equity_curve']) + [scaled(r) for r in segment['equity_curve'] if r['timestamp'] > cutoff]
    new['decisions'] = copy.deepcopy(old.get('decisions', [])) + [scaled(r) for r in segment.get('decisions', []) if r['timestamp'] > cutoff]
    for key in ('paper_start_after_timestamp', 'base_capital_brl', 'opening_snapshot', 'candidate', 'mode'):
        if key in old:
            new[key] = copy.deepcopy(old[key])
    amounts = ('gross_result_brl','fees_brl','funding_result_brl','total_cost_brl','net_result_brl')
    assets = copy.deepcopy(old.get('assets', {}))
    for item in assets.values():
        item.update(status='closed', direction='none', current_weight=0.0, position_value_brl=0.0)
    for symbol, item in segment.get('assets', {}).items():
        latest = scaled(item)
        prior = old.get('assets', {}).get(symbol, {})
        for key in amounts:
            latest[key] = round(prior.get(key, 0.0)+latest.get(key, 0.0), 2)
        if 'tracked_since' in prior:
            latest['tracked_since'] = prior['tracked_since']
            latest['inherited_at_paper_start'] = prior.get('inherited_at_paper_start', False)
        assets[symbol] = latest
    new['assets'] = assets
    summary = scaled(segment['summary'])
    for key in amounts:
        summary[key] = round(old['summary'].get(key, 0.0)+summary.get(key, 0.0), 2)
    for key in ('positioned_hours','decision_events','position_adjustments','positive_hours','negative_hours'):
        summary[key] = old['summary'].get(key, 0)+segment['summary'].get(key, 0)
    capitals = [r['capital_brl'] for r in new['equity_curve']]
    summary.update(current_capital_brl=capitals[-1], highest_capital_brl=max(capitals), lowest_capital_brl=min(capitals))
    summary['net_result_brl'] = round(capitals[-1]-old['base_capital_brl'], 2)
    summary['total_cost_brl'] = round(summary.get('fees_brl',0)-summary.get('funding_result_brl',0),2)
    summary['gross_result_brl'] = round(summary['net_result_brl']+summary['total_cost_brl'],2)
    if assets:
        last = next(reversed(assets.values()))
        for key in ('gross_result_brl','fees_brl','funding_result_brl'):
            last[key] = round(last.get(key,0)+summary.get(key,0)-sum(a.get(key,0) for a in assets.values()),2)
        for item in assets.values():
            item['total_cost_brl'] = round(item.get('fees_brl',0)-item.get('funding_result_brl',0),2)
            item['net_result_brl'] = round(item.get('gross_result_brl',0)-item['total_cost_brl'],2)
    new['summary'] = summary
    new['execution_checkpoint'] = execution_state
    new['continuity'] = copy.deepcopy(old.get('continuity', {'method': 'durable_incremental_execution', 'segments': []}))
    if 'migration' in execution_state:
        new['continuity']['migration'] = execution_state['migration']
    if pd.Timestamp(new['latest_data_timestamp'])-pd.Timestamp(cutoff) > pd.Timedelta(hours=3):
        new['continuity']['segments'].append({'after': cutoff, 'through': new['latest_data_timestamp'],
            'kind': 'RETROSPECTIVE_GAP_RECOVERY', 'computed_at_utc': pd.Timestamp.now(tz='UTC').isoformat()})
        new['continuity']['independent_forward_after_timestamp'] = pd.Timestamp.now(tz='UTC').floor('h').isoformat()
    return new


def continue_frozen(data, frozen, old, previous, execution):
    """Continue V99's two independent sleeves and preserve transfer schedule."""
    cutoff = pd.Timestamp(old['latest_data_timestamp'])
    checkpoint = old.get('execution_checkpoint')
    weight = float(old['composite']['satellite_realized_weight'])
    if checkpoint is None:
        parent_old = baseline(PROJECT/'reports'/'paper_v16_ledger.json')
        parent_previous_path = PROJECT/'reports'/'published_baseline'/'paper_v16_state.json'
        parent_previous = json.loads(parent_previous_path.read_text()) if parent_previous_path.exists() else {}
        parent_cp = parent_old.get('execution_checkpoint') or migrate_checkpoint(parent_old, frozen.parent_result, data, parent_previous)
        if pd.Timestamp(parent_cp['timestamp']) != cutoff:
            raise RuntimeError('V99 and its legacy parent have different publication hours')
        aggregate = previous.get('current_simulated_positions', {})
        sat_weights = {s: (aggregate.get(s, 0.0)-(1-weight)*parent_cp['weights'].get(s, 0.0))/weight
                       for s in set(aggregate)|set(parent_cp['weights'])} if weight > 1e-12 else {}
        sat_window = frozen.satellite_result.equity.loc[:cutoff]
        sat_old = {'latest_data_timestamp': cutoff.isoformat(), 'base_capital_brl': 10000,
                   'equity_curve': [{'timestamp': t.isoformat(), 'capital_brl': float(v)*10000} for t,v in sat_window.items()],
                   'assets': {}, 'opening_snapshot': {'positions': {}}, 'decisions': []}
        sat_cp = migrate_checkpoint(sat_old, frozen.satellite_result, data, {'current_simulated_positions': sat_weights})
        sat_cp['last_requested_target'] = {s: float(v) for s,v in frozen.satellite_result.requested_targets.loc[cutoff-pd.Timedelta(hours=1)].items() if abs(v)>1e-12}
        total = old['summary']['current_capital_brl']/old['base_capital_brl']
        checkpoint = {'timestamp': cutoff.isoformat(), 'parent': parent_cp, 'satellite': sat_cp,
                      'parent_capital': total*(1-weight), 'satellite_capital': total*weight,
                      'next_rebalance': (int(data.close.index.get_loc(cutoff))//720+1)*720-int(data.close.index.get_loc(cutoff)),
                      'migration': 'Legacy V99 sleeve allocations inferred from published aggregate positions and parent checkpoint; missing guard internals reconstructed.'}
    parent = resume_tail(data, frozen.parent_result.requested_targets, frozen.parent_result, checkpoint['parent'], checkpoint['parent'].get('next_target'))
    satellite = resume_tail(data, frozen.satellite_result.requested_targets, frozen.satellite_result, checkpoint['satellite'], checkpoint['satellite'].get('next_target'))
    idx = parent.equity.index
    pr = parent.equity.pct_change(fill_method=None).fillna(0.0)
    sr = satellite.equity.pct_change(fill_method=None).fillna(0.0)
    pc, sc = checkpoint['parent_capital'], checkpoint['satellite_capital']
    next_rebalance = int(checkpoint['next_rebalance'])
    equity, weights = [], []
    cost_total = 0.0
    for i, t in enumerate(idx):
        if i:
            pc *= 1+float(pr.loc[t]); sc *= 1+float(sr.loc[t])
            total = pc+sc
            if total <= 0:
                raise RuntimeError('V99 composite reached ruin; do not restart')
            if i == next_rebalance:
                desired = float(frozen.target_satellite_weight.loc[t])
                cost = total*abs(sc/total-desired)*2*execution['base_cost_per_side']
                cost_total += cost
                pc, sc = (total-cost)*(1-desired), (total-cost)*desired
                next_rebalance += 720
        equity.append(pc+sc); weights.append(sc/(pc+sc))
    eq = pd.Series(equity,index=idx)
    w = pd.Series(weights,index=idx)
    positions = parent.positions.mul(1-w,axis=0)+satellite.positions.mul(w,axis=0)
    state = {'timestamp': idx[-1].isoformat(), 'parent': parent.execution_state,
             'satellite': satellite.execution_state, 'parent_capital': pc, 'satellite_capital': sc,
             'next_rebalance': next_rebalance-(len(idx)-1)}
    for key,result in [('parent',parent),('satellite',satellite)]:
        state[key]['execution_parameters'] = result.execution_parameters
        state[key]['next_target'] = {s:float(v) for s,v in result.requested_targets.iloc[-1].items() if abs(v)>1e-12}
    if 'migration' in checkpoint:
        state['migration'] = checkpoint['migration']
    # Frozen ledger normalizes from the original boundary: use immutable equity prefix.
    full_eq = pd.Series({pd.Timestamp(p['timestamp']):p['capital_brl']/old['base_capital_brl'] for p in old['equity_curve']})
    full_eq = full_eq.reindex(data.close.index).fillna(1.0)
    full_eq.loc[idx] = eq
    full_pos = positions.reindex(data.close.index,fill_value=0.0)
    full_w = w.reindex(data.close.index).ffill().fillna(weight)
    return replace(frozen, equity=full_eq, positions=full_pos, satellite_weight=full_w,
                   execution_state=state, transfer_cost_total=cost_total)
