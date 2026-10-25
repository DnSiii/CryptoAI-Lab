"""Independent original-byte 182 native listing coverage oracle. No primary imports."""
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

def audit(source_dir, report_file):
    root=Path(source_dir)
    registry=json.loads((root/"native_instrument_registry.json").read_text())
    report=json.loads(Path(report_file).read_text())
    assert report["schema"]=="V99_I1_ORIGINAL_NATIVE_INSTRUMENT_LISTING_COVERAGE_V1"
    assert report["eligible_weeks"]==91 and report["asset_weeks"]==182
    original={}
    for asset in ("BTC","ETH"):
        info=registry["sources"][asset]
        raw=gzip.decompress((root/info["original_gzip"]).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==info["original_raw_sha256"]
        all_rows=json.loads(raw)["result"]
        assert len(all_rows)==info["original_instruments"]
        original[asset]=[r for r in all_rows if r.get("kind")=="option" and r.get("option_type")=="put"]
    folds=[datetime(2021,12,9,tzinfo=timezone.utc),
           datetime(2022,4,20,4,tzinfo=timezone.utc),
           datetime(2022,8,30,9,tzinfo=timezone.utc),
           datetime(2023,1,9,14,tzinfo=timezone.utc),
           datetime(2023,5,21,19,tzinfo=timezone.utc),
           datetime(2023,10,1,tzinfo=timezone.utc)]
    count={str(i):{"BTC":0,"ETH":0} for i in range(1,6)}
    checked=[]
    for week in range(91):
        decision=datetime(2021,12,13,tzinfo=timezone.utc)+timedelta(weeks=week)
        d=int(decision.timestamp()*1000)
        fold=next(i for i in range(1,6) if folds[i-1]<=decision<folds[i])
        for asset in ("BTC","ETH"):
            exp_strikes=defaultdict(set)
            for row in original[asset]:
                expiry=row.get("expiration_timestamp")
                created=row.get("creation_timestamp")
                if expiry is None or created is None: continue
                if not (created<=d and 21*86400000<=expiry-d<=45*86400000
                        and expiry<1696118400000): continue
                if row.get("settlement_currency")!=asset: continue
                if any(row.get(k) is None or float(row[k])<=0 for k in
                       ("contract_size","min_trade_amount","tick_size")): continue
                exp_strikes[expiry].add(float(row["strike"]))
            maximum=max((len(v) for v in exp_strikes.values()),default=0)
            ok=maximum>=2
            count[str(fold)][asset]+=int(ok)
            checked.append({"decision_utc":decision.isoformat(),"asset":asset,
                            "fold":fold,"max_same_expiry_put_strikes":maximum,
                            "native_listed_pair":ok})
    assert checked==report["weekly"]
    assert count==report["folds"]
    assert sum(row["native_listed_pair"] for row in checked)==report["listed_pairs"]
    assert report["historical_quote_pairs_certified"]==0
    for flag in ("historical_fees_certified","native_margin_liquidation_certified",
                 "economic_train_executed","validation_opened","holdout_opened",
                 "promotion_authorized","orders_enabled"):
        assert report[flag] is False
    print(json.dumps({"original_asset_weeks":len(checked),
                      "native_listed_pairs":report["listed_pairs"],"folds":count,
                      "source_only":True},sort_keys=True))
    return True

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_native_listing_coverage REGISTRY_DIR REPORT_JSON")
    assert audit(sys.argv[1],sys.argv[2])
