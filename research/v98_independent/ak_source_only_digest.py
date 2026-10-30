#!/usr/bin/env python3
"""AK source-only official Clean-4 cross-OS provenance receipt, no PnL."""
import argparse
import hashlib
import json
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official
from ak_slow_compound_sources import source_bundle

def run():
    frames, manifest = load_official()
    growth, opportunity, rv, stress, router = source_bundle(
        frames[3], frames[1], frames[2], frames[5], frames[6])
    names = ('growth', 'opportunity', 'relative_value', 'stress')
    digests = {}
    activation = {}
    for name, array in zip(names, (growth, opportunity, rv, stress)):
        a = np.round(array, 12).astype('<f8')
        digests[name] = hashlib.sha256(a.tobytes()).hexdigest()
        activation[name] = int(np.count_nonzero(
            np.sum(np.abs(a), axis=1) > 1e-12))
    states = router['state']
    digests['router'] = hashlib.sha256(
        '|'.join(states.tolist()).encode()).hexdigest()
    return {
        'architecture': 'AK',
        'historical_training_only': True,
        'historical_system_pnl_computed': False,
        'validation_2025_read': False,
        'source_manifest_sha256': hashlib.sha256(json.dumps(
            manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'source_sha256': digests,
        'active_hours': activation,
        'hours': int(len(states)),
        'decision': 'AK_SOURCE_ONLY_RECEIPT_NO_ECONOMIC_CLAIM',
    }

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    args = p.parse_args()
    result = run()
    with open(args.output, 'w') as f:
        json.dump(result, f, sort_keys=True, indent=2)
    print('AK_SOURCE_ONLY', json.dumps(result, sort_keys=True))
