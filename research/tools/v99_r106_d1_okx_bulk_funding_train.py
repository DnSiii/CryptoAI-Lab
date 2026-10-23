"""First-party OKX bulk funding archive acquisition for D1 TRAIN (read-only).

Bulk archive is distinct from the REST 3-month funding-history endpoint.
NEVER substitutes venue funding rate for an account funding cash receipt.
Never requests months after September 2023 or submits orders.
"""
from __future__ import annotations
import hashlib
import io
import json
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
WINDOWS = (
    ("2022-02-28T16:00:00", "2022-10-31T16:00:00"),
    ("2022-10-31T16:00:00", "2023-06-30T16:00:00"),
    ("2023-06-30T16:00:00", "2023-09-30T15:59:59"),
)
INSTS = ("BTC-USDT-SWAP", "ETH-USDT-SWAP")


def epoch(value):
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp() * 1000)


def get(url, max_bytes):
    req = Request(url, headers={"User-Agent": "CryptoAI-Lab-D1-TRAIN-funding-archive/1.0",
                                "Accept": "application/json,application/zip"})
    with urlopen(req, timeout=45) as response:
        actual = urlsplit(response.geturl())
        if response.status != 200 or actual.scheme != "https" or actual.hostname not in (
            "www.okx.com", "static.okx.com"):
            raise ValueError("UNAPPROVED_ARCHIVE_REDIRECT")
        raw = response.read(max_bytes + 1)
    if not raw or len(raw) > max_bytes:
        raise ValueError("OVERSIZED_OR_EMPTY_OKX_ARCHIVE")
    return raw


def unique(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError("DUPLICATE_JSON_PROPERTY")
        obj[k] = v
    return obj


def listing(inst, begin, end):
    params = {"module": "3", "instType": "SWAP",
              "instFamilyList": inst.removesuffix("-SWAP"),
              "dateAggrType": "monthly", "begin": str(epoch(begin)),
              "end": str(epoch(end))}
    url = "https://www.okx.com/api/v5/public/market-data-history?" + urlencode(params)
    raw = get(url, 250000)
    obj = json.loads(raw, object_pairs_hook=unique)
    if obj.get("code") != "0" or not isinstance(obj.get("data"), list):
        raise ValueError("OKX_ARCHIVE_LISTING_ERROR:" + str(obj.get("code")))
    found = []
    for item in obj["data"]:
        for group in item.get("details", []):
            for file in group.get("groupDetails", []):
                found.append(file)
    return raw, found


def archive_rows(raw, inst):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members = [m for m in z.infolist() if m.filename.lower().endswith(".csv")]
        if len(members) != 1 or members[0].file_size > 10000000:
            raise ValueError("BAD_ARCHIVE_CSV_STRUCTURE")
        text = z.read(members[0]).decode("utf-8-sig")
    rates = {}
    for row in text.splitlines():
        fields = row.strip().split(",")
        if len(fields) < 3 or fields[0] != inst:
            continue
        if not fields[2].isdecimal():
            raise ValueError("INVALID_FUNDING_TIMESTAMP")
        ts = int(fields[2])
        if ts >= END:
            raise ValueError("SEALED_FUNDING_ROW")
        if ts < START:
            continue
        rate = Decimal(fields[1])
        if not rate.is_finite() or abs(rate) > Decimal("0.1"):
            raise ValueError("INVALID_FUNDING_RATE")
        if ts in rates:
            raise ValueError("DUPLICATE_FUNDING_SETTLEMENT")
        rates[ts] = str(rate)
    return rates


def collect(inst, out):
    folder = out / inst
    folder.mkdir(parents=True, exist_ok=True)
    result = {"instrument": inst, "listings": [], "archives": [], "rates": 0,
              "first_ms": None, "last_ms": None, "issue": None}
    rates = {}
    try:
        files = {}
        for i, (begin, end) in enumerate(WINDOWS):
            raw, found = listing(inst, begin, end)
            name = f"listing_{i}.raw.json"
            (folder / name).write_bytes(raw)
            result["listings"].append({"file": name, "sha256": hashlib.sha256(raw).hexdigest(),
                                       "begin": begin, "end": end, "file_count": len(found)})
            for item in found:
                filename = item.get("filename")
                url = item.get("url")
                if not isinstance(filename, str) or not isinstance(url, str):
                    raise ValueError("BAD_ARCHIVE_LISTING")
                if not filename.startswith(inst + "-") or "funding" not in filename.lower():
                    raise ValueError("WRONG_INSTRUMENT_OR_ARCHIVE_MODULE")
                match = re.search(r"(20\d{2})-(\d{2})\.zip$", filename)
                if not match or not ("2022-03" <= match.group(1) + "-" + match.group(2) <= "2023-09"):
                    raise ValueError("ARCHIVE_MONTH_OUTSIDE_ALLOWED_TRAIN")
                parsed = urlsplit(url)
                if parsed.scheme != "https" or parsed.hostname != "static.okx.com" or not parsed.path.endswith("/" + filename):
                    raise ValueError("UNTRUSTED_ARCHIVE_DOWNLOAD_LINK")
                if filename in files and files[filename] != url:
                    raise ValueError("INCONSISTENT_ARCHIVE_URL")
                files[filename] = url
        for idx, (filename, url) in enumerate(sorted(files.items())):
            raw = get(url, 15000000)
            fresh = archive_rows(raw, inst)
            for ts, value in fresh.items():
                if ts in rates and rates[ts] != value:
                    raise ValueError("CONFLICTING_SETTLED_FUNDING")
                rates[ts] = value
            stored = f"archive_{idx:03d}.raw.zip"
            (folder / stored).write_bytes(raw)
            result["archives"].append({"file": stored, "original_filename": filename,
                                       "sha256": hashlib.sha256(raw).hexdigest(),
                                       "funding_rows": len(fresh)})
            time.sleep(0.12)
    except Exception as exc:
        result["issue"] = str(exc)
    result["rates"] = len(rates)
    result["first_ms"] = min(rates) if rates else None
    result["last_ms"] = max(rates) if rates else None
    (folder / "funding_rows.json").write_text(json.dumps(
        [{"settlement_ms": t, "venue_rate": rates[t]} for t in sorted(rates)]) + "\n")
    return result


def main():
    out = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("research_evidence/d1_bulk_funding")
    out.mkdir(parents=True, exist_ok=True)
    instruments = {}
    for inst in INSTS:
        instruments[inst] = collect(inst, out)
        print(inst, "archive files", len(instruments[inst]["archives"]),
              "rates", instruments[inst]["rates"], "issue", instruments[inst]["issue"], flush=True)
    report = {
        "schema": "D1_OKX_BULK_FUNDING_TRAIN_ONLY_V1",
        "status": "DATA_ONLY_PARTIAL_FUNDING_ARCHIVE_NOT_ECONOMICS",
        "train_start_ms": START, "train_end_exclusive_ms": END,
        "instruments": instruments,
        "account_settled_funding_cash_authenticated": False,
        "native_fee_tiers_authenticated": False,
        "actual_execution_fills_authenticated": False,
        "full_2021_2023_train_coverage_authenticated": False,
        "historical_economic_trial_run": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False, "promotion_authorized": False,
    }
    (out / "manifest.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(report["status"], flush=True)
    # A partial funding archive cannot satisfy the original full TRAIN.
    return 2


if __name__ == "__main__":
    sys.exit(main())
