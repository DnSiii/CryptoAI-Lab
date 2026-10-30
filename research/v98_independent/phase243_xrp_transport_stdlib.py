#!/usr/bin/env python3
"""V98 Phase243 isolated Binance archive transport (stdlib only).

DATA_ONLY: frozen XRP training source capture. No alpha, holdout, source repair,
or changes to V16/V99. Binance checksum is not a publisher signature.
"""
from __future__ import annotations
import os
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def _inside(root: Path, target: Path) -> None:
    root, target = Path(root).absolute(), Path(target).absolute()
    if 'v98_independent' not in root.parts or not target.is_relative_to(root):
        raise ValueError('V98-only containment required')
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('symlink in source root')
    p = root
    for part in target.relative_to(root).parts:
        p = p / part
        if p.is_symlink():
            raise ValueError('symlink in source path')


def _atomic(dest: Path, payload: bytes) -> None:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.v98_xrp_capture_', dir=dest.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, dest)
    finally:
        Path(temp).unlink(missing_ok=True)


def _download(url: str, cap: int) -> bytes:
    parsed = urlparse(url)
    if (parsed.scheme != 'https' or parsed.netloc != 'data.binance.vision'
            or not parsed.path.startswith('/data/futures/um/')):
        raise ValueError('unapproved source URL')
    if type(cap) is not int or not 0 < cap <= 12_000_000:
        raise ValueError('invalid byte cap')
    request = Request(url, headers={'User-Agent': 'V98-Independent-Phase243-Source/1.0'})
    with urlopen(request, timeout=45) as response:
        final = urlparse(response.geturl())
        if final.scheme != 'https' or final.netloc != 'data.binance.vision':
            raise ValueError('unexpected cross-origin redirect')
        payload = response.read(cap + 1)
    if not payload or len(payload) > cap:
        raise ValueError('empty/oversized source response')
    return payload


def _fetch_with_retry(getter, url: str, cap: int, *, attempts: int = 3,
                      sleeper=time.sleep) -> bytes:
    if type(attempts) is not int or not 1 <= attempts <= 5:
        raise ValueError('invalid retry count')
    for index in range(attempts):
        try:
            return getter(url, cap)
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or index + 1 == attempts:
                raise
        except (OSError, TimeoutError):
            if index + 1 == attempts:
                raise
        sleeper(min(2 ** index, 4))
    raise RuntimeError('unreachable transport retry')
