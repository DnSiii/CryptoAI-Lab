"""First-party original TRAIN native-option listing feasibility (NOT quotes).
Precommitted: V99_R106_I1_NATIVE_LISTING_COVERAGE_PREREG_20261024.md
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC=timezone.utc
END=datetime(2023,10,1,tzinfo=UTC)
EDGES=[datetime(2021,12,9,tzinfo=UTC),datetime(2022,4,20,4,tzinfo=UTC),
       datetime(2022,8,30,9,tzinfo=UTC),datetime(2023,1,9,14,tzinfo=UTC),
       datetime(2023,5,21,19,tzinfo=UTC),END]
DATES=[datetime(2021,12,13,tzinfo=UTC)+timedelta(days=7*i) for i in range(91)]


def run(registry_file):
    src=json.loads(Path(registry_file).read_text())
    assert src["schema"]=="V99_I1_DERIBIT_HISTORICAL_INSTRUMENT_REGISTRY_V1"
    assert not src["historical_executable_quotes_authenticated"]
    assert len(DATES)==91 and DATES[-1]+timedelta(days=21)<END
    report=[]
    folds={str(i):{"BTC":0,"ETH":0} for i in range(1,6)}
    for decision in DATES:
        when=int(decision.timestamp()*1000)
        fold=next(i for i in range(1,6) if EDGES[i-1]<=decision<EDGES[i])
        for asset in ("BTC","ETH"):
            by_expiry=defaultdict(set)
            for item in src["registry"][asset]:
                created=item["creation_timestamp"]
                expiry=item["expiration_timestamp"]
                if (created is None or expiry is None or created>when or
                    not 21*86400000<=expiry-when<=45*86400000 or expiry>=int(END.timestamp()*1000)):
                    continue
                if item["settlement_currency"] != asset:
                    continue
                if any(item[k] is None or float(item[k])<=0 for k in
                       ("contract_size","min_trade_amount","tick_size")):
                    continue
                by_expiry[expiry].add(float(item["strike"]))
            max_strikes=max(map(len,by_expiry.values()),default=0)
            qualified=max_strikes>=2
            folds[str(fold)][asset]+=int(qualified)
            report.append({"decision_utc":decision.isoformat(),"asset":asset,
                           "fold":fold,"max_same_expiry_put_strikes":max_strikes,
                           "native_listed_pair":qualified})
    result={"schema":"V99_I1_ORIGINAL_NATIVE_INSTRUMENT_LISTING_COVERAGE_V1",
            "status":"LISTING_ONLY_NOT_EXECUTABLE_BOOK_OR_ECONOMICS",
            "original_source":"FIRST_PARTY_ARCHIVED_DERIBIT_INSTRUMENT_REGISTRY",
            "eligible_weeks":91,"asset_weeks":182,
            "listed_pairs":sum(x["native_listed_pair"] for x in report),
            "folds":folds,"weekly":report,
            "historical_quote_pairs_certified":0,"historical_fees_certified":False,
            "native_margin_liquidation_certified":False,"economic_train_executed":False,
            "validation_opened":False,"holdout_opened":False,"promotion_authorized":False,
            "orders_enabled":False}
    return result


if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: python -m research.tools.v99_r106_i1_native_listing_coverage REGISTRY_JSON OUT_JSON")
    result=run(sys.argv[1])
    dest=Path(sys.argv[2]);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="weekly"},sort_keys=True))
