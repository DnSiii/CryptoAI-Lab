"""Read-only V99 Phase195-BK official paper provenance audit (DATA_ONLY).

Archive hashes identify artifact bytes, NOT authenticated exchange-time receipts.
"""
from __future__ import annotations
import hashlib
import json
import math
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

TRACKS = ('paper_v13_ledger.json', 'paper_core_comparison_v1_ledger.json',
          'paper_opportunity_v1_ledger.json', 'paper_combined_v1_ledger.json',
          'paper_v14_ledger.json', 'paper_v15_ledger.json',
          'paper_v16_ledger.json', 'paper_v99_ledger.json')


def strict_json(raw):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError('duplicate JSON key: ' + k)
            d[k] = v
        return d
    def reject(s):
        raise ValueError('nonfinite JSON: ' + s)
    x = json.loads(raw, object_pairs_hook=unique, parse_constant=reject)
    def check(v):
        if isinstance(v, float) and not math.isfinite(v):
            raise ValueError('nonfinite numeric value')
        if isinstance(v, dict):
            for q in v.values(): check(q)
        if isinstance(v, list):
            for q in v: check(q)
    check(x)
    return x


def rows(ledger):
    seq = ledger['equity_curve']
    if not isinstance(seq, list) or not seq:
        raise ValueError('empty equity curve')
    out = {}
    previous = None
    for row in seq:
        ts = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
        if ts.utcoffset() != timedelta(0):
            raise ValueError('UTC timestamp required')
        if previous is not None and ts - previous != timedelta(hours=1):
            raise ValueError('non-hourly/duplicate/unordered equity curve')
        out[row['timestamp']] = row
        previous = ts
    return out


def audit_zip(path):
    payload = Path(path).read_bytes()
    result = {'archive_sha256': hashlib.sha256(payload).hexdigest(),
              'tracks': {}, 'status': 'DATA_ONLY_HOLD',
              'publication_authorized': False, 'promotion_authorized': False,
              'exchange_receipts_authenticated': False}
    with zipfile.ZipFile(path) as z:
        for name in TRACKS:
            published = strict_json(z.read('reports/published_baseline/' + name))
            candidate = strict_json(z.read('reports/' + name))
            if published.get('mode') != 'PAPER_ONLY' or candidate.get('mode') != 'PAPER_ONLY':
                raise ValueError('paper-only required: ' + name)
            old, new = rows(published), rows(candidate)
            missing = sorted(set(old) - set(new))
            changed = sorted(t for t in set(old) & set(new) if old[t] != new[t])
            appended = sorted(set(new) - set(old))
            field_diffs = {}
            for t in changed:
                field_diffs[t] = {k: {'published': old[t].get(k), 'candidate': new[t].get(k)}
                                  for k in old[t].keys() | new[t].keys()
                                  if old[t].get(k) != new[t].get(k)}
            result['tracks'][name] = {
                'published_hours': len(old), 'candidate_hours': len(new),
                'missing_hours': missing, 'rewritten_hours': changed,
                'appended_hours': len(appended), 'changed_fields': field_diffs,
                'published_prefix_sha256': hashlib.sha256(json.dumps(
                    list(old.values()), sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            }
    return result


def compare_archives(paths):
    if len(paths) < 2:
        raise ValueError('at least two independent run archives required')
    audits = [audit_zip(p) for p in paths]
    invariants = {}
    for name in TRACKS:
        patterns = [a['tracks'][name]['changed_fields'] for a in audits]
        with_candidates = []
        for path in paths:
            with zipfile.ZipFile(path) as z:
                with_candidates.append(rows(strict_json(z.read('reports/' + name))))
        common = set.intersection(*(set(c) for c in with_candidates))
        drift = sorted(t for t in common if any(c[t] != with_candidates[0][t] for c in with_candidates[1:]))
        invariants[name] = {
            'candidate_shared_hours': len(common),
            'candidate_cross_run_drift_hours': len(drift),
            'candidate_cross_run_drift_first': drift[:5],
            'same_changed_rows_across_runs': all(p == patterns[0] for p in patterns[1:]),
            'same_published_prefix_sha256': len({a['tracks'][name]['published_prefix_sha256'] for a in audits}) == 1,
            'rewritten_hours_per_run': [len(a['tracks'][name]['rewritten_hours']) for a in audits],
            'changed_timestamps': [a['tracks'][name]['rewritten_hours'] for a in audits],
        }
    return {'status': 'DATA_ONLY_HOLD', 'publication_authorized': False,
            'promotion_authorized': False, 'source_receipts_authenticated': False,
            'runs': audits, 'cross_run_invariants': invariants}


if __name__ == '__main__':
    print(json.dumps(compare_archives(sys.argv[1:]), indent=2))
