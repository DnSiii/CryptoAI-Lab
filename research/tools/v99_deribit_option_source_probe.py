"""Deribit first-party historical options TRADE feasibility; TRAIN only, no PnL."""
from __future__ import annotations
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from research.tools.v99_r106_d1_real_train_source_join import START, END, FOLD_EDGES

BASE = "https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time"
FLAGS = {"model_only": True, "economic_train_executed": False, "validation_opened": False,
         "holdout_opened": False, "orders_enabled": False, "promotion_authorized": False}

def fetch(url):
    last = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "CryptoAI-V99-research-data-only/1.0",
                                                "Accept": "application/json"}), timeout=25) as resp:
                if resp.status != 200:
                    raise ValueError(f"HTTP_STATUS_{resp.status}")
                raw = resp.read(5_000_001)
                if len(raw) > 5_000_000:
                    raise ValueError("UNBOUNDED_SOURCE_RESPONSE")
                return raw
        except (HTTPError, URLError, TimeoutError) as exc:
            last = exc
            if isinstance(exc, HTTPError) and exc.code not in (408, 429, 500, 502, 503, 504):
                break
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"SOURCE_UNAVAILABLE: {type(last).__name__}: {last}")

def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    assert START == 1639008000000 and END == 1696118400000 and len(FOLD_EDGES) == 6
    assert FOLD_EDGES[0] == START and FOLD_EDGES[-1] == END
    records = []
    for fold, (start, end) in enumerate(zip(FOLD_EDGES, FOLD_EDGES[1:]), 1):
        # Ex-ante midpoint sample; never select dates by price or profitability.
        day = ((start + (end - start) // 2) // 86_400_000) * 86_400_000
        if day < start:
            day += 86_400_000
        day_end = day + 86_400_000
        assert start <= day < day_end <= end <= END
        for currency in ("BTC", "ETH"):
            params = {"currency": currency, "kind": "option", "start_timestamp": day,
                      "end_timestamp": day_end - 1, "count": 100,
                      "include_old": "true", "sorting": "asc"}
            record = {"fold": fold, "currency": currency,
                      "day_utc": datetime.fromtimestamp(day/1000, timezone.utc).isoformat(),
                      "start_ms": day, "end_exclusive_ms": day_end, "endpoint": BASE}
            try:
                raw = fetch(BASE + "?" + urlencode(params))
                receipt = out / f"deribit_option_f{fold}_{currency}.json"
                receipt.write_bytes(raw)
                payload = json.loads(raw)
                if payload.get("error"):
                    raise ValueError(f"EXCHANGE_ERROR: {payload['error']}")
                result = payload.get("result")
                if not isinstance(result, dict) or not isinstance(result.get("trades"), list):
                    raise ValueError("UNEXPECTED_EXCHANGE_SCHEMA")
                trades = result["trades"]
                if not all(isinstance(t, dict) and day <= int(t.get("timestamp", -1)) < day_end
                           and str(t.get("instrument_name", "")).startswith(currency + "-")
                           for t in trades):
                    raise ValueError("OFFGRID_OR_NONOPTION_SOURCE_ROW")
                record.update(status="TRADES_FOUND" if trades else "NO_TRADES_IN_SAMPLE",
                              sha256=hashlib.sha256(raw).hexdigest(), count=len(trades),
                              has_more=bool(result.get("has_more", False)),
                              iv_field_count=sum("iv" in t and t["iv"] is not None for t in trades),
                              distinct_instruments=len({t.get("instrument_name") for t in trades}),
                              fields=sorted({k for t in trades for k in t.keys()}),
                              receipt_file=receipt.name)
            except Exception as exc:
                record.update(status="SOURCE_ERROR", error=f"{type(exc).__name__}: {exc}")
            records.append(record)
            print(json.dumps({k: v for k, v in record.items() if k != "fields"}, sort_keys=True), flush=True)
    complete = all(r["status"] == "TRADES_FOUND" for r in records)
    report = {"schema": "DERIBIT_OPTIONS_TRADE_FIRSTPARTY_TRAIN_FEASIBILITY_V1",
              "status": "TRADE_SAMPLE_COVERED_NOT_EXECUTABLE_SURFACE" if complete
                        else "SOURCE_INCOMPLETE_OR_UNAVAILABLE",
              "train_start_ms": START, "train_end_exclusive_ms": END,
              "five_folds_checked": 5, "sample_days_per_asset": 5,
              "not_proven": ["full-hour TRAIN options-chain coverage", "historical executable bid/ask quotes",
                             "IV skew/term-structure available at decision time",
                             "instrument expiry settlement", "historical account fee tiers",
                             "actual hypothetical-order fills"],
              "records": records, **FLAGS}
    (out / "source_feasibility.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("SOURCE STATUS:", report["status"], "NO PNL / NO PROMOTION / NO ORDERS")
    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_deribit_option_source_probe OUT_DIR")
    main(sys.argv[1])
