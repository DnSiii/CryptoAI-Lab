#!/usr/bin/env python3
"""V98 Clean-4 official mark source failure locator; no PnL, no gate changes."""
import json
from pathlib import Path
from phase797_official_mark_archive_attestor import ASSETS,MONTHS,verify_month

result={'phase':961,'decision':'NO_FAILURE','verified_months':0,
        'historical_pnl_computed':False,'validation_2025_read':False,
        'external_benchmarks_used':False}
for asset in ASSETS:
    for month in MONTHS:
        try:
            verify_month(asset,month)
            result['verified_months']+=1
        except Exception as exc:
            result.update(decision='QUARANTINE_MARK_SOURCE',asset=asset,month=month,
                          reason=type(exc).__name__+': '+str(exc)[:240])
            break
    if result['decision']!='NO_FAILURE':break
Path('phase961_n_mark_month_locator_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
