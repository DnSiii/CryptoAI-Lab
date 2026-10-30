#!/usr/bin/env python3
"""V98 Independent Phase798: verify Phase797 receipt + materialize 1h conservative funding.

Source-only bridge, not a PnL authorization. Production caller MUST run Phase797
freshly in the same process before invoking load(); cached receipts are invalid.
"""
from __future__ import annotations
import csv, hashlib, json
from decimal import Decimal
from pathlib import Path
from phase797_official_mark_archive_attestor import PASS
from phase751_official_archive_gate import ASSETS, START, END, STEP
from phase728_g_staged_training_funding import panel_from_marks

COLUMNS=('asset','funding_slot_ms','funding_time_ms','funding_rate','mark_low','mark_high','conservative_mark')


def load(receipt:dict, raw:bytes):
    if (not isinstance(receipt,dict) or receipt.get('decision')!=PASS or
        receipt.get('vendor_origin_attested') is not True or
        receipt.get('api_mark_attested') is not False or
        receipt.get('official_mark_candle_bound_attested') is not True or
        receipt.get('verified_funding_monthly_archives')!=100 or
        receipt.get('verified_mark_monthly_archives')!=100 or
        receipt.get('verified_asset_events')!=9144 or
        receipt.get('mark_interval')!='1h' or
        receipt.get('mark_conservatism')!='high_on_debit_low_on_credit_long_only' or
        any(receipt.get(k) is not False for k in ('historical_pnl_computed','promotion_eligible','validation_2025_read','holdout_accessed','external_benchmarks_used'))):
        raise PermissionError('Phase798 requires complete distinct Phase797 source-only receipt')
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=receipt.get('conservative_bounds_csv_sha256'):
        raise PermissionError('Phase797 canonical conservative funding CSV digest mismatch')
    try:
        decoded=raw.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('Phase797 non-UTF8 CSV') from exc
    reader=csv.DictReader(decoded.splitlines())
    if tuple(reader.fieldnames or ())!=COLUMNS:
        raise ValueError('Phase797 canonical funding schema mismatch')
    marks={a:{} for a in ASSETS}
    for row in reader:
        if set(row)!=set(COLUMNS):raise ValueError('Phase797 CSV unexpected field')
        a=row['asset']
        if a not in ASSETS:raise ValueError('Phase797 Clean-4 only')
        slot=int(row['funding_slot_ms']); t=int(row['funding_time_ms'])
        rate=Decimal(row['funding_rate']);lo=Decimal(row['mark_low'])
        hi=Decimal(row['mark_high']); bound=Decimal(row['conservative_mark'])
        if (slot not in range(START,END,STEP) or slot in marks[a] or
            not slot<=t<=slot+29 or not all(x.is_finite() for x in (rate,lo,hi,bound)) or
            lo<=0 or hi<lo or bound!=(hi if rate>=0 else lo)):
            raise ValueError('Phase797 funding calendar/mark conservatism mismatch')
        marks[a][slot]=(t,rate,bound)
    if any(set(marks[a])!=set(range(START,END,STEP)) for a in ASSETS):
        raise ValueError('Phase797 funding event coverage mismatch')
    return panel_from_marks(marks)


def run_fresh_source_only():
    """Must never read an existing receipt before fresh official attestation."""
    from phase797_official_mark_archive_attestor import ROOT,run
    if run()!=0:raise PermissionError('fresh official Phase797 attestation failed')
    receipt=json.loads((ROOT/'phase797_official_mark_archive_receipt.json').read_text())
    raw=(ROOT/'phase797_conservative_training_funding_bounds.csv').read_bytes()
    return load(receipt,raw),receipt
