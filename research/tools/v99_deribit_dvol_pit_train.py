"""Original first-party Deribit daily DVOL source, five-fold PIT TRAIN only."""
from __future__ import annotations
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from research.tools.v99_deribit_weekly_pit_1000_coverage import decisions, DAY
from research.tools.v99_r106_d1_real_train_source_join import START, END, FOLD_EDGES

HOSTS = ("https://history.deribit.com/api/v2/public/get_volatility_index_data",
         "https://www.deribit.com/api/v2/public/get_volatility_index_data")
MAX_AGE = 2 * DAY
FLAGS = dict(economic_train_executed=False, validation_opened=False,
             holdout_opened=False, orders_enabled=False, promotion_authorized=False)


def original(url):
    last = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"Accept":"application/json",
                           "User-Agent":"CryptoAI-V99-DVOL-TRAIN/1.0"}), timeout=30) as r:
                if r.status != 200:
                    raise RuntimeError("HTTP_NON_200")
                b = r.read(2_000_001)
                if len(b) > 2_000_000:
                    raise RuntimeError("OVERSIZE")
                return b
        except (HTTPError, URLError, TimeoutError) as exc:
            last = exc
            if isinstance(exc, HTTPError) and exc.code not in (408,429,500,502,503,504):
                break
            time.sleep(attempt+1)
    raise RuntimeError(str(last))


def retrieve_fold(root, fold, currency):
    begin = max(START, ((FOLD_EDGES[fold-1] - 3*DAY) // DAY) * DAY)
    # The five immutable folds have non-midnight edges; request only completed
    # UTC daily candles well before the next fold, and never touch holdout.
    end = ((FOLD_EDGES[fold] - 1) // DAY) * DAY - DAY - 1
    params = dict(currency=currency, start_timestamp=begin,
                  end_timestamp=end, resolution="1D")
    errors = []
    for endpoint in HOSTS:
        try:
            url = endpoint + "?" + urlencode(params)
            raw = original(url)
            payload = json.loads(raw)
            if payload.get("error"):
                raise RuntimeError("EXCHANGE_ERROR: " + str(payload["error"]))
            result = payload.get("result")
            if not isinstance(result, dict) or not isinstance(result.get("data"), list):
                raise RuntimeError("BAD_RESPONSE")
            if result.get("continuation") is not None:
                raise RuntimeError("CONTINUATION_UNHANDLED")
            data = result["data"]
            if not data:
                raise RuntimeError("NO_HISTORICAL_DVOL_DATA")
            parsed = {}
            ignored = 0
            for v in data:
                if not isinstance(v, list) or len(v) < 5:
                    raise ValueError("BAD_CANDLE")
                ts = int(v[0])
                if not (START <= ts < END):
                    raise ValueError("OUTSIDE_TRAIN_CANDLE")
                if not (begin <= ts <= end):
                    ignored += 1
                    continue
                o,h,l,c = [float(x) for x in v[1:5]]
                if not (all(math.isfinite(x) and x>0 for x in (o,h,l,c))
                        and h>=max(o,c,l) and l<=min(o,c,h)):
                    raise ValueError("BAD_OHLC")
                if ts in parsed:
                    raise ValueError("DUPLICATE_CANDLE")
                parsed[ts] = c
            if list(parsed) != sorted(parsed):
                raise ValueError("NON_MONOTONIC_CANDLES")
            filename = f"dvol_fold{fold}_{currency}.json"
            (root / filename).write_bytes(raw)
            return dict(fold=fold,currency=currency,status="SOURCE_OK",
                        endpoint=endpoint,query_start_ms=begin,query_end_ms=end,
                        receipt_file=filename,sha256=hashlib.sha256(raw).hexdigest(),
                        candles=len(parsed),ignored_out_of_query=ignored,
                        first_candle_ms=min(parsed),last_candle_ms=max(parsed)),parsed
        except Exception as exc:
            errors.append(f"{endpoint}: {type(exc).__name__}: {exc}")
    return dict(fold=fold,currency=currency,status="SOURCE_ERROR",errors=errors),{}


def main(directory):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    sources = []
    series = {}
    for fold in range(1,6):
        for currency in ("BTC","ETH"):
            row, candles = retrieve_fold(root,fold,currency)
            sources.append(row)
            series[(fold,currency)] = candles
            print(json.dumps(row,sort_keys=True),flush=True)
    weekly = []
    for t,fold in decisions():
        for currency in ("BTC","ETH"):
            eligible = False
            candle = None
            close = None
            age = None
            for stamp,value in series[(fold,currency)].items():
                # Candle timestamp is start-of-day; never assume a candle
                # ending at the decision clock was known before that clock.
                candle_end = stamp+DAY
                if candle_end < t and t-candle_end<=MAX_AGE:
                    if candle is None or stamp>candle:
                        candle=stamp;close=value;age=t-candle_end
                        eligible=True
            weekly.append(dict(decision_ms=t,fold=fold,currency=currency,
                               eligible=eligible,candle_start_ms=candle,
                               dvol_close=close,age_after_close_ms=age))
    folds=[]
    for fold in range(1,6):
        for currency in ("BTC","ETH"):
            subset=[r for r in weekly if r["fold"]==fold and r["currency"]==currency]
            n=sum(r["eligible"] for r in subset)
            folds.append(dict(fold=fold,currency=currency,weeks=len(subset),
                              eligible=n,fraction=n/len(subset)))
    good=sum(all(next(r for r in folds if r["fold"]==f and r["currency"]==c)["fraction"]>=0.95
                 for c in ("BTC","ETH")) for f in range(1,6))
    report=dict(schema="V99_DERIBIT_FIRSTPARTY_DVOL_PIT_TRAIN_V1",
                start_ms=START,end_exclusive_ms=END,fold_edges=FOLD_EDGES,
                source_rows=sources,weekly=weekly,folds=folds,good_folds=good,
                gate="DVOL_SOURCE_READY_FOR_ONE_ENGINE_PREREG" if good>=4 else "DVOL_SOURCE_FAIL",
                max_age_ms=MAX_AGE,**FLAGS)
    (root/"dvol_train_source.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("DVOL ORIGINAL TRAIN GATE:",report["gate"],good,"/5 folds")
    print("NO ECONOMICS / NO PNL / NO PROMOTION")
    return report

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python -m research.tools.v99_deribit_dvol_pit_train OUTPUT_DIR")
    main(sys.argv[1])
