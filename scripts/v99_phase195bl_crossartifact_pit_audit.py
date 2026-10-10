"""Read-only cross-artifact temporal conflicts; never a promotion gate."""
from __future__ import annotations
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime, timedelta


def timestamp(s):
    t = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if t.utcoffset() != timedelta(0):
        raise ValueError('explicit UTC required')
    return t


def read_zip(path, name):
    with zipfile.ZipFile(path) as z:
        return json.loads(z.read(name))


def audit(old, new, universes):
    names = ('r98', 'f1', 'f3', 'f7', 'f12')
    receipts = {}
    for universe in universes:
        for symbol, meta in universe['symbols'].items():
            if meta.get('source') == 'dynamic_binance_discovery':
                receipts.setdefault(symbol, []).append(timestamp(meta['discovered_at_utc']))
    changes = {}
    for name in names:
        a = {(x['timestamp'], x['symbol']): x for x in old['variants'][name]['operations']}
        b = {(x['timestamp'], x['symbol']): x for x in new['variants'][name]['operations']}
        only = [b[k] for k in b.keys() - a.keys()]
        conflicts = [dict(symbol=x['symbol'], timestamp=x['timestamp']) for x in only
                     if x['symbol'] in receipts and timestamp(x['timestamp']) < min(receipts[x['symbol']])]
        changes[name] = {
            'old_operations': len(a), 'new_operations': len(b),
            'old_new_overlap': len(a.keys() & b.keys()),
            'changed_shared_operations': sum(a[k] != b[k] for k in a.keys() & b.keys()),
            'new_only_symbols': dict(Counter(x['symbol'] for x in only)),
            'new_only_before_later_observed_receipt': conflicts,
            'operations_capped': len(a) >= 1500 or len(b) >= 1500,
        }
    reissued = {s: [t.isoformat() for t in times] for s, times in receipts.items()
                if len(set(times)) > 1}
    return {'status': 'DATA_ONLY_HOLD', 'promotion_authorized': False,
            'publication_authorized': False, 'receipt_source_authenticated': False,
            'cross_artifact_observation_only': True,
            'later_observed_receipt_is_not_original_asof_proof': True,
            'receipt_reissued_symbols': reissued, 'variants': changes}


if __name__ == '__main__':
    old, new = [read_zip(p, 'reports/paper_v99_research_ledger.json') for p in sys.argv[1:3]]
    universes = [read_zip(p, 'state/paper_v15_universe.json') for p in sys.argv[3:]]
    print(json.dumps(audit(old, new, universes), indent=2))
