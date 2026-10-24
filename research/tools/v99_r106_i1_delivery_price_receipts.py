"""Read-only original Deribit expiry-index receipts, TRAIN partition only.

This is historical *delivery price* provenance, NOT executable option quotes,
not a strategy, not a historical fill, not certified account PnL. No orders.
Discard every record outside [2021-12-09, 2023-10-01) before serialization.
"""
import hashlib
import json
import os
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

START = date(2021, 12, 9)
END = date(2023, 10, 1)
HOST = "https://www.deribit.com/api/v2/public/get_delivery_prices"
PAGE = 100
MAX_PAGES = 40


def get_page(index, offset):
    url = HOST + "?" + urlencode({"index_name": index, "offset": offset, "count": PAGE})
    last = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "V99-ReadOnly-Research/1.0",
                                               "Accept": "application/json"}), timeout=35) as response:
                raw = response.read(4_000_000)
            body = json.loads(raw)
            if body.get("error") or not isinstance(body.get("result"), dict):
                raise ValueError("DERIBIT_RPC_ERROR: " + str(body.get("error")))
            return raw, body["result"]
        except Exception as exc:
            last = exc
            time.sleep(attempt + 1)
    raise RuntimeError(f"DERIBIT_DELIVERY_SOURCE_UNAVAILABLE {index} offset={offset}: {last}")


def collect(index):
    selected = {}
    pages = []
    total = None
    for n in range(MAX_PAGES):
        offset = n * PAGE
        raw, response = get_page(index, offset)
        records = response.get("data")
        if not isinstance(records, list):
            raise ValueError("MISSING_DELIVERY_RECORDS")
        if total is None:
            total = int(response.get("records_total", -1))
            if total < 1:
                raise ValueError("BAD_TOTAL_RECORDS")
        dates = []
        for row in records:
            when = date.fromisoformat(row["date"])
            value = float(row["delivery_price"])
            if not (0 < value < 10_000_000):
                raise ValueError("BAD_DELIVERY_PRICE")
            dates.append(when)
            if START <= when < END:
                iso = when.isoformat()
                if iso in selected and selected[iso] != value:
                    raise ValueError("CONFLICTING_DELIVERY_PRICE")
                selected[iso] = value
        print(json.dumps({"source_index": index, "offset": offset,
                          "reported_total": total, "page_count": len(records),
                          "page_earliest_date": min(dates).isoformat() if dates else None,
                          "page_latest_date": max(dates).isoformat() if dates else None,
                          "train_rows_so_far": len(selected)}), flush=True)
        if dates != sorted(dates, reverse=True):
            raise ValueError("UNSORTED_DELIVERY_SOURCE")
        canonical_rows = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
        pages.append({"offset": offset, "sha256_raw_response_local": hashlib.sha256(raw).hexdigest(),
                      "sha256_canonical_data_rows": hashlib.sha256(canonical_rows).hexdigest(),
                      "records": len(records)})
        if not records or offset + len(records) >= total or (dates and min(dates) < START):
            break
    else:
        raise ValueError("UNBOUNDED_DELIVERY_PAGINATION")
    if not selected:
        raise ValueError("NO_ORIGINAL_TRAIN_DELIVERY_PRICES")
    return {"index": index, "train_start": START.isoformat(), "train_end_exclusive": END.isoformat(),
            "source": HOST, "total_reported": total, "pages": pages,
            "records": [{"date": k, "delivery_price": selected[k]} for k in sorted(selected)]}


def main():
    dest = Path(os.environ.get("V99_DELIVERY_OUTPUT", "/tmp/v99_i1_delivery_train_receipts.json"))
    payload = {"schema": "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1",
               "read_only": True, "no_orders": True, "no_promotion": True,
               "not_executable_quotes": True,
               "assets": {x: collect(x) for x in ("btc_usd", "eth_usd")}}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    for asset, part in payload["assets"].items():
        rows = part["records"]
        print(json.dumps({"index": asset, "train_delivery_rows": len(rows),
                          "first": rows[0]["date"], "last": rows[-1]["date"],
                          "api_pages": len(part["pages"]), "not_option_quotes": True,
                          "native_fees_authenticated": False, "promotion": False}))
    print("SOURCE_DATA_ONLY; NO OPTIONS ECONOMIC TRAIN; NO VALIDATION/HOLDOUT OUTPUT; NO ORDERS")


if __name__ == "__main__":
    main()
