from __future__ import annotations
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT/'reports'/'candidate_v99_r106_phase58_taker_buy_ingestion_spec.json'

# Binance USD-M 1h kline archives contain exchange-native taker-buy base/quote
# volume fields in the official kline schema. This phase only specifies a
# research-only ingestion contract. It does not fetch returns or alter a strategy.
SCHEMA = [
 'open_time','open','high','low','close','volume','close_time','quote_volume',
 'trades','taker_buy_base_volume','taker_buy_quote_volume','ignore'
]

def main():
    out={
      'study':'V99 R106 phase 58 — taker-buy research-only ingestion contract',
      'status':'SPEC_READY_NO_BACKTEST',
      'frozen_assets_untouched':{'v16':True,'v99_frozen':True},
      'source_contract':{
        'venue':'Binance USD-M perpetual futures',
        'archive':'data.binance.vision futures/um klines 1h',
        'schema':SCHEMA,
        'required_fields':['open_time','close_time','taker_buy_base_volume','taker_buy_quote_volume','volume','quote_volume'],
        'provenance_rule':'accept only exchange archive bytes with archive CHECKSUM verification',
        'research_only_destination':'data/research/v99_r106/taker_buy_1h',
        'canonical_mutation_forbidden':True,
      },
      'causality_contract':{
        'feature_timestamp':'bar close_time',
        'decision_availability':'strictly after bar close; feature must be shifted t-1 before position decision',
        'no_same_bar_execution':True,
        'no_holdout_selection':True,
      },
      'integrity_gates':[
        'checksum and ZIP CRC pass','unique symbol/open_time','strict hourly monotonic timestamps',
        '0 <= taker_buy_base_volume <= volume','0 <= taker_buy_quote_volume <= quote_volume',
        'full expected train/validation coverage before any alpha evaluation','no OHLCV-derived proxy substitution'
      ],
      'next_gate':'implement deterministic downloader/parser + coverage/provenance audit; only then pre-register an alpha transform and direction without holdout inspection',
      'disclosure':'No candidate, returns, direction choice, parameter search, or holdout inspection occurs in phase58.'
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
