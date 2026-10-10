#!/usr/bin/env python3
"""V98-only Phase243 exhaustive training-source diagnostic; fail closed."""
from __future__ import annotations
import json
from pathlib import Path
from phase243_source_acquisition import acquire_one, _inside, _atomic
from phase243_binance_archive_ingest import ASSETS, MONTHS


def scan(root: Path, acquire=acquire_one) -> dict:
    root = Path(root)
    _inside(root, root)
    verified, failed = [], []
    for asset in ASSETS:
        for month in MONTHS:
            try:
                verified.append(acquire(root, asset, month))
            except Exception as exc:
                failed.append({'asset': asset, 'month': month,
                               'type': type(exc).__name__, 'detail': str(exc)[:900]})
    return {'engine': 'V98 Independent', 'phase': 243,
            'status': 'FAIL_SOURCE_ONLY' if failed else 'PASS_SOURCE_ONLY',
            'holdout_accessed': False, 'promotion_eligible': False,
            'expected': len(ASSETS)*len(MONTHS),
            'verified': len(verified), 'failures': failed,
            'verified_rows': sum(x['rows'] for x in verified),
            'verified_archive_hashes': [
                {'asset': x['asset'], 'month': x['month'], 'sha256': x['sha256']}
                for x in verified]}


def main() -> None:
    root = Path('research/v98_independent/phase243_archives')
    dest = Path('research/v98_independent/phase243_source_failure_sweep.json')
    _inside(Path('research/v98_independent'), dest)
    report = scan(root)
    _atomic(dest, (json.dumps(report, sort_keys=True, indent=2, allow_nan=False)+'\n').encode())
    print(json.dumps({'status': report['status'], 'verified': report['verified'],
                      'failures': len(report['failures'])}))
    if report['status'] != 'PASS_SOURCE_ONLY' or report['verified'] != 185 or report['verified_rows'] != 135240:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
