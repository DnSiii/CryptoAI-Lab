#!/usr/bin/env python3
"""V98 Phase243: capture three frozen, checksum-verified XRP source ZIPs.

DATA_ONLY: no holdout, alpha, source repair, or promotion. A successful capture
is NOT source adjudication. Existing contradictory data remains quarantined.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from phase243_source_acquisition import _download, _fetch_with_retry, _inside, _atomic

ROOT = Path('research/v98_independent')
URLS = {
    'monthly_1h': 'https://data.binance.vision/data/futures/um/monthly/klines/XRPUSDT/1h/XRPUSDT-1h-2023-11.zip',
    'daily_1h': 'https://data.binance.vision/data/futures/um/daily/klines/XRPUSDT/1h/XRPUSDT-1h-2023-11-14.zip',
    'daily_1m': 'https://data.binance.vision/data/futures/um/daily/klines/XRPUSDT/1m/XRPUSDT-1m-2023-11-14.zip',
}
CAP = 12_000_000
CHECKSUM = re.compile(rb'([0-9a-fA-F]{64})[ \t]+\\*?([^\\s]+)[\\r\\n]*\\Z')


def capture(root: Path, *, getter=_download, sleeper=None) -> dict:
    """Preserve original bytes; return a fail-closed source acquisition report."""
    root = Path(root)
    _inside(ROOT, root)
    if root.exists() and any(root.iterdir()):
        raise ValueError('immutable capture root already populated')
    result = {'engine': 'V98 Independent', 'phase': 243,
              'holdout_accessed': False, 'promotion_eligible': False,
              'status': 'INCONCLUSIVE_SOURCE_CAPTURE', 'sources': {}}
    try:
        for key, url in URLS.items():
            name = url.rsplit('/', 1)[-1]
            kwargs = {'attempts': 3}
            if sleeper is not None:
                kwargs['sleeper'] = sleeper
            sidecar = _fetch_with_retry(getter, url + '.CHECKSUM', 2048, **kwargs)
            match = CHECKSUM.fullmatch(sidecar)
            if not match or match.group(2) != name.encode('ascii'):
                raise ValueError(f'{key}: invalid publisher checksum sidecar')
            raw = _fetch_with_retry(getter, url, CAP, **kwargs)
            digest = hashlib.sha256(raw).hexdigest()
            if digest != match.group(1).decode('ascii').lower():
                raise ValueError(f'{key}: checksum mismatch')
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                members = z.infolist()
                if (len(members) != 1 or members[0].filename != name[:-4] + '.csv'
                        or members[0].is_dir() or members[0].file_size > CAP):
                    raise ValueError(f'{key}: unsafe or unexpected ZIP member')
                member = z.read(members[0])
            if not member or len(member) > CAP or b'\0' in member:
                raise ValueError(f'{key}: empty/oversized/binary CSV')
            for suffix, payload in (('', raw), ('.CHECKSUM', sidecar)):
                dest = root / (name + suffix)
                _inside(ROOT, dest)
                _atomic(dest, payload)
                if dest.read_bytes() != payload:
                    raise ValueError(f'{key}: source preservation mismatch')
            result['sources'][key] = {
                'archive_sha256': digest,
                'member_sha256': hashlib.sha256(member).hexdigest(),
                'bytes': len(raw), 'checksum_verified': True,
                'schema_and_economic_validity': 'NOT_YET_ADJUDICATED'}
        result['status'] = 'CAPTURED_UNADJUDICATED_NO_ALPHA'
    except Exception as exc:
        result['error_type'] = type(exc).__name__
        result['error'] = str(exc)[:600]
    _inside(ROOT, root / 'capture_manifest.json')
    _atomic(root / 'capture_manifest.json',
            (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', default='research/v98_independent/phase243_xrp_daily_source_capture')
    a = p.parse_args()
    report = capture(Path(a.out))
    print(json.dumps({'status': report['status'], 'sources': len(report['sources']),
                      'error': report.get('error')}, sort_keys=True))
    if report['status'] != 'CAPTURED_UNADJUDICATED_NO_ALPHA':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
