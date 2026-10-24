"""Independent original HTTPS byte replay of TRAIN-only Deribit delivery receipts.

Does not import collector implementation. Read-only, no strategy, no orders.
"""
import hashlib
import json
import os
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def main():
    src = Path(os.environ.get("V99_DELIVERY_OUTPUT", "/tmp/v99_i1_delivery_train_receipts.json"))
    result = json.loads(src.read_text())
    assert result["schema"] == "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1"
    assert result["read_only"] and result["no_orders"] and result["no_promotion"]
    assert set(result["assets"]) == {"btc_usd", "eth_usd"}
    low, high = date(2021, 12, 9), date(2023, 10, 1)
    verified_pages = 0
    for asset, batch in result["assets"].items():
        assert batch["train_start"] == low.isoformat()
        assert batch["train_end_exclusive"] == high.isoformat()
        assert batch["source"] == "https://www.deribit.com/api/v2/public/get_delivery_prices"
        rebuilt = {}
        for page in batch["pages"]:
            query = urlencode({"index_name": asset, "offset": page["offset"], "count": 1000})
            url = batch["source"] + "?" + query
            with urlopen(Request(url, headers={"User-Agent": "V99-ReadOnly-Research/1.0",
                                               "Accept": "application/json"}), timeout=35) as r:
                raw = r.read(4_000_000)
            assert hashlib.sha256(raw).hexdigest() == page["sha256_raw_response"], "ORIGINAL_PAGE_CHANGED"
            parsed = json.loads(raw)
            assert parsed.get("error") is None
            rows = parsed["result"]["data"]
            assert len(rows) == page["records"]
            assert int(parsed["result"]["records_total"]) == batch["total_reported"]
            for row in rows:
                when = date.fromisoformat(row["date"])
                price = float(row["delivery_price"])
                assert 0 < price < 10_000_000
                if low <= when < high:
                    assert when.isoformat() not in rebuilt or rebuilt[when.isoformat()] == price
                    rebuilt[when.isoformat()] = price
            verified_pages += 1
        expected = [{"date": day, "delivery_price": rebuilt[day]} for day in sorted(rebuilt)]
        assert expected == batch["records"], "INDEPENDENT_TRAIN_REPLAY_MISMATCH"
        assert all(low <= date.fromisoformat(r["date"]) < high for r in expected)
        print(json.dumps({"index": asset, "independent_original_page_replay": True,
                          "train_rows": len(expected), "no_executable_quotes": True}))
    print(json.dumps({"status": "ORIGINAL_DERIBIT_DELIVERY_PRICE_TRAIN_ORACLE_PASS",
                      "verified_pages": verified_pages, "economic_train_run": False,
                      "margin_or_fees_certified": False, "promotion": False, "orders": False}))


if __name__ == "__main__":
    main()
