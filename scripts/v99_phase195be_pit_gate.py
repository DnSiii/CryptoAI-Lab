"""Read-only V99 Phase195-BE PIT gate; never authorizes trading/promotion."""
from __future__ import annotations
import json, zipfile, sys
from datetime import datetime, timedelta, timezone


def utc(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError('explicit UTC timestamp required')
    return t.astimezone(timezone.utc)


def causal_start(first_seen):
    t = utc(first_seen)
    return t.replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)


def read(path):
    with zipfile.ZipFile(path) as z:
        return (json.loads(z.read('state/paper_v15_universe.json')),
                json.loads(z.read('reports/paper_v15_ledger.json')))


def scan(universe, ledger):
    if ledger.get('mode') != 'PAPER_ONLY':
        raise ValueError('paper-only required')
    dynamic = {k: v for k, v in universe['symbols'].items()
               if v.get('source') == 'dynamic_binance_discovery'}
    bad = [k for k, v in dynamic.items()
           if utc(v['eligible_after_timestamp']) < causal_start(v['discovered_at_utc'])]
    unsafe = []
    previous = None
    count = 0
    for row in ledger['decisions']:
        t = utc(row['timestamp'])
        if previous is not None and t <= previous:
            raise ValueError('unsorted or duplicate decision')
        previous = t
        for adj in row.get('adjustments', []):
            count += 1
            symbol = adj['symbol']
            if symbol in dynamic and t < causal_start(dynamic[symbol]['discovered_at_utc']):
                unsafe.append((row['timestamp'], symbol))
    return {'symbols': len(universe['symbols']), 'dynamic': len(dynamic),
            'noncausal_legacy_eligibility': len(bad), 'decision_rows': len(ledger['decisions']),
            'adjustments': count, 'unsafe_observed': unsafe,
            'partial_decision_window': True,
            'status': 'HOLD' if bad or unsafe else 'OBSERVED_ONLY_PASS_NOT_CERTIFICATION'}


def compare(old, new):
    a, b = old[0]['symbols'], new[0]['symbols']
    fields = ('source', 'start_month', 'onboard_date', 'discovered_at_utc', 'eligible_after_timestamp')
    changed = {s: [f for f in fields if a[s].get(f) != b[s].get(f)]
               for s in a.keys() & b.keys()}
    changed = {s: v for s, v in changed.items() if v}
    old_scan, new_scan = scan(*old), scan(*new)
    return {'previous': old_scan, 'candidate': new_scan, 'changed_provenance': changed,
            'removed': sorted(a.keys() - b.keys()), 'added': sorted(b.keys() - a.keys()),
            'decision': 'DATA_ONLY_HOLD' if changed or a.keys()-b.keys() or
                        old_scan['status'] == 'HOLD' or new_scan['status'] == 'HOLD'
                        else 'PREFIX_PASS_NOT_PROMOTION',
            'promotion_authorized': False, 'publication_authorized': False}


if __name__ == '__main__':
    result = compare(read(sys.argv[1]), read(sys.argv[2]))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result['decision'] == 'DATA_ONLY_HOLD':
        sys.exit(2)
