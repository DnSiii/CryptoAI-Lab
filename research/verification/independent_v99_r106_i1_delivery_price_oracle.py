"""Independent first-party Deribit TRAIN delivery-price date-keyed replay.

The original archive's newest-first offset page membership drifts as new
daily records arrive. Never compare 2026-10-24 page hashes against today's
offsets: independently compare all 661 immutable TRAIN date/price keys.
No imports from production collector, no post-TRAIN output, no economics.
Prereg: V99_R106_I1_DELIVERY_ORACLE_PAGINATION_DRIFT_PREREG_20261028.md.
"""
from __future__ import annotations

import json
import os
import time
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

START = date(2021, 12, 9)
END = date(2023, 10, 1)
DAYS = (END - START).days
HOST = "https://www.deribit.com/api/v2/public/get_delivery_prices"
PAGE = 100
MAX_PAGES = 40


def _positive(value):
    if isinstance(value, bool):
        raise ValueError("INVALID_FIRSTPARTY_DELIVERY_PRICE")
    try:
        number = Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation) as exc:
        raise ValueError("INVALID_FIRSTPARTY_DELIVERY_PRICE") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("INVALID_FIRSTPARTY_DELIVERY_PRICE")
    return number


def fetch_live_page(index, offset):
    url = HOST + "?" + urlencode({"index_name": index, "offset": offset, "count": PAGE})
    error = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={
                    "User-Agent": "V99-ReadOnly-Research/1.0",
                    "Accept": "application/json"}), timeout=35) as stream:
                body = json.loads(stream.read(4_000_000))
            if body.get("error") or not isinstance(body.get("result"), dict):
                raise ValueError("DERIBIT_RPC_ERROR")
            return body["result"]
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(attempt + 1)
    raise RuntimeError("FIRSTPARTY_DELIVERY_LIVE_SOURCE_UNAVAILABLE:" + index) from error


def verify_archive(archive, fetch_page=fetch_live_page):
    if (not isinstance(archive, dict)
            or archive.get("schema") != "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1"
            or archive.get("read_only") is not True
            or archive.get("no_orders") is not True
            or archive.get("no_promotion") is not True
            or archive.get("not_executable_quotes") is not True
            or not isinstance(archive.get("assets"), dict)
            or set(archive["assets"]) != {"btc_usd", "eth_usd"}):
        raise ValueError("UNTRUSTED_ARCHIVED_FIRSTPARTY_DELIVERY")
    checked = {}
    for index in ("btc_usd", "eth_usd"):
        part = archive["assets"][index]
        if (not isinstance(part, dict) or part.get("index") != index
                or part.get("source") != HOST
                or part.get("train_start") != START.isoformat()
                or part.get("train_end_exclusive") != END.isoformat()
                or not isinstance(part.get("pages"), list) or not part["pages"]
                or not isinstance(part.get("records"), list)
                or len(part["records"]) != DAYS):
            raise ValueError("INCOMPLETE_ARCHIVED_FIRSTPARTY_TRAIN:" + index)
        historical = {}
        for i, row in enumerate(part["records"]):
            expected = (START + timedelta(days=i)).isoformat()
            if (not isinstance(row, dict) or set(row) != {"date", "delivery_price"}
                    or row["date"] != expected):
                raise ValueError("ARCHIVED_TRAIN_DATE_MISSING_OR_SHIFTED:" + index)
            historical[expected] = _positive(row["delivery_price"])

        # The archived page hashes remain evidence of the original 2026-10-24
        # acquisition. Their offset boundaries cannot be replayed after new
        # daily records prepend to Deribit's newest-first history.
        for i, page in enumerate(part["pages"]):
            if (page.get("offset") != i*PAGE
                    or not isinstance(page.get("sha256_canonical_data_rows"), str)
                    or len(page["sha256_canonical_data_rows"]) != 64):
                raise ValueError("MALFORMED_ARCHIVED_ACQUISITION_PAGE")

        live = {}
        page_count = 0
        reached_start = False
        for n in range(MAX_PAGES):
            result = fetch_page(index, n*PAGE)
            if not isinstance(result, dict) or not isinstance(result.get("data"), list):
                raise ValueError("MALFORMED_LIVE_FIRSTPARTY_DELIVERY")
            rows = result["data"]
            if not rows or len(rows) > PAGE:
                raise ValueError("INCOMPLETE_LIVE_FIRSTPARTY_DELIVERY")
            dates = []
            for row in rows:
                when = date.fromisoformat(row["date"])
                price = _positive(row["delivery_price"])
                dates.append(when)
                if START <= when < END:
                    key = when.isoformat()
                    if key in live and live[key] != price:
                        raise ValueError("CONFLICTING_LIVE_FIRSTPARTY_DELIVERY")
                    live[key] = price
            if dates != sorted(dates, reverse=True):
                raise ValueError("REORDERED_LIVE_FIRSTPARTY_DELIVERY")
            page_count += 1
            if min(dates) < START:
                reached_start = True
                break
        if not reached_start:
            raise ValueError("UNBOUNDED_OR_INCOMPLETE_LIVE_DELIVERY_HISTORY")
        if live != historical:
            missing = len(set(historical)-set(live))
            changed = sum(live.get(k) != v for k,v in historical.items())
            raise ValueError(f"ORIGINAL_TRAIN_DATE_PRICE_CHANGED:{index}:missing={missing}:changed={changed}")
        checked[index] = {"original_train_dates_verified": DAYS,
                          "live_pages": page_count,
                          "offset_page_hash_replay_not_valid_after_prepends": True}
    return {"status": "ORIGINAL_DERIBIT_TRAIN_DELIVERY_DATE_KEYED_REPLAY_PASS",
            "assets": checked, "economic_train_run": False,
            "native_settlement_terms_certified": False,
            "promotion": False, "orders": False}


def main():
    path = Path(os.environ.get("V99_DELIVERY_OUTPUT",
                               "/tmp/v99_i1_delivery_train_receipts.json"))
    result = verify_archive(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
