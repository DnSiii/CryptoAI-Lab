#!/usr/bin/env python3
"""Pre-PnL Phase189 gate: canonical cache must natively expose quote/notional volume."""
import csv,json
from pathlib import Path
ALIASES=('quote_volume','quoteVolume','quote_asset_volume','quoteAssetVolume','notional_volume','notionalVolume')
def inspect(path):
 with open(path,newline='',encoding='utf-8') as f: fields=csv.DictReader(f).fieldnames or []
 hits=[x for x in ALIASES if x in fields]
 return {'path':path,'fieldnames':fields,'native_quote_volume_fields':hits,'pass':len(hits)==1}
def main():
 checks=[inspect('data/canonical/BTCUSDT_1h.csv'),inspect('data/canonical/ETHUSDT_1h.csv')]
 ok=all(x['pass'] for x in checks) and checks[0]['native_quote_volume_fields']==checks[1]['native_quote_volume_fields']
 out={'study':'V99 R106 Phase189 mandatory canonical schema gate','pnl_inspected':False,'holdout_market_values_parsed':False,'checks':checks,'status':'CANONICAL_NATIVE_QUOTE_VOLUME_PASS' if ok else 'CLOSE_PHASE189_PRE_PNL_CANONICAL_FIELD_ABSENT_OR_AMBIGUOUS'}
 Path('reports').mkdir(exist_ok=True);Path('reports/v99_r106_phase189_canonical_schema_gate.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True,indent=2))
 if not ok: raise SystemExit(42)
if __name__=='__main__': main()
