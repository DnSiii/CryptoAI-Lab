"""Fail-closed read-only official paper prefix gate; never edits published ledgers."""
from __future__ import annotations
import json, sys, zipfile
from datetime import datetime, timezone, timedelta

TRACKS = ('v13', 'v14', 'v15', 'v16', 'v99', 'opportunity_v1', 'core_comparison_v1', 'combined_v1')


def strict_index(rows):
    out = {}
    last = None
    for row in rows:
        t = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
        if t.tzinfo is None or t.utcoffset() != timedelta(0):
            raise ValueError('UTC required')
        if last is not None and t <= last:
            raise ValueError('duplicate or unordered equity timestamps')
        last = t
        out[row['timestamp']] = row
    return out


def audit(z):
    tracks = {}
    for track in TRACKS:
        name = f'paper_{track}_ledger.json'
        old = json.loads(z.read('reports/published_baseline/' + name))
        new = json.loads(z.read('reports/' + name))
        if old.get('mode') != 'PAPER_ONLY' or new.get('mode') != 'PAPER_ONLY':
            raise ValueError('paper-only mode required')
        baseline = strict_index(old['equity_curve'])
        candidate = strict_index(new['equity_curve'])
        missing = sorted(set(baseline) - set(candidate))
        changed = sorted(k for k in baseline.keys() & candidate.keys() if baseline[k] != candidate[k])
        tracks[track] = {'published_hours': len(baseline), 'candidate_hours': len(candidate),
                         'missing_published': missing, 'rewritten_published': changed,
                         'first_changed_fields': sorted(k for k in set(baseline[changed[0]]) | set(candidate[changed[0]])
                                                        if baseline[changed[0]].get(k) != candidate[changed[0]].get(k)) if changed else []}
    safe = all(not t['missing_published'] and not t['rewritten_published'] for t in tracks.values())
    return {'status': 'PREFIX_PASS_NOT_PROMOTION' if safe else 'DATA_ONLY_HOLD',
            'publication_authorized': False, 'promotion_authorized': False,
            'tracks': tracks}


def audit_zip(path):
    with zipfile.ZipFile(path) as z:
        return audit(z)


if __name__ == '__main__':
    print(json.dumps(audit_zip(sys.argv[1]), ensure_ascii=False, indent=2))
    sys.exit(2 if audit_zip(sys.argv[1])['status'] == 'DATA_ONLY_HOLD' else 0)
