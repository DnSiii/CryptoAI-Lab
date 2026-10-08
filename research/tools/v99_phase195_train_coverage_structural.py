#!/usr/bin/env python3
"""Phase195-E: streaming, fail-closed dual-source TRAIN continuity checker.

Input JSONL is UNTRUSTED operator-generated evidence. It cannot prove canonical
consensus anchoring, historical latency, operator independence, or economics.
Even a PASS is STRUCTURAL_ONLY and NEVER authorizes a backtest/holdout trial.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from itertools import zip_longest
from pathlib import Path

TRAIN_START = 1638316800
TRAIN_END = 1705536000
INTERIOR_DAYS = 776
FOLDS = 6
HEX32 = re.compile(r'0x[0-9a-f]{64}\Z')


def reject(reason):
    raise ValueError(reason)


def _no_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            reject('duplicate_json_key:' + key)
        obj[key] = value
    return obj


def _no_nonfinite(value):
    reject('nonfinite_json_number:' + value)


def parse_rows(path):
    with Path(path).open('r',encoding='utf-8') as stream:
        for n,line in enumerate(stream,1):
            if not line.strip():reject(f'blank_line:{n}')
            try:
                row=json.loads(line, object_pairs_hook=_no_duplicate_keys,
                               parse_constant=_no_nonfinite)
            except ValueError as exc:
                if str(exc).startswith(('duplicate_json_key:', 'nonfinite_json_number:')):
                    raise
                reject(f'invalid_json:{n}')
            except TypeError:reject(f'invalid_json:{n}')
            if not isinstance(row,dict):reject(f'nonobject_row:{n}')
            yield row


def h32(v):
    if not isinstance(v,str) or HEX32.fullmatch(v) is None:
        reject('noncanonical_hash')
    return v


def require_int(v,field):
    if type(v) is not int or v < 0:reject('invalid_'+field)
    return v


def compare(a,b,field):
    if a.get(field)!=b.get(field):reject('operator_disagreement_'+field)


def verify_pair(a_path,b_path,*,start=TRAIN_START,end=TRAIN_END,
                interior_days=INTERIOR_DAYS,folds=FOLDS):
    """Test overrides are Python-only; CLI always uses fixed frozen envelope."""
    if end<=start or (end-start)%86400 or (end-start)//86400-2!=interior_days:
        reject('invalid_frozen_day_envelope')
    if folds<1 or folds>interior_days:reject('invalid_fold_count')
    streams=[parse_rows(a_path),parse_rows(b_path)]
    prev_height=prev_time=None
    prev_hash=None
    first=True
    after=False
    operator_ids=None
    counts=[0]*((end-start)//86400)
    blocks=0
    events=0
    digest=hashlib.sha256()
    for a,b in zip_longest(*streams):
        if a is None or b is None:reject('operator_length_disagreement')
        if first:
            if a.get('operator')==b.get('operator') or not all(
                    isinstance(z.get('operator'),str) and z['operator'] for z in (a,b)):
                reject('operator_labels_not_distinct')
            operator_ids=(a['operator'],b['operator'])
        elif (a.get('operator'),b.get('operator'))!=operator_ids:
            reject('operator_label_changed')
        for key in ('height','hash','parent_hash','timestamp','receipts_root',
                    'native_event_count','native_event_sha256','header_only'):
            compare(a,b,key)
        height=require_int(a.get('height'),'height')
        stamp=require_int(a.get('timestamp'),'timestamp')
        hh=h32(a.get('hash')); parent=h32(a.get('parent_hash'))
        if prev_height is not None:
            if height!=prev_height+1 or parent!=prev_hash:reject('header_chain_gap_or_reorg')
            if stamp<=prev_time:reject('nonincreasing_block_timestamp')
        if first:
            if stamp>=start or a.get('header_only') is not True:
                reject('missing_before_boundary_header_sentinel')
            for row in (a,b):
                if any(row.get(k) is not None for k in (
                        'native_event_count','receipts_root','native_event_sha256',
                        'local_receipts_root_checked','all_receipts_present',
                        'both_native_topics_checked','all_unrelated_logs_included')):
                    reject('sentinel_contains_out_of_train_events')
            first=False
        elif stamp>=end:
            if after:reject('extra_after_boundary_rows')
            if a.get('header_only') is not True:
                reject('missing_after_boundary_header_sentinel')
            for row in (a,b):
                if any(row.get(k) is not None for k in (
                        'native_event_count','receipts_root','native_event_sha256',
                        'local_receipts_root_checked','all_receipts_present',
                        'both_native_topics_checked','all_unrelated_logs_included')):
                    reject('sentinel_contains_out_of_train_events')
            after=True
        else:
            if after:reject('train_after_end_sentinel')
            if stamp<start or a.get('header_only') is not False:
                reject('invalid_train_block')
            for row in (a,b):
                if any(row.get(flag) is not True for flag in (
                        'local_receipts_root_checked','all_receipts_present',
                        'both_native_topics_checked','all_unrelated_logs_included')):
                    reject('unproven_complete_block')
            root=h32(a.get('receipts_root'))
            n=require_int(a.get('native_event_count'),'native_event_count')
            raw_digest=a.get('native_event_sha256')
            if not isinstance(raw_digest,str):reject('invalid_native_event_sha256')
            eh=h32('0x'+raw_digest)
            day=(stamp-start)//86400
            counts[day]+=1
            blocks+=1;events+=n
            digest.update(json.dumps([height,hh,root,n,eh],separators=(',',':')).encode()+b'\n')
        prev_height=height;prev_time=stamp;prev_hash=hh
    if not after:reject('missing_after_boundary_header_sentinel')
    if any(x==0 for x in counts):reject('missing_train_calendar_day')
    interior=counts[1:-1]
    if len(interior)!=interior_days:reject('wrong_interior_day_count')
    fold_days=[len(interior[i*interior_days//folds:(i+1)*interior_days//folds])
               for i in range(folds)]
    if not all(x>0 for x in fold_days):reject('empty_chronological_fold')
    return {'decision':'STRUCTURAL_COVERAGE_CLAIMS_MATCH_ONLY',
            'full_train_calendar_days':len(counts),'interior_train_days':len(interior),
            'chronological_fold_days':fold_days,'complete_claimed_train_blocks':blocks,
            'native_events_claimed':events,'paired_stream_sha256':digest.hexdigest(),
            'independent_consensus_anchor_proven':False,
            'operator_independence_proven':False,
            'historical_latency_proven':False,'economic_trials':0,
            'holdout_touched':False,'no_economic_trial_authorized':True}


def main():
    p=argparse.ArgumentParser(description='Phase195-E TRAIN-only structural checker')
    p.add_argument('--operator-a',required=True)
    p.add_argument('--operator-b',required=True)
    args=p.parse_args()
    try:out=verify_pair(args.operator_a,args.operator_b)
    except ValueError as exc:
        print(json.dumps({'decision':'HOLD_STRUCTURAL_INCOMPLETE','error':str(exc),
                          'economic_trials':0,'no_economic_trial_authorized':True}))
        raise SystemExit(2)
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
