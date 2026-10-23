#!/usr/bin/env python3
"""V98 Independent Phase991: source-only, preregistered BTC 2023-02 tri-source audit.

No historical PnL, no source substitution, no relaxed Phase797 gate, no 2025+.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from phase797_official_mark_archive_attestor import BASE, calendar_ms, parse_zip
from phase206_acquire_funding_archive import checksum_expected

ASSET, MONTH = 'BTCUSDT', '2023-02'
MONTH_NAME = f'{ASSET}-1h-{MONTH}.zip'
DAILY = 'https://data.binance.vision/data/futures/um/daily/markPriceKlines'
API = 'https://fapi.binance.com/fapi/v1/markPriceKlines'
TIMES = calendar_ms(MONTH)
OUT = Path(__file__).resolve().parent / 'phase991_source_triangulation_result.json'
PRICE_COLS = (0, 1, 2, 3, 4, 6)
ALL_COLS = tuple(range(12))

def get(url, cap=10_000_000):
    if not (url.startswith(BASE + '/') or url.startswith(DAILY + '/') or url.startswith(API + '?')):
        raise ValueError('FORBIDDEN_SOURCE_URL')
    request = urllib.request.Request(url, headers={'User-Agent': 'V98-Independent-Phase991/1.0'})
    with urllib.request.urlopen(request, timeout=35) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError('SOURCE_REDIRECT_OR_HTTP_ERROR')
        raw = response.read(cap + 1)
    if len(raw) > cap:
        raise ValueError('SOURCE_SIZE_LIMIT')
    return raw

def authenticated_zip(base, name):
    url = f'{base}/{ASSET}/1h/{name}'
    expected = checksum_expected(get(url + '.CHECKSUM', 4096), name)
    raw = get(url)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected:
        raise ValueError('OFFICIAL_SHA256_MISMATCH')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.namelist() != [name[:-4] + '.csv']:
            raise ValueError('ZIP_MEMBER_MISMATCH')
        member = archive.infolist()[0]
        if member.file_size > 10_000_000:
            raise ValueError('DECOMPRESSED_SIZE_LIMIT')
        with archive.open(member) as stream:
            rows = list(csv.reader(io.TextIOWrapper(stream, encoding='utf-8-sig', newline='')))
    if rows and rows[0] and rows[0][0].strip().lower() == 'open_time':
        header = tuple(v.strip().lower() for v in rows.pop(0))
        if len(header) != 12 or header[:5] != ('open_time','open','high','low','close') or header[6] != 'close_time':
            raise ValueError('CSV_HEADER_MISMATCH')
    return raw, rows, digest

def inspect(rows, expected):
    faults, by_time = [], {}
    for i, row in enumerate(rows):
        kinds = []
        if len(row) != 12:
            kinds.append('ROW_WIDTH')
        else:
            try:
                timestamp, close_time = int(row[0]), int(row[6])
                o, h, l, c = (Decimal(v) for v in row[1:5])
                if i >= len(expected) or timestamp != expected[i]: kinds.append('UTC_ORDER_OR_COVERAGE')
                if close_time != timestamp + 3599999: kinds.append('CLOSE_TIME')
                if not all(v.is_finite() for v in (o,h,l,c)): kinds.append('NONFINITE')
                elif l <= 0 or l > min(o,c) or h < max(o,c) or h < l: kinds.append('OHLC_GEOMETRY')
                if timestamp in by_time: kinds.append('DUPLICATE_TIMESTAMP')
                else: by_time[timestamp] = row
            except (ValueError, InvalidOperation, IndexError, TypeError):
                kinds.append('INVALID_VALUE')
        if kinds:
            faults.append({'index':i,'expected_utc':datetime.fromtimestamp(expected[i]/1000,timezone.utc).isoformat() if i<len(expected) else None,'faults':kinds,'raw_first7':row[:7]})
    if len(rows) != len(expected):
        faults.append({'index':len(rows),'faults':['COVERAGE_COUNT'],'actual':len(rows),'expected':len(expected)})
    return {'rows':len(rows),'fault_count':len(faults),'first_faults':faults[:20]}, by_time

def diff(left, right, fields=PRICE_COLS):
    missing_left = sorted(set(right)-set(left))
    missing_right = sorted(set(left)-set(right))
    differences = []
    for t in sorted(set(left)&set(right)):
        a,b=left[t],right[t]
        cols=[]
        for col in fields:
            try:
                if Decimal(str(a[col])) != Decimal(str(b[col])): cols.append(col)
            except (IndexError, InvalidOperation, ValueError, TypeError): cols.append(col)
        if cols:
            differences.append({'utc':datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),'columns':cols,'left_first7':a[:7],'right_first7':b[:7]})
    return {'shared':len(set(left)&set(right)), 'missing_left':len(missing_left), 'missing_right':len(missing_right), 'different_rows':len(differences), 'first_differences':differences[:20]}

def fetch_day(day):
    name = f'{ASSET}-1h-{MONTH}-{day:02d}.zip'
    _, rows, digest = authenticated_zip(DAILY, name)
    expected = TIMES[(day-1)*24:day*24]
    audit, mapped = inspect(rows, expected)
    return day, audit, mapped, digest

def run():
    receipt = {'phase':991,'asset':ASSET,'month':MONTH,'source_only':True,
        'historical_pnl_computed':False,'economic_clearance':False,
        'validation_2025_read':False,'holdout_accessed':False,
        'external_benchmarks_used':False,'source_substitution_authorized':False,
        'frozen_gate_changed':False,'decision':'QUARANTINE_PENDING_EVIDENCE'}
    def persist():
        OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    try:
        raw, monthly, digest = authenticated_zip(BASE, MONTH_NAME)
        receipt['monthly_sha256'] = digest
        receipt['monthly_audit'], month_map = inspect(monthly, TIMES)
        try:
            parse_zip(raw, MONTH_NAME, MONTH)
            receipt['unchanged_phase797_parser'] = 'PASS'
        except Exception as exc:
            receipt['unchanged_phase797_parser'] = type(exc).__name__ + ': ' + str(exc)[:180]
        persist()
        daily_map, day_sha, day_audits, day_errors = {}, {}, {}, {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(fetch_day, day): day for day in range(1,29)}
            for future in as_completed(futures):
                day = futures[future]
                try:
                    _, audit, mapped, sha = future.result()
                    day_audits[str(day)] = audit
                    day_sha[str(day)] = sha
                    for timestamp, row in mapped.items():
                        if timestamp in daily_map:
                            day_errors[str(day)] = 'CROSS_DAY_DUPLICATE_TIMESTAMP'
                        else:
                            daily_map[timestamp] = row
                except Exception as exc:
                    day_errors[str(day)] = type(exc).__name__ + ': ' + str(exc)[:180]
                receipt['days_checked'] = len(day_sha) + len(day_errors)
                persist()
        receipt['daily_verified_count'] = len(day_sha)
        receipt['daily_sha256'] = dict(sorted(day_sha.items(),key=lambda x:int(x[0])))
        receipt['daily_errors'] = day_errors
        receipt['daily_faults'] = {day:audit for day,audit in day_audits.items() if audit['fault_count']}
        receipt['monthly_vs_daily'] = diff(month_map,daily_map,ALL_COLS)
        persist()
        query = urllib.parse.urlencode({'symbol':ASSET,'interval':'1h','startTime':TIMES[0], 'endTime':TIMES[-1]+3599999,'limit':1000})
        try:
            api_raw = get(API+'?'+query,2_000_000)
            api = json.loads(api_raw)
            if not isinstance(api,list): raise ValueError('API_SCHEMA')
            api_rows = [[str(v) for v in row] for row in api]
            receipt['api_audit'], api_map = inspect(api_rows,TIMES)
            receipt['api_payload_sha256'] = hashlib.sha256(api_raw).hexdigest()
            receipt['monthly_vs_api'] = diff(month_map,api_map)
            receipt['daily_vs_api'] = diff(daily_map,api_map)
        except Exception as exc:
            receipt['api_error'] = type(exc).__name__ + ': ' + str(exc)[:180]
        complete = (len(day_sha)==28 and not day_errors and not receipt['daily_faults'] and
            receipt['monthly_audit']['fault_count']==0 and receipt['unchanged_phase797_parser']=='PASS' and
            receipt['monthly_vs_daily']['shared']==672 and
            all(receipt['monthly_vs_daily'][k]==0 for k in ('missing_left','missing_right','different_rows')) and
            'api_error' not in receipt and receipt['api_audit']['fault_count']==0 and
            receipt['monthly_vs_api']['shared']==672 and receipt['daily_vs_api']['shared']==672 and
            all(receipt[s][k]==0 for s in ('monthly_vs_api','daily_vs_api') for k in ('missing_left','missing_right','different_rows')))
        receipt['decision'] = 'THREE_SOURCE_CONSISTENT_DIAGNOSTIC_ONLY' if complete else 'QUARANTINE_SOURCE_CONFLICT_OR_INCOMPLETE'
    except Exception as exc:
        receipt['error'] = type(exc).__name__ + ': ' + str(exc)[:180]
    persist()
    print(json.dumps({'phase':991,'decision':receipt['decision'],'monthly_audit':receipt.get('monthly_audit'),'monthly_vs_daily':receipt.get('monthly_vs_daily'),'monthly_vs_api':receipt.get('monthly_vs_api'),'daily_errors':receipt.get('daily_errors'),'api_error':receipt.get('api_error'),'error':receipt.get('error')},sort_keys=True))
    return receipt

if __name__=='__main__':
    run()
    raise SystemExit(2)  # Diagnostics cannot authorize economic PnL.
