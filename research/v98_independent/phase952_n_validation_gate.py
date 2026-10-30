#!/usr/bin/env python3
"""V98 Independent: additive pre-2025 validation gate; no strategy modification."""
from __future__ import annotations
import json
from pathlib import Path
from phase950_n_accounting_consistency import audit_n_training_accounting
from phase948_n_validation_firewall import seal_training_receipt
ROOT=Path(__file__).resolve().parent


def authorize_separate_validation(training_receipt):
    # Algebraic verification cannot replace existing vendor provenance and
    # economic growth/survival gates. BOTH are mandatory and independent.
    integrity=audit_n_training_accounting(training_receipt)
    frozen=seal_training_receipt(training_receipt)
    return {'decision':'READY_FOR_SEPARATE_2025_VALIDATION_NOT_EXECUTED',
            'accounting_integrity':integrity,'training_freeze':frozen,
            'validation_2025_read':False,'external_benchmarks_used':False,
            'historical_pnl_computed_by_this_gate':False}


def run(root=ROOT):
    root=Path(root)
    out={'phase':952,'decision':'BLOCKED_BEFORE_2025_VALIDATION',
         'validation_2025_read':False,'external_benchmarks_used':False,
         'historical_pnl_computed_by_this_gate':False}
    try:
        receipt=json.loads((root/'phase940_n_official_90cell_hourly_result.json').read_text())
        out=authorize_separate_validation(receipt)
        out['phase']=952
    except Exception as exc:
        out['reason']=type(exc).__name__+': '+str(exc)[:300]
    (root/'phase952_n_validation_gate_result.json').write_text(
        json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+'\n')
    return out

if __name__=='__main__':
    result=run()
    print(json.dumps({k:result.get(k) for k in ('decision','reason','validation_2025_read')},sort_keys=True))
