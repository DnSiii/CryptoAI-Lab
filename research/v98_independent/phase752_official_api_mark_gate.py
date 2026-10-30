#!/usr/bin/env python3
"""V98 Independent Phase752: official funding API mark verification, source-only.

Runs only after the exact Phase751 100-archive receipt. Four Clean-4 assets,
2022-12 through 2024-12 only. No PnL, 2025 reads, or external benchmarks.
"""
from __future__ import annotations
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from decimal import Decimal
from pathlib import Path
from phase751_official_archive_gate import ROOT, ASSETS, START, END, STEP, native, audit as fresh_archive_audit

API = 'https://fapi.binance.com/fapi/v1/fundingRate'
PASS_ARCHIVES = 'PASS_OFFICIAL_100_TRAINING_ARCHIVES_NATIVE_ONLY'
PASS_ALL = 'PASS_OFFICIAL_100_ARCHIVES_9144_API_MARKS_SOURCE_ONLY'


def fetch(url: str) -> bytes:
    if not url.startswith(API+'?'):
        raise ValueError('API origin not allowed')
    req = urllib.request.Request(url, headers={'User-Agent': 'V98Independent-Phase752/1.0'})
    with urllib.request.urlopen(req, timeout=45) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError('API status/redirect mismatch')
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError('API response too large')
    return raw


def verify_asset(asset: str, expected: dict, download=fetch):
    if asset not in ASSETS or len(expected) != 2286:
        raise ValueError('strict Clean-4 funding training universe required')
    cursor, marks, pages = START, {}, 0
    while cursor < END:
        if pages >= 4:
            raise ValueError('official API pagination budget exceeded')
        query = urllib.parse.urlencode({'symbol': asset, 'startTime': cursor,
                                        'endTime': END-1, 'limit': 1000})
        rows = json.loads(download(API+'?'+query))
        pages += 1
        if not isinstance(rows, list) or not rows or len(rows) > 1000:
            raise ValueError('official API incomplete/malformed batch')
        last = cursor - 1
        for row in rows:
            t = row.get('fundingTime')
            if (row.get('symbol') != asset or type(t) is not int or
                    not cursor <= t < END or t <= last):
                raise ValueError('API out-of-order/future funding event')
            slot = (t // STEP) * STEP
            rate = Decimal(str(row['fundingRate']))
            mark = Decimal(str(row['markPrice']))
            if (slot not in expected or expected[slot] != (t, rate) or
                    slot in marks or not rate.is_finite() or
                    not mark.is_finite() or mark <= 0):
                raise ValueError('official API mark/rate mismatch')
            marks[slot] = str(mark)
            last = t
        cursor = last + 1
        if len(rows) < 1000:
            break
    if set(marks) != set(expected):
        raise ValueError('official API settlement coverage mismatch')
    return {'events': len(marks), 'api_pages': pages,
            'mark_sha256': hashlib.sha256(json.dumps(marks, sort_keys=True).encode()).hexdigest()}


def run(root=ROOT):
    root = Path(root)
    result = {'phase': 752, 'decision': 'BLOCKED_API_MARK_SOURCE',
              'vendor_origin_attested': False, 'historical_pnl_computed': False,
              'validation_2025_read': False, 'holdout_accessed': False,
              'promotion_eligible': False, 'assets': {}}
    try:
        receipt = json.loads((root/'phase751_official_archive_result.json').read_text())
        if (receipt.get('decision') != PASS_ARCHIVES or
                set(receipt.get('assets', {})) != set(ASSETS) or
                sum(v.get('archives', 0) for v in receipt['assets'].values()) != 100 or
                sum(v.get('settlements', 0) for v in receipt['assets'].values()) != 9144):
            raise PermissionError('Phase751 official archive receipt not complete')
        # Cached Phase751 receipts alone cannot attest vendor origin. Re-fetch
        # every official monthly ZIP and CHECKSUM in this invocation.
        for asset in ASSETS:
            expected = native(asset)
            fresh = fresh_archive_audit(asset, expected)
            if fresh.get('archives') != 25 or fresh.get('settlements') != 2286:
                raise ValueError('fresh archive verification incomplete')
            result['assets'][asset] = verify_asset(asset, expected)
            result['assets'][asset]['fresh_archives_verified'] = fresh['archives']
        if sum(v['fresh_archives_verified'] for v in result['assets'].values()) != 100:
            raise ValueError('fresh archive count mismatch')
        if sum(x['events'] for x in result['assets'].values()) != 9144:
            raise ValueError('official API event count mismatch')
        result.update(decision=PASS_ALL, vendor_origin_attested=True)
    except Exception as exc:
        result['reason'] = f'{type(exc).__name__}: {str(exc)[:350]}'
    return result


if __name__ == '__main__':
    output = run()
    (ROOT/'phase752_official_api_mark_result.json').write_text(
        json.dumps(output, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'decision': output['decision'], 'reason': output.get('reason')}))
    sys.exit(0 if output['vendor_origin_attested'] else 2)
