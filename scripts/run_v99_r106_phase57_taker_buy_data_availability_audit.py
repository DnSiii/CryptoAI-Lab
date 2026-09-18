from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
REPORT=PROJECT/'reports'/'candidate_v99_r106_phase57_taker_buy_data_availability_audit.json'
ROOTS=[PROJECT/'data'/'canonical', PROJECT/'data']
TOKENS=('taker_buy','takerbuy','taker buy')

def inspect_file(path: Path):
    rec={'path':str(path.relative_to(PROJECT)),'suffix':path.suffix.lower(),'matched_columns':[],'readable':False}
    try:
        if path.suffix.lower()=='.csv': df=pd.read_csv(path,nrows=2000)
        elif path.suffix.lower()=='.parquet': df=pd.read_parquet(path)
        elif path.suffix.lower() in ('.json','.jsonl'):
            try: df=pd.read_json(path,lines=path.suffix.lower()=='.jsonl')
            except Exception: return rec
        else: return rec
        rec['readable']=True; rec['columns']=[str(c) for c in df.columns]
        rec['matched_columns']=[str(c) for c in df.columns if any(t in str(c).lower() for t in TOKENS)]
        rec['rows_inspected']=int(len(df))
        if rec['matched_columns']:
            rec['null_fraction']={c:float(df[c].isna().mean()) for c in rec['matched_columns']}
    except Exception as e: rec['error']=type(e).__name__
    return rec

def main():
    seen=set(); rows=[]
    for root in ROOTS:
        if not root.exists(): continue
        for p in root.rglob('*'):
            if not p.is_file() or p in seen or p.suffix.lower() not in ('.csv','.parquet','.json','.jsonl'): continue
            seen.add(p); r=inspect_file(p)
            if r.get('matched_columns'): rows.append(r)
    usable=bool(rows)
    out={'study':'V99 R106 phase 57A — genuine taker-buy data availability audit','status':'DATA_AVAILABLE_REQUIRES_CAUSAL_PROVENANCE_AUDIT' if usable else 'DATA_BLOCKED_NO_PROXY','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'data_availability_only':True,'strategy_change':False,'no_proxy_from_ohlcv':True,'no_holdout_feature_selection':True,'required_feature':'exchange-provided taker-buy volume field'},'roots_scanned':[str(x.relative_to(PROJECT)) for x in ROOTS if x.exists()],'matching_sources':rows,'genuine_field_found':usable,'actionable_for_phase57b':False,'next_step':'If genuine fields exist, audit timestamp semantics/provenance/full coverage and causal join before any returns. If absent, specify research-only ingestion/cache without changing canonical or frozen assets.','disclosure':'No candidate, return backtest, direction choice or holdout inspection is performed by Phase57A.'}
    REPORT.parent.mkdir(exist_ok=True); REPORT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
