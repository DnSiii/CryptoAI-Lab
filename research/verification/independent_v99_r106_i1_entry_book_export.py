"""Independent raw-byte reconstruction of I1 exported entry books (NO PNL)."""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
STOP = datetime(2023, 10, 1, tzinfo=UTC)

def audit(root, export_path):
    root = Path(root)
    export = json.loads(Path(export_path).read_text(encoding="utf-8"))
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert export["schema"] == "I1_ORIGINAL_ENTRY_BOOK_EXPORT_V1"
    assert manifest["schema"] == "I1_FULL_TRAIN_SUNDAY_ARCHIVE_V1"
    assert export["fixture"] == manifest["fixture"]
    assert not any(export[k] for k in ("economic_train_executed",
        "validation_opened", "holdout_opened", "promotion_authorized", "orders_enabled"))
    expected = []
    for i, item in enumerate(manifest["days"]):
        decision = datetime(2021, 12, 13, tzinfo=UTC) + timedelta(days=7*i)
        assert decision + timedelta(days=21) < STOP
        path = root / item["file"]
        assert path.name == item["file"] and path.is_file() and not path.is_symlink()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        cutoff = int(decision.timestamp()*1_000_000)-300_000_000
        upper = int(decision.timestamp()*1_000_000)
        lower = upper - 86_400_000_000
        latest = {}
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            assert set(("exchange","symbol","timestamp","local_timestamp",
                "bid_price","ask_price","bid_amount","ask_amount")).issubset(reader.fieldnames)
            n = 0
            for row in reader:
                n += 1
                assert row["exchange"] == "deribit"
                arrival, event = int(row["local_timestamp"]), int(row["timestamp"])
                assert lower <= arrival < upper and event <= arrival
                if arrival < cutoff:
                    continue
                symbol = row["symbol"]
                previous = latest.get(symbol)
                if previous is None or (arrival, event) >= previous[0]:
                    latest[symbol] = ((arrival,event),row)
        assert n == item["rows"]
        for symbol, ((arrival,event),row) in latest.items():
            parts = symbol.split("-")
            if len(parts)!=4 or parts[0] not in ("BTC","ETH") or parts[3]!="P":
                continue
            try:
                expiry = datetime.strptime(parts[1], "%d%b%y").replace(hour=8,tzinfo=UTC)
                strike = float(parts[2])
                bid,ask,bs,az = (float(row[k]) for k in
                    ("bid_price","ask_price","bid_amount","ask_amount"))
            except (ValueError,TypeError):
                continue
            if not (all(map(math.isfinite,(strike,bid,ask,bs,az)))
                    and strike > 0 and 0 < bid < ask and bs > 0 and az > 0
                    and event >= cutoff and timedelta(days=21) <= expiry-decision
                    <= timedelta(days=45) and expiry < STOP):
                continue
            fold_edges = [
                datetime(2021,12,9,tzinfo=UTC),datetime(2022,4,20,4,tzinfo=UTC),
                datetime(2022,8,30,9,tzinfo=UTC),datetime(2023,1,9,14,tzinfo=UTC),
                datetime(2023,5,21,19,tzinfo=UTC),STOP]
            fold = next(j for j in range(1,6) if fold_edges[j-1]<=decision<fold_edges[j])
            expected.append({
                "decision_utc": decision.isoformat(), "fold": fold,
                "asset": parts[0], "symbol": symbol, "strike_usd": strike,
                "expiry_utc": expiry.isoformat(), "bid_coin": bid, "ask_coin": ask,
                "bid_size_source_units": bs, "ask_size_source_units": az,
                "exchange_us": event, "arrival_us": arrival,
                "source_file": item["file"], "source_sha256": item["sha256"],
            })
    key = lambda x: (x["decision_utc"],x["symbol"])
    assert sorted(expected,key=key) == sorted(export["quotes"],key=key), (
        "INDEPENDENT_RAW_BYTE_ENTRY_BOOK_MISMATCH")
    by_expiry = defaultdict(set)
    for x in expected:
        by_expiry[(x["decision_utc"],x["asset"],x["expiry_utc"])].add(x["strike_usd"])
    by_asset = {(d,a) for (d,a,_),strikes in by_expiry.items() if len(strikes)>=2}
    assert len(by_asset) == export["source_pairs"]
    assert export["required_pairs"] == 182
    print(json.dumps({"independent":"VERIFIED_ORIGINAL_BYTE_TO_BOOK",
        "quote_count":len(expected),"asset_weeks":len(by_asset),
        "fixture":export["fixture"],"economic_train":False,"promotion":False},
        sort_keys=True))
    return len(expected)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_entry_book_export ROOT EXPORT")
    audit(sys.argv[1],sys.argv[2])
