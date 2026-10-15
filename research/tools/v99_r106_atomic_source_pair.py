"""Atomic same-hour DATA_ONLY OKX market+native-terms receipt commit.
Never backfill missing hours, overwrite archived observations, grant PnL or access holdout.
"""
import argparse,hashlib,json,re,shutil,tempfile
from pathlib import Path
from research.tools import v99_r106_receipt_append as market
from research.tools import v99_r106_terms_append as terms

def verify(market_dir,terms_dir):
    m=market.verify_source(market_dir)
    t=terms.validate(terms_dir)
    a=market.utc(m["last_received_utc"]);b=market.utc(t["acquisition_last_utc"])
    bucket=a.strftime("%Y-%m-%dT%H")
    if bucket!=b.strftime("%Y-%m-%dT%H"):raise ValueError("crossed_utc_hour")
    if b<a or (b-a).total_seconds()>180:raise ValueError("acquisition_pair_over_180_seconds_or_reversed")
    if m.get("economic_trials")!=0 or t.get("economic_trials")!=0:raise ValueError("economic_trials_denied")
    if m.get("holdout_accessed") is not False or t.get("holdout_accessed") is not False:raise ValueError("holdout_denied")
    if set(m["instruments"])!=set(t["contracts"])!=set(market.INSTRUMENTS):raise ValueError("pair_instruments_differ")
    if market.utc(m["earliest_candidate_decision_utc"])!=market.utc(t["earliest_safe_decision_utc"]):
        raise ValueError("safe_tminus1_decision_disagreement")
    closes={v["latest_confirmed_close_utc"] for v in m["instruments"].values()}
    if len(closes)!=1 or market.utc(next(iter(closes)))>a:raise ValueError("unclosed_or_divergent_candle")
    return bucket

def append_pair(market_dir,terms_dir,receipt_root,run_id):
    if not isinstance(run_id,str) or not re.fullmatch(r"\d{8,15}",run_id):
        raise ValueError("real_actions_run_id_required")
    bucket=verify(market_dir,terms_dir)
    mroot=receipt_root/"v99_r106_okx";troot=receipt_root/"v99_r106_okx_terms"
    mtarget=mroot/bucket;ttarget=troot/bucket
    if mtarget.exists() or ttarget.exists():
        status="ALREADY_PAIRED_UNCHANGED" if mtarget.is_dir() and ttarget.is_dir() else "DATA_ONLY_HOLD_PARTIAL_PREEXISTING_HOUR"
        return {"status":status,"bucket":bucket,"changed":False,"promotion_authorized":False,"paper_publication_authorized":False}
    receipt_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pair-stage-",dir=receipt_root) as tmp:
        stage=Path(tmp)
        market.append(market_dir,stage/"v99_r106_okx",run_id)
        terms.append(terms_dir,stage/"v99_r106_okx_terms",run_id)
        sm=stage/"v99_r106_okx"/bucket;st=stage/"v99_r106_okx_terms"/bucket
        if not sm.is_dir() or not st.is_dir():raise ValueError("missing_staged_receipt")
        mroot.mkdir(parents=True,exist_ok=True);troot.mkdir(parents=True,exist_ok=True)
        if mtarget.exists() or ttarget.exists():raise ValueError("concurrent_writer")
        try:
            sm.rename(mtarget);st.rename(ttarget)
        except Exception:
            if mtarget.exists():shutil.rmtree(mtarget)
            if ttarget.exists():shutil.rmtree(ttarget)
            raise
    return {"status":"ATOMIC_PAIRED_RECEIPT_APPENDED","bucket":bucket,"changed":True,
        "run_id":run_id,
        "market_manifest_sha256":hashlib.sha256((mtarget/"manifest.json").read_bytes()).hexdigest(),
        "terms_manifest_sha256":hashlib.sha256((ttarget/"manifest.json").read_bytes()).hexdigest(),
        "first_party_http_not_exchange_signed":True,"realized_funding_authenticated":False,
        "fee_tier_authenticated":False,"holdout_accessed":False,"economic_trials":0,
        "promotion_authorized":False,"paper_publication_authorized":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--market",type=Path,required=True);p.add_argument("--terms",type=Path,required=True)
    p.add_argument("--receipts-root",type=Path,required=True);p.add_argument("--run-id",required=True)
    a=p.parse_args();print(json.dumps(append_pair(a.market,a.terms,a.receipts_root,a.run_id),sort_keys=True))
if __name__=="__main__":main()
