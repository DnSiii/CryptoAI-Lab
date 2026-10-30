#!/usr/bin/env python3
"""V98 Independent Phase243: authenticated, training-only Binance ZIP acquisition.
DATA_ONLY: never reads 2026+, holdout, V16 or V99. Binance SHA256 sidecars
provide transport/source consistency, not a cryptographic publisher signature.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from phase243_binance_archive_ingest import ASSETS, MONTHS, MAX_MEMBER_BYTES, _parse_month

BASE = 'https://data.binance.vision/data/futures/um/monthly/klines'
CHECKSUM_PATTERN = re.compile(rb'([a-fA-F0-9]{64})[ \t]+\*?([^\s]+)[\r\n]*\Z')


def _inside(root: Path, target: Path) -> None:
    root, target = root.absolute(), target.absolute()
    if 'v98_independent' not in root.parts or not target.is_relative_to(root):
        raise ValueError('V98-only namespace and containment required')
    if any(x.is_symlink() for x in (root, *root.parents)):
        raise ValueError('symlink in root ancestry')
    x = root
    for part in target.relative_to(root).parts:
        x = x / part
        if x.is_symlink():
            raise ValueError('symlink in target ancestry')


def _download(url: str, cap: int) -> bytes:
    req = Request(url, headers={'User-Agent': 'V98-Independent-Phase243-Source/1.0'})
    with urlopen(req, timeout=45) as resp:
        final = urlparse(resp.geturl())
        if final.scheme != 'https' or final.netloc != 'data.binance.vision':
            raise ValueError('unexpected cross-origin redirect')
        data = resp.read(cap + 1)
    if not data or len(data) > cap:
        raise ValueError('empty or oversized network response')
    return data


def _atomic(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.v98_source_', dir=dest.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, dest)
    finally:
        Path(name).unlink(missing_ok=True)


def _fetch_with_retry(getter, url: str, cap: int, *, attempts: int = 3, sleeper=time.sleep) -> bytes:
    """Retry transport failures only; NEVER retry integrity/schema rejection."""
    if type(attempts) is not int or not 1 <= attempts <= 5:
        raise ValueError('invalid bounded retry budget')
    for attempt in range(attempts):
        try:
            return getter(url, cap)
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt + 1 == attempts:
                raise
        except (OSError, TimeoutError):
            if attempt + 1 == attempts:
                raise
        sleeper(min(2 ** attempt, 4))
    raise RuntimeError('unreachable transport retry state')


def _quarantine_rejected_checksum_verified(root: Path, asset: str, month: str,
                                          raw: bytes, sidecar_bytes: bytes,
                                          error: Exception) -> None:
    """Preserve checksum-matching rejected originals outside the verified input grid."""
    name = f'{asset}-1h-{month}.zip'
    folder = root / 'quarantine' / asset / month
    digest = hashlib.sha256(raw).hexdigest()
    metadata = {'engine': 'V98 Independent', 'phase': 243, 'asset': asset,
                'month': month, 'archive_sha256': digest,
                'source_authentication': 'provider checksum sidecar; not a signature',
                'validation': 'REJECTED_NO_ALPHA', 'holdout_accessed': False,
                'promotion_eligible': False, 'error_type': type(error).__name__,
                'error': str(error)[:1200]}
    contents = ((folder / name, raw),
                (folder / (name + '.CHECKSUM'), sidecar_bytes),
                (folder / 'rejection.json',
                 (json.dumps(metadata, sort_keys=True, indent=2) + '\n').encode()))
    for path, payload in contents:
        _inside(root, path)
        if path.exists():
            if not path.is_file() or path.read_bytes() != payload:
                raise ValueError('quarantine immutable evidence conflict')
        else:
            _atomic(path, payload)


def acquire_one(root: Path, asset: str, month: str, *, getter=_download,
                attempts: int = 3, sleeper=time.sleep) -> dict:
    if asset not in ASSETS or month not in MONTHS:
        raise ValueError('frozen training-only universe violated')
    name = f'{asset}-1h-{month}.zip'
    url = f'{BASE}/{asset}/1h/{name}'
    path = root / 'klines' / asset / '1h' / name
    sidecar = path.with_name(name + '.CHECKSUM')
    for p in (path, sidecar):
        _inside(root, p)
    check = _fetch_with_retry(getter, url + '.CHECKSUM', 2048, attempts=attempts, sleeper=sleeper)
    match = CHECKSUM_PATTERN.fullmatch(check)
    if not match or match.group(2) != name.encode('ascii'):
        raise ValueError('invalid Binance checksum sidecar')
    digest = match.group(1).decode('ascii').lower()
    cache_ok = False
    if path.is_file() and path.stat().st_size <= MAX_MEMBER_BYTES:
        with path.open('rb') as f:
            raw = f.read(MAX_MEMBER_BYTES + 1)
        cache_ok = bool(raw) and len(raw) <= MAX_MEMBER_BYTES and hashlib.sha256(raw).hexdigest() == digest
    if not cache_ok:
        raw = _fetch_with_retry(getter, url, MAX_MEMBER_BYTES, attempts=attempts, sleeper=sleeper)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('ZIP does not match publisher checksum')
    try:
        with tempfile.TemporaryDirectory(prefix='v98_source_parse_') as tmp:
            candidate = Path(tmp) / name
            candidate.write_bytes(raw)
            rows, evidence = _parse_month(candidate, asset, month)
            if evidence['archive_sha256'] != digest:
                raise ValueError('parse/source SHA256 divergence')
    except Exception as exc:
        _quarantine_rejected_checksum_verified(root, asset, month, raw, check, exc)
        raise
    for p in (path, sidecar):
        _inside(root, p)
    if not cache_ok:
        _atomic(path, raw)
    _atomic(sidecar, check)
    return {'asset': asset, 'month': month, 'sha256': digest,
            'member_sha256': evidence['member_sha256'], 'rows': len(rows),
            'bytes': len(raw), 'status': 'VERIFIED_CACHE' if cache_ok else 'VERIFIED_DOWNLOAD'}


def acquire_all(root: Path, *, getter=_download, attempts: int = 3, sleeper=time.sleep) -> dict:
    root = Path(root)
    _inside(root, root)
    results = [acquire_one(root, a, m, getter=getter, attempts=attempts, sleeper=sleeper)
               for a in ASSETS for m in MONTHS]
    if len(results) != 185 or sum(x['rows'] for x in results) != 135240:
        raise ValueError('incomplete frozen training grid')
    return {'engine': 'V98 Independent', 'phase': 243, 'holdout_accessed': False,
            'status': 'PASS_TRAINING_ARCHIVES_DATA_ONLY_NO_ALPHA',
            'source_authentication': 'provider SHA256 sidecar; not a digital signature',
            'archives': len(results), 'asset_hours': 135240, 'results': results}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--root', default='research/v98_independent/phase243_archives')
    p.add_argument('--attempts', type=int, default=3)
    p.add_argument('--out', default='research/v98_independent/phase243_acquisition_manifest.json')
    a = p.parse_args()
    root, out = Path(a.root), Path(a.out)
    _inside(root, root)
    _inside(Path('research/v98_independent'), out)
    result = acquire_all(root, attempts=a.attempts)
    _inside(Path('research/v98_independent'), out)
    _atomic(out, (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n').encode())
    print(json.dumps({'status': result['status'], 'archives': result['archives'], 'asset_hours': result['asset_hours']}))


if __name__ == '__main__':
    main()
