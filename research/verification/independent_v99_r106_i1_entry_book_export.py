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

def independent_stream_digest(path):
    """Hash original compressed bytes without loading a multi-GiB source."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def audit(root, export_path):
    root = Path(root)
    export = json.loads(Path(export_path).read_text(encoding="utf-8"))
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert export["schema"] == "I1_ORIGINAL_ENTRY_BOOK_EXPORT_V1"
    assert manifest["schema"] in ("I1_FULL_TRAIN_SUNDAY_ARCHIVE_V1",
        "I1_FIXED_TENOR_TRAIN_SUNDAY_ARCHIVE_V1")
    fixed = manifest["schema"] == "I1_FIXED_TENOR_TRAIN_SUNDAY_ARCHIVE_V1"
    assert export["source_scope"] == ("FIXED_28_35D" if fixed else "LEGACY_21_45D")
    assert len(manifest["days"]) == (90 if fixed else 91)
    assert export["fixture"] == manifest["fixture"]
    from research.verification.independent_v99_r106_i1_full_archive_intake import (
        original_native_lookup, independently_check_historical_ticks, independent_atomic)
    native = None if manifest["fixture"] else original_native_lookup(root)
    native_sources = (None if native is None else json.loads(
        (root / "native_instrument_registry.json").read_text())["sources"])
    assert export["native_registry_verified"] == (native is not None)
    assert export["native_terms_bound_to_original_bytes"] == (native is not None)
    assert export["historical_dated_price_grid_checked"] == (native is not None)
    assert export["historical_native_lot_asof_certified"] is False
    assert export["historical_fee_asof_certified"] is False
    assert export["quote_size_to_native_lot_conversion_certified"] is False
    assert export["historical_fee_margin_certified"] is False
    assert not any(export[k] for k in ("economic_train_executed",
        "validation_opened", "holdout_opened", "promotion_authorized", "orders_enabled"))
    expected = []
    for i, item in enumerate(manifest["days"]):
        decision = datetime(2021, 12, 13, tzinfo=UTC) + timedelta(days=7*i)
        assert decision + timedelta(days=(28 if fixed else 21)) < STOP
        path = root / item["file"]
        assert path.name == item["file"] and path.is_file() and not path.is_symlink()
        assert independent_stream_digest(path) == item["sha256"]
        cutoff = int(decision.timestamp()*1_000_000)-300_000_000
        upper = int(decision.timestamp()*1_000_000)
        lower = upper - 86_400_000_000
        latest = {}
        last_seen_arrival = None
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
                assert last_seen_arrival is None or arrival >= last_seen_arrival, (
                    "INDEPENDENT_OUT_OF_ORDER_ORIGINAL_CAPTURE")
                last_seen_arrival = arrival
                if arrival < cutoff:
                    continue
                # Independent raw-byte capture sequence; do not sort by event timestamp.
                latest[row["symbol"]] = ((arrival,event),row)
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
                    and event >= cutoff
                    and timedelta(days=(28 if fixed else 21)) <= expiry-decision
                    <= timedelta(days=(35 if fixed else 45)) and expiry < STOP):
                continue
            meta = None
            if native is not None:
                meta = native[parts[0]].get(symbol)
                if (meta is None or
                    int(meta["creation_timestamp"]) > int(decision.timestamp()*1000) or
                    int(meta["expiration_timestamp"]) != int(expiry.timestamp()*1000) or
                    float(meta["strike"]) != strike or
                    meta["settlement_currency"] != parts[0] or
                    any(meta.get(k) is None or float(meta[k]) <= 0 for k in
                        ("contract_size","min_trade_amount","tick_size")) or
                    not independently_check_historical_ticks(meta, decision, (bid, ask))):
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
                # Independent original compressed venue bytes, NOT the primary
                # exporter metadata lookup. Exact terms must survive export.
                "native_contract_terms": (None if meta is None else {
                    k: meta[k] for k in ("contract_size", "min_trade_amount",
                                         "tick_size", "settlement_currency",
                                         "creation_timestamp", "expiration_timestamp",
                                         "tick_size_steps")}),
                "native_registry_source_sha256": (None if native_sources is None
                    else native_sources[parts[0]]["original_raw_sha256"]),
            })
    key = lambda x: (x["decision_utc"],x["symbol"])
    assert sorted(expected,key=key) == sorted(export["quotes"],key=key), (
        "INDEPENDENT_RAW_BYTE_ENTRY_BOOK_MISMATCH")
    by_expiry = defaultdict(set)
    for x in expected:
        by_expiry[(x["decision_utc"],x["asset"],x["expiry_utc"])].add(x["strike_usd"])
    by_asset = {(d,a) for (d,a,_),strikes in by_expiry.items() if len(strikes)>=2}
    assert len(by_asset) == export["source_pairs"]
    assert export["synchronized_max_skew_us"] == 1_000_000
    timed = defaultdict(list)
    for q in expected:
        timed[(q["decision_utc"],q["asset"],q["expiry_utc"])].append(q)
    synchronized_asset_weeks = set()
    for (day, asset, _), quotes in timed.items():
        # Independent event-first bucket algorithm, not the primary matcher.
        if independent_atomic([
            (q["strike_usd"], q["arrival_us"], q["exchange_us"])
            for q in quotes
        ]):
            synchronized_asset_weeks.add((day, asset))
    assert len(synchronized_asset_weeks) == export["synchronized_source_pairs"], (
        "INDEPENDENT_ENTRY_SYNC_PAIR_MISMATCH")
    assert export["required_pairs"] == (180 if fixed else 182)
    print(json.dumps({"independent":"VERIFIED_ORIGINAL_BYTE_TO_BOOK",
        "quote_count":len(expected),"asset_weeks":len(by_asset),
        "synchronized_asset_weeks":len(synchronized_asset_weeks),
        "fixture":export["fixture"],"economic_train":False,"promotion":False},
        sort_keys=True))
    return len(expected)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_entry_book_export ROOT EXPORT")
    audit(sys.argv[1],sys.argv[2])
