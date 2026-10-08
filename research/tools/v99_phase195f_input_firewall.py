#!/usr/bin/env python3
"""Phase195-F TRAIN-only single-stream input firewall; never authorizes PnL.

Checks syntax and local consistency of untrusted provider JSONL claims. It is
NOT a consensus anchor, two-provider parity test or complete TRAIN gate.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

START, END = 1638316800, 1705536000
HASH = re.compile(r'0x[0-9a-f]{64}\Z')
QUANTITY = re.compile(r'0x(?:0|[1-9a-f][0-9a-f]*)\Z')
FLAGS = ('local_receipts_root_checked','all_receipts_present',
         'both_native_topics_checked','all_unrelated_logs_included')
DATA = ('native_event_count','native_event_sha256','receipts_root')


def fail(reason):
    raise ValueError(reason)


def pairs_no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out: fail('duplicate_json_key:' + key)
        out[key] = value
    return out


def reject_nonfinite(value):
    fail('nonfinite_json_number:' + value)


def canonical_json(line):
    return json.loads(line, object_pairs_hook=pairs_no_duplicates,
                      parse_constant=reject_nonfinite)


def canonical_quantity(value):
    if not isinstance(value, str) or QUANTITY.fullmatch(value) is None:
        fail('noncanonical_rpc_quantity')
    return int(value[2:], 16)


def hash32(value):
    if not isinstance(value, str) or HASH.fullmatch(value) is None:
        fail('noncanonical_hash')
    return value


def uint(value, name):
    if type(value) is not int or value < 0: fail('invalid_' + name)
    return value


def verify(path):
    count = 0
    interior = 0
    prev = None
    label = None
    digest = hashlib.sha256()
    with Path(path).open(encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            if not line.strip(): fail('blank_line:' + str(n))
            row = canonical_json(line)
            if not isinstance(row, dict): fail('nonobject_row')
            op = row.get('operator')
            if not isinstance(op, str) or not op: fail('invalid_operator')
            if label is None: label = op
            elif label != op: fail('operator_label_changed')
            height = uint(row.get('height'), 'height')
            stamp = uint(row.get('timestamp'), 'timestamp')
            block = hash32(row.get('hash'))
            parent = hash32(row.get('parent_hash'))
            if prev is not None:
                if height != prev[0]+1 or parent != prev[1]:
                    fail('header_chain_gap_or_reorg')
                if stamp <= prev[2]: fail('nonincreasing_block_timestamp')
            sentinel = row.get('header_only')
            if type(sentinel) is not bool: fail('invalid_header_only')
            if sentinel:
                if any(row.get(key) is not None for key in DATA + FLAGS):
                    fail('sentinel_contains_out_of_train_receipt_claim')
            else:
                if not START <= stamp < END: fail('train_timestamp_firewall')
                hash32(row.get('receipts_root'))
                hash32('0x' + row.get('native_event_sha256', '')
                       if isinstance(row.get('native_event_sha256'), str) else None)
                uint(row.get('native_event_count'), 'native_event_count')
                if any(row.get(flag) is not True for flag in FLAGS):
                    fail('incomplete_receipt_claim')
                interior += 1
            digest.update(json.dumps(row, sort_keys=True,
                separators=(',', ':'), ensure_ascii=True).encode() + b'\n')
            prev = (height, block, stamp)
            count += 1
    if not count: fail('empty_stream')
    return {'decision':'SINGLE_STREAM_CLAIMS_SYNTAX_ONLY',
            'rows':count,'train_rows_claimed':interior,
            'sha256_canonical_rows':digest.hexdigest(),
            'operator_label':label,'economic_trials':0,
            'independent_consensus_anchor_proven':False,
            'two_provider_parity_proven':False,
            'full_train_coverage_proven':False,
            'historical_latency_proven':False,
            'no_economic_trial_authorized':True}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--jsonl', required=True)
    args = p.parse_args()
    try: result = verify(args.jsonl)
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({'decision':'HOLD_UNTRUSTED_INPUT',
            'reason':str(exc),'economic_trials':0,
            'no_economic_trial_authorized':True}, sort_keys=True))
        raise SystemExit(2)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__': main()
