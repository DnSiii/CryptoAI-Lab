from __future__ import annotations
import importlib.util
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,PROJECT/path); assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
P111=load_module('v98_independent_phase111','scripts/v98_independent_phase111_stablecoin_peg_feasibility.py')

def test_phase111_flat_schema_parser_and_daily_canonicalization():
    hist=[
      {'id':'1','price':1.0,'timestamp':1672531200},
      {'id':'1','price':1.001,'timestamp':1672534800},
      {'id':'2','price':0.999,'timestamp':1672531200},
      {'id':'1','price':1.0,'timestamp':1672617600},
    ]
    d,meta=P111.canonical_history(hist,'1')
    assert meta['schema_ok'] is True
    assert meta['raw_records_for_id']==3
    assert meta['collapsed_duplicate_days']==1
    assert list(d['date_norm'])==['2023-01-01','2023-01-02']

def test_phase111_parser_is_id_specific():
    hist=[{'id':'1','price':1.0,'timestamp':1672531200},{'id':'2','price':1.0,'timestamp':1672531200}]
    d,_=P111.canonical_history(hist,'2')
    assert len(d)==1

def test_phase111_script_exposes_no_price_descriptives_or_trading_logic():
    text=(PROJECT/'scripts'/'v98_independent_phase111_stablecoin_peg_feasibility.py').read_text()
    forbidden=('profit_factor','total_return','position','correlation','final_holdout_start','2026-09-16','2026-10-15')
    assert not any(x in text for x in forbidden)
