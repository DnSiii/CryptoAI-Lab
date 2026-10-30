#!/usr/bin/env python3
"""V98 AI1253 synthetic cross-OS signed-source forensic; never historical PnL."""
from __future__ import annotations
import argparse
import hashlib
import json
import numpy as np
from phase1247_ai_four_signed_sources import source_bundle, relative_value
from phase1251_ai_complete_180cell import fixture

SOURCE_NAMES = ('Growth', 'Opportunity', 'RelativeValue', 'Stress', 'RV_beta')
ROUND_DIGITS = (12, 10, 9, 8, 7)

def sha_bytes(a):
    return hashlib.sha256(np.asarray(a, dtype='<f8').tobytes()).hexdigest()

def quantized_sha(a, digits):
    v = np.round(np.asarray(a, dtype=np.float64), digits)
    v[v == 0.] = 0.  # only canonicalize zero signs for DIAGNOSTICS
    return sha_bytes(v)

def emit():
    data = {'phase': 1253, 'historical_pnl_computed': False,
            'synthetic_only': True, 'fixtures': {}}
    for crisis in (False, True):
        label = 'crisis' if crisis else 'benign'
        frames = fixture(crisis)
        close, high, low, rate, event = (frames[3], frames[1],
                                         frames[2], frames[5], frames[6])
        sources = source_bundle(close, high, low, rate, event)
        rv, beta = relative_value(close)
        if not np.array_equal(rv, sources[2]):
            raise AssertionError('AI1253_RV_REPEAT_NOT_DETERMINISTIC')
        arrays = list(sources[:4]) + [beta]
        if any(a.shape != (900, 4) or not np.isfinite(a).all()
               for a in arrays):
            raise AssertionError('AI1253_ARRAY_INVALID')
        state = sources[4]['state'].tolist()
        data['fixtures'][label] = {
            'sources': {name: a.tolist() for name, a in zip(SOURCE_NAMES, arrays)},
            'raw_sha': {name: sha_bytes(a) for name, a in zip(SOURCE_NAMES, arrays)},
            'quantized_sha': {
                name: {str(k): quantized_sha(a, k) for k in ROUND_DIGITS}
                for name, a in zip(SOURCE_NAMES, arrays)},
            'states': state,
            'activation': {name: int(np.count_nonzero(
                np.abs(a[720:]).sum(axis=1) > 1e-10))
                for name, a in zip(SOURCE_NAMES[:4], arrays[:4])},
            'state_sha': hashlib.sha256(
                json.dumps(state, separators=(',', ':')).encode()).hexdigest(),
        }
    return data

def compare(a, b):
    if a['phase'] != 1253 or b['phase'] != 1253:
        raise AssertionError('AI1253_PHASE_MISMATCH')
    outcome = {'phase': 1253, 'historical_pnl_computed': False,
               'fixtures': {}, 'numeric_diagnostic_pass': True}
    for label in ('benign', 'crisis'):
        x, y = a['fixtures'][label], b['fixtures'][label]
        same_state = x['states'] == y['states']
        outcome['fixtures'][label] = {'states_equal': same_state,
                                      'sources': {}}
        if not same_state:
            outcome['numeric_diagnostic_pass'] = False
        for name in SOURCE_NAMES:
            p = np.asarray(x['sources'][name], dtype=np.float64)
            q = np.asarray(y['sources'][name], dtype=np.float64)
            if p.shape != (900, 4) or q.shape != p.shape:
                raise AssertionError('AI1253_SOURCE_SHAPE')
            diff = np.abs(p-q)
            direction = (np.sign(p) != np.sign(q)) & (
                (np.abs(p) > 1e-8) | (np.abs(q) > 1e-8))
            gross = np.max(np.abs(np.abs(p).sum(axis=1) -
                                  np.abs(q).sum(axis=1)))
            quant = {str(k): x['quantized_sha'][name][str(k)] ==
                                y['quantized_sha'][name][str(k)]
                     for k in ROUND_DIGITS}
            z = {'raw_hash_equal': x['raw_sha'][name] == y['raw_sha'][name],
                 'different_elements': int(np.count_nonzero(diff)),
                 'max_abs_diff': float(np.max(diff)),
                 'mean_abs_diff': float(np.mean(diff)),
                 'sign_disagreements_gt_1e8': int(np.count_nonzero(direction)),
                 'max_gross_diff': float(gross),
                 'rounded_hash_equal': quant,
                 'first_differences': [
                     [int(i), int(j), float(p[i, j]), float(q[i, j])]
                     for i, j in np.argwhere(diff > 0)[:5]],
                 }
            outcome['fixtures'][label]['sources'][name] = z
            if z['max_abs_diff'] > 1e-8 or z['sign_disagreements_gt_1e8']:
                outcome['numeric_diagnostic_pass'] = False
        if x['activation'] != y['activation']:
            outcome['numeric_diagnostic_pass'] = False
        outcome['fixtures'][label]['activation_equal'] = (
            x['activation'] == y['activation'])
    return outcome

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--emit', metavar='PATH')
    p.add_argument('--compare', nargs=2, metavar=('OS22', 'OS24'))
    p.add_argument('--output', default='ai1253_crossos_forensic.json')
    args = p.parse_args()
    if bool(args.emit) == bool(args.compare):
        p.error('choose exactly one of --emit or --compare')
    if args.emit:
        result = emit()
        with open(args.emit, 'w') as f:
            json.dump(result, f, sort_keys=True, separators=(',', ':'),
                      allow_nan=False)
        for label, frame in result['fixtures'].items():
            print('AI1253_EMIT', label, 'ACTIVATION', frame['activation'],
                  'RAW_SHA', frame['raw_sha'])
    else:
        with open(args.compare[0]) as f:
            a = json.load(f)
        with open(args.compare[1]) as f:
            b = json.load(f)
        result = compare(a, b)
        with open(args.output, 'w') as f:
            json.dump(result, f, sort_keys=True, indent=2, allow_nan=False)
        for label, frame in result['fixtures'].items():
            for name, v in frame['sources'].items():
                print('AI1253_COMPARE', label, name, json.dumps(v, sort_keys=True))
        print('AI1253_DIAGNOSTIC_PASS', result['numeric_diagnostic_pass'])
        if not result['numeric_diagnostic_pass']:
            raise SystemExit(2)

if __name__ == '__main__':
    main()
