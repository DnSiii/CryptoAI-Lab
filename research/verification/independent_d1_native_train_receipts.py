"""Independent offline oracle for real D1 OKX four-leg TRAIN source receipts.

Never uses the downloader's parser. Verifies original bytes, request cursor
chain, 15,864-hour common grid and opens. Does not authorize economics.
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
HOUR = 3600000
EXPECTED = (END - START) // HOUR
INSTS = ("BTC-USDT", "BTC-USDT-SWAP", "ETH-USDT", "ETH-USDT-SWAP")


def distinct(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError("DUPLICATE_SOURCE_JSON_KEY")
        obj[k] = v
    return obj


def verify(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_bytes(), object_pairs_hook=distinct)
    if manifest.get("train_start_ms") != START or manifest.get("train_end_exclusive_ms") != END:
        raise ValueError("TRAIN_PARTITION_CHANGED")
    for flag in ("validation_opened", "holdout_opened", "economic_trial_run",
                 "paper_publication_authorized", "orders_enabled", "promotion_authorized"):
        if manifest.get(flag) is not False:
            raise ValueError("UNSAFE_SOURCE_MANIFEST")
    if set(manifest.get("instruments", {})) != set(INSTS):
        raise ValueError("FOUR_LEGS_REQUIRED")
    results = {}
    for inst in INSTS:
        folder = root / inst
        original = {}
        cursor = END
        pages = manifest["instruments"][inst]["pages"]
        for i, meta in enumerate(pages):
            name = f"page_{i:04d}.raw.json"
            if meta.get("file") != name:
                raise ValueError("UNEXPECTED_SOURCE_PAGE_FILE")
            raw = (folder / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != meta.get("sha256"):
                raise ValueError("RAW_PAGE_SHA256_MISMATCH")
            url = urlsplit(meta["url"])
            args = parse_qs(url.query)
            if (url.scheme != "https" or url.hostname != "www.okx.com" or
                url.path != "/api/v5/market/history-candles" or
                args.get("instId") != [inst] or args.get("bar") != ["1H"] or
                args.get("limit") != ["100"] or args.get("after") != [str(cursor)]):
                raise ValueError("WRONG_ENDPOINT_OR_CURSOR")
            data = json.loads(raw, object_pairs_hook=distinct)
            if data.get("code") != "0" or not isinstance(data.get("data"), list):
                raise ValueError("BAD_FIRST_PARTY_PAGE")
            stamps = []
            for row in data["data"]:
                if not isinstance(row, list) or len(row) < 9 or row[8] != "1":
                    raise ValueError("INVALID_BAR")
                stamp = row[0]
                if not isinstance(stamp, str) or not stamp.isdecimal():
                    raise ValueError("INVALID_TIMESTAMP")
                t = int(stamp)
                if t >= cursor or t >= END or t % HOUR:
                    raise ValueError("SEALED_OR_INVALID_TIMESTAMP")
                o, h, l, c = (Decimal(str(row[k])) for k in (1, 2, 3, 4))
                if (not all(x.is_finite() for x in (o, h, l, c)) or
                    min(o, h, l, c) <= 0 or l > min(o, c) or h < max(o, c)):
                    raise ValueError("INVALID_PRICE")
                if t >= START:
                    if t in original:
                        raise ValueError("REPEATED_HISTORICAL_BAR")
                    original[t] = str(o)
                stamps.append(t)
            if stamps != sorted(stamps, reverse=True) or len(stamps) != len(set(stamps)):
                raise ValueError("BAD_PAGE_ORDER")
            if not stamps:
                break
            cursor = min(stamps)
            if cursor <= START:
                break
        stored = json.loads((folder / "train_opens.json").read_bytes(), object_pairs_hook=distinct)
        expected_rows = [{"ts": t, "open": original[t]} for t in sorted(original)]
        if stored != expected_rows:
            raise ValueError("DOWNLOADER_VS_INDEPENDENT_OPEN_MISMATCH")
        missing = [START + HOUR * i for i in range(EXPECTED)
                   if START + HOUR * i not in original]
        if (manifest["instruments"][inst]["observed_hours"] != len(original) or
            manifest["instruments"][inst]["missing_hours"] != len(missing)):
            raise ValueError("SOURCE_MANIFEST_COUNT_MISMATCH")
        results[inst] = {"verified_hours": len(original), "missing_hours": len(missing),
                         "raw_pages_verified": len(pages)}
    complete = all(x["verified_hours"] == EXPECTED and x["missing_hours"] == 0
                   for x in results.values())
    return {"status": "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS" if complete
            else "INDEPENDENT_SOURCE_INCOMPLETE_NO_ECONOMICS",
            "instruments": results, "expected_hours": EXPECTED,
            "economic_trial_run": False, "validation_opened": False,
            "holdout_opened": False, "promotion_authorized": False}


def main():
    result = verify(sys.argv[1])
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"].startswith("INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE") else 2


if __name__ == "__main__":
    sys.exit(main())
