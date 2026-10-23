"""Independent original-byte oracle for D1 historical OKX bulk funding archives.

Verifies ZIP SHA-256, instrument identity, settlement timestamps, 8h cadence,
and exact published rates without relying on the archive downloader parser.
Does NOT claim account-settled cash, fees, fills, economics or promotion.
"""
from __future__ import annotations
import hashlib
import io
import json
import sys
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
INSTS = ("BTC-USDT-SWAP", "ETH-USDT-SWAP")


def check(root):
    root = Path(root)
    m = json.loads((root / "manifest.json").read_bytes())
    if m["train_start_ms"] != START or m["train_end_exclusive_ms"] != END:
        raise ValueError("CHANGED_TRAIN_SPLIT")
    for k in ("account_settled_funding_cash_authenticated",
              "native_fee_tiers_authenticated", "actual_execution_fills_authenticated",
              "full_2021_2023_train_coverage_authenticated",
              "historical_economic_trial_run", "validation_opened",
              "holdout_opened", "orders_enabled", "promotion_authorized"):
        if m.get(k) is not False:
            raise ValueError("INVALID_ECONOMIC_PERMISSION")
    if set(m["instruments"]) != set(INSTS):
        raise ValueError("MISSING_FUNDING_ASSET")
    report = {}
    for inst in INSTS:
        folder = root / inst
        entry = m["instruments"][inst]
        recovered = {}
        for item in entry["archives"]:
            raw = (folder / item["file"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError("FUNDING_ZIP_HASH_MISMATCH")
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                members = [x for x in archive.namelist() if x.lower().endswith(".csv")]
                if len(members) != 1:
                    raise ValueError("INVALID_FUNDING_ZIP")
                for line in archive.read(members[0]).decode("utf-8-sig").splitlines():
                    parts = line.strip().split(",")
                    if len(parts) < 3 or parts[0] != inst:
                        continue
                    if not parts[2].isdecimal():
                        raise ValueError("BAD_SETTLEMENT_TIME")
                    stamp = int(parts[2])
                    if stamp < START or stamp >= END:
                        raise ValueError("OUT_OF_TRAIN_FUNDING")
                    rate = Decimal(parts[1])
                    if not rate.is_finite() or abs(rate) > Decimal("0.1"):
                        raise ValueError("BAD_SETTLEMENT_RATE")
                    if stamp in recovered and recovered[stamp] != str(rate):
                        raise ValueError("CONFLICTING_FUNDING_RECEIPTS")
                    recovered[stamp] = str(rate)
        stored = json.loads((folder / "funding_rows.json").read_bytes())
        if stored != [{"settlement_ms": t, "venue_rate": recovered[t]} for t in sorted(recovered)]:
            raise ValueError("ARCHIVE_VS_DOWNLOADER_RATE_MISMATCH")
        if len(recovered) != entry["rates"]:
            raise ValueError("FUNDING_COUNT_MISMATCH")
        ordered = sorted(recovered)
        gaps = [(a, b) for a, b in zip(ordered, ordered[1:]) if b-a != 8*3600000]
        report[inst] = {
            "first_settlement_ms": ordered[0] if ordered else None,
            "last_settlement_ms": ordered[-1] if ordered else None,
            "venue_funding_rates": len(recovered),
            "raw_archives_verified": len(entry["archives"]),
            "non_8h_intervals": len(gaps),
        }
    return {"status": "INDEPENDENT_PARTIAL_FIRST_PARTY_FUNDING_NO_ECONOMICS",
            "instruments": report, "account_settled_cash_verified": False,
            "full_train_coverage_verified": False, "promotion_authorized": False}


def main():
    print(json.dumps(check(sys.argv[1]), sort_keys=True))


if __name__ == "__main__":
    main()
