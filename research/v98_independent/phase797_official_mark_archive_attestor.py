#!/usr/bin/env python3
"""V98 Independent Phase797: independent official mark-candle SOURCE-ONLY attestation.

Only Clean-4 Dec-2022..Dec-2024. Never calculates PnL, touches 2025+, or promotes.
A separate receipt proves conservative 1h funding mark bounds, NOT API marks.
"""
from __future__ import annotations
import calendar, csv, hashlib, io, json, sys, time, urllib.request, zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from phase751_official_archive_gate import ROOT, ASSETS, MONTHS, START, END, STEP, native, audit
from phase206_acquire_funding_archive import checksum_expected

BASE = 'https://data.binance.vision/data/futures/um/monthly/markPriceKlines'
PASS = 'PASS_OFFICIAL_100_MARK_ARCHIVES_9144_CONSERVATIVE_BOUNDS_SOURCE_ONLY'


def download(url):
    if not url.startswith(BASE + '/') or not (url.endswith('.zip') or url.endswith('.zip.CHECKSUM')):
        raise ValueError('V98 mark archive origin/path forbidden')
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'V98-Independent-Phase797/1.0'})
            with urllib.request.urlopen(req, timeout=50) as response:
                if response.status != 200 or response.geturl() != url:
                    raise ValueError('official mark URL redirect/status mismatch')
                raw = response.read(10_000_001)
            if len(raw) > 10_000_000:
                raise ValueError('mark archive exceeds fixed size budget')
            return raw
        except (TimeoutError, OSError) as exc:
            last = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f'official mark transport failed: {type(last).__name__}: {last}')


def calendar_ms(month):
    if month not in MONTHS:
        raise ValueError('month outside locked pre-2025 training universe')
    year, mon = map(int, month.split('-'))
    first = int(datetime(year, mon, 1, tzinfo=timezone.utc).timestamp() * 1000)
    return tuple(first + i * 3_600_000 for i in range(calendar.monthrange(year, mon)[1] * 24))


def parse_zip(raw, filename, month):
    expected = calendar_ms(month)
    bounds = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if names != [filename[:-4] + '.csv']:
            raise ValueError('mark ZIP must contain exactly its canonical CSV')
        with archive.open(names[0]) as stream:
            rows = csv.reader(io.TextIOWrapper(stream, encoding='utf-8-sig', newline=''))
            count = 0
            for row in rows:
                if count == 0 and row and row[0].strip().lower() == 'open_time':
                    names = tuple(x.strip().lower() for x in row)
                    if len(names) != 12 or names[:5] != ('open_time','open','high','low','close') or names[6] != 'close_time':
                        raise ValueError('unrecognized mark CSV header schema')
                    continue
                if count >= len(expected) or len(row) != 12:
                    raise ValueError('mark candle schema/row count mismatch')
                try:
                    timestamp = int(row[0]); close_time = int(row[6])
                    o, h, l, c = (Decimal(x) for x in row[1:5])
                except (ValueError, ArithmeticError) as exc:
                    raise ValueError('invalid mark OHLC/timestamp') from exc
                if (timestamp != expected[count] or close_time != timestamp + 3_599_999 or
                    not all(x.is_finite() for x in (o,h,l,c)) or l <= 0 or
                    l > min(o,c) or h < max(o,c)):
                    raise ValueError('mark UTC chronology/geometry mismatch')
                if timestamp % STEP == 0:
                    bounds[timestamp] = (l, h)
                count += 1
            if count != len(expected):
                raise ValueError('mark monthly hour coverage incomplete')
    return bounds


def verify_month(asset, month, get=download):
    if asset not in ASSETS or month not in MONTHS:
        raise ValueError('Clean-4 training-only asset/month required')
    name = f'{asset}-1h-{month}.zip'
    url = f'{BASE}/{asset}/1h/{name}'
    checksum = checksum_expected(get(url + '.CHECKSUM'), name)
    raw = get(url)
    sha = hashlib.sha256(raw).hexdigest()
    if sha != checksum:
        raise ValueError('official mark archive checksum mismatch')
    return parse_zip(raw, name, month), sha


def conservative_rows(expected, marks, asset):
    if set(expected) != set(range(START, END, STEP)) or set(marks) != set(expected):
        raise ValueError('native funding and mark settlement coverage mismatch')
    out = []
    for slot in sorted(expected):
        timestamp, rate = expected[slot]
        low, high = marks[slot]
        if not (slot <= timestamp <= slot + 29 and rate.is_finite() and low > 0 and high >= low):
            raise ValueError('native funding timestamp/mark bound mismatch')
        bound = high if rate >= 0 else low
        out.append((asset,slot,timestamp,str(rate),str(low),str(high),str(bound)))
    return out


def run():
    receipt = {'phase': 797, 'decision': 'BLOCKED_OFFICIAL_MARK_SOURCE',
        'vendor_origin_attested': False, 'api_mark_attested': False,
        'historical_pnl_computed': False, 'promotion_eligible': False,
        'validation_2025_read': False, 'holdout_accessed': False,
        'external_benchmarks_used': False}
    try:
        if len(MONTHS) != 25 or MONTHS[0] != '2022-12' or MONTHS[-1] != '2024-12':
            raise ValueError('frozen training calendar mismatch')
        expected = {a: native(a) for a in ASSETS}
        funding = {a: audit(a, expected[a]) for a in ASSETS}
        if sum(x['archives'] for x in funding.values()) != 100 or sum(x['settlements'] for x in funding.values()) != 9144:
            raise ValueError('100 fresh funding archives not authenticated')
        all_rows = []; digests = {}
        for asset in ASSETS:
            marks = {}; digests[asset] = {}
            for month in MONTHS:
                block, sha = verify_month(asset, month)
                if set(block) & set(marks):
                    raise ValueError('duplicate settlement-hour mark')
                marks.update(block)
                digests[asset][month] = sha
            all_rows.extend(conservative_rows(expected[asset], marks, asset))
        if len(all_rows) != 9144:
            raise ValueError('strict 9144 event count mismatch')
        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow(('asset','funding_slot_ms','funding_time_ms','funding_rate','mark_low','mark_high','conservative_mark'))
        writer.writerows(all_rows)
        raw = output.getvalue().encode('utf-8')
        receipt.update(decision=PASS, vendor_origin_attested=True,
            official_mark_candle_bound_attested=True,
            verified_funding_monthly_archives=100, verified_mark_monthly_archives=100,
            verified_asset_events=9144, mark_interval='1h',
            mark_conservatism='high_on_debit_low_on_credit_long_only',
            conservative_bounds_csv_sha256=hashlib.sha256(raw).hexdigest(),
            mark_zip_digest_manifest_sha256=hashlib.sha256(json.dumps(digests,sort_keys=True).encode()).hexdigest(),
            funding_manifest_sha256=hashlib.sha256(json.dumps(funding,sort_keys=True).encode()).hexdigest())
        (ROOT/'phase797_conservative_training_funding_bounds.csv').write_bytes(raw)
    except Exception as exc:
        receipt['reason'] = f'{type(exc).__name__}: {str(exc)[:350]}'
    (ROOT/'phase797_official_mark_archive_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,sort_keys=True))
    return 0 if receipt['decision'] == PASS else 2

if __name__ == '__main__':
    sys.exit(run())
