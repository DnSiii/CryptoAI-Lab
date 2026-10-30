#!/usr/bin/env python3
"""V98 Independent Phase955: bind N training receipt to original source artifacts.

No data acquisition, historical PnL calculation, signal changes, 2025 or
external benchmark access. Source files are read solely for SHA256 attestation.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from phase803_training_ohlc_official_replay import ASSETS, PINS, PASS as PASS_OHLC
from phase797_official_mark_archive_attestor import PASS as PASS_MARK
from phase952_n_validation_gate import authorize_separate_validation

ROOT = Path(__file__).resolve().parent


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _hex_digest(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _read_json(path: Path):
    obj = json.loads(path.read_text())
    if not isinstance(obj, dict):
        raise PermissionError('source receipt is not an object: ' + path.name)
    return obj


def bind_training_source_evidence(root=ROOT):
    root = Path(root)
    training = _read_json(root / 'phase940_n_official_90cell_hourly_result.json')
    ohlc = _read_json(root / 'phase803_official_training_ohlc_receipt.json')
    mark = _read_json(root / 'phase797_official_mark_archive_receipt.json')
    if ohlc.get('decision') != PASS_OHLC or ohlc.get('vendor_origin_attested') is not True:
        raise PermissionError('OHLC source receipt is not authenticated')
    if set(ohlc.get('assets', {})) != set(ASSETS):
        raise PermissionError('Clean-4 asset registry mismatch')
    for asset in ASSETS:
        entry = ohlc['assets'][asset]
        pin, size = PINS[asset]
        if entry.get('sha256') != pin or entry.get('hours') != 18288 or entry.get('monthly_archives') != 25:
            raise PermissionError('OHLC receipt asset pin/count mismatch: ' + asset)
        if not _hex_digest(entry.get('archive_digest_manifest_sha256')):
            raise PermissionError('OHLC archive manifest missing: ' + asset)
        raw = (root / 'phase243_clean4_canonical' / f'{asset}_1h.csv').read_bytes()
        if len(raw) != size or _sha(raw) != pin:
            raise PermissionError('Clean-4 canonical source mismatch: ' + asset)
    required = {
        'decision': PASS_MARK, 'vendor_origin_attested': True,
        'verified_funding_monthly_archives': 100,
        'verified_mark_monthly_archives': 100, 'verified_asset_events': 9144,
        'historical_pnl_computed': False, 'validation_2025_read': False,
        'holdout_accessed': False, 'external_benchmarks_used': False,
    }
    for key, value in required.items():
        if type(mark.get(key)) is not type(value) or mark[key] != value:
            raise PermissionError('funding/mark receipt mismatch: ' + key)
    for key in ('mark_zip_digest_manifest_sha256', 'funding_manifest_sha256', 'conservative_bounds_csv_sha256'):
        if not _hex_digest(mark.get(key)):
            raise PermissionError('mark/funding manifest missing: ' + key)
    bounds = (root / 'phase797_conservative_training_funding_bounds.csv').read_bytes()
    bounds_digest = _sha(bounds)
    if mark['conservative_bounds_csv_sha256'] != bounds_digest:
        raise PermissionError('funding/mark CSV digest mismatch')
    receipt = training.get('source_receipts', {})
    if receipt.get('ohlc') != ohlc['decision'] or receipt.get('mark') != mark['decision']:
        raise PermissionError('N training source decisions not bound to original receipts')
    if receipt.get('funding_mark_sha256') != bounds_digest:
        raise PermissionError('N training funding-mark digest not bound to source')
    validation = authorize_separate_validation(training)
    return {
        'decision': 'EVIDENCE_BOUND_N_TRAINING_READY_FOR_SEPARATE_VALIDATION',
        'ohlc_receipt_sha256': _sha((root / 'phase803_official_training_ohlc_receipt.json').read_bytes()),
        'mark_receipt_sha256': _sha((root / 'phase797_official_mark_archive_receipt.json').read_bytes()),
        'funding_mark_csv_sha256': bounds_digest,
        'training_receipt_sha256': validation['training_freeze']['training_receipt_sha256'],
        'canonical_asset_count': len(ASSETS), 'official_monthly_archive_count_required': 300,
        'source_authentication_performed_by_this_check': False,
        'historical_pnl_computed_by_this_check': False, 'validation_2025_read': False,
        'external_benchmarks_used': False,
    }


def run(root=ROOT):
    root = Path(root)
    out = {'phase': 955, 'decision': 'BLOCKED_BEFORE_2025_VALIDATION',
           'historical_pnl_computed_by_this_check': False, 'validation_2025_read': False,
           'external_benchmarks_used': False}
    try:
        out = bind_training_source_evidence(root)
        out['phase'] = 955
    except Exception as exc:
        out['reason'] = type(exc).__name__ + ': ' + str(exc)[:240]
    (root / 'phase955_n_source_evidence_binding_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    return out


if __name__ == '__main__':
    result = run()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result['decision'] == 'EVIDENCE_BOUND_N_TRAINING_READY_FOR_SEPARATE_VALIDATION' else 2)
