"""Fail-closed ORIGINAL options quote tape intake for I1. No economics/orders.

Unlike the two-day sample gate, accepts 91 original Sunday CSV(.gz) captures
for Monday TRAIN decisions. No sealed future data, no inferred fills.
"""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

UTC = timezone.utc
START = datetime(2021, 12, 9, tzinfo=UTC)
END = datetime(2023, 10, 1, tzinfo=UTC)
ASSETS = ("BTC", "ETH")
REQUIRED = ("exchange", "symbol", "timestamp", "local_timestamp",
            "bid_price", "ask_price", "bid_amount", "ask_amount")


def decisions():
    first = START + timedelta(days=(7 - START.weekday()) % 7)
    return [first + timedelta(days=7*i) for i in range(94)]


def eligible(fixed_tenor=False):
    """Keep the legacy 91-week signal-source scope; opt in to 90 I1 trade weeks."""
    if type(fixed_tenor) is not bool:
        raise ValueError("INVALID_SOURCE_SCOPE")
    ds = decisions()
    assert len(ds) == 94 and ds[0] >= START and ds[-1] < END
    minimum = 28 if fixed_tenor else 21
    yes = [d for d in ds if d + timedelta(days=minimum) < END]
    assert len(yes) == (90 if fixed_tenor else 91)
    return yes


def file_digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def instrument(symbol):
    p = symbol.split("-")
    if len(p) != 4 or p[0] not in ASSETS or p[3] != "P":
        return None
    try:
        expiry = datetime.strptime(p[1], "%d%b%y").replace(hour=8, tzinfo=UTC)
        strike = float(p[2])
    except (ValueError, OverflowError):
        return None
    if not math.isfinite(strike) or strike <= 0:
        return None
    return p[0], expiry, strike


def safe_path(root, name):
    if not isinstance(name, str) or Path(name).name != name or not (
            name.endswith(".csv") or name.endswith(".csv.gz")):
        raise ValueError("INVALID_ARCHIVE_FILENAME")
    path = root / name
    if not path.is_file() or path.is_symlink():
        raise ValueError("ARCHIVE_MISSING_OR_SYMLINK")
    return path


def native_contracts(root):
    """Require original venue bytes before any non-fixture quote is called eligible.

    A self-declared complete quote CSV or invented symbol cannot certify an
    exchange-listed, causally created native contract.
    """
    path = root / "native_instrument_registry.json"
    if not path.is_file() or path.is_symlink():
        raise ValueError("NATIVE_ORIGINAL_REGISTRY_REQUIRED")
    from research.verification.independent_v99_r106_i1_historical_instruments import audit
    try:
        audit(root)  # independently replay original Deribit gzip bytes and SHA256
    except (AssertionError, KeyError, ValueError, OSError) as exc:
        raise ValueError("NATIVE_ORIGINAL_REGISTRY_UNVERIFIED") from exc
    report = json.loads(path.read_text(encoding="utf-8"))
    index = {asset: {item["instrument_name"]: dict(item)
                     for item in report["registry"][asset]} for asset in ASSETS}
    # The nine-field historical registry projection drops tick_size_steps.
    # Recover them ONLY from independently hashed original first-party bytes.
    # Do not infer post-July 2023 price steps from the minimum tick alone.
    for asset in ASSETS:
        source = report["sources"][asset]
        original = gzip.decompress((root / source["original_gzip"]).read_bytes())
        if hashlib.sha256(original).hexdigest() != source["original_raw_sha256"]:
            raise ValueError("NATIVE_TICK_STEPS_SOURCE_HASH_MISMATCH")
        for item in json.loads(original)["result"]:
            name = item.get("instrument_name")
            if name in index[asset]:
                index[asset][name]["tick_size_steps"] = item.get("tick_size_steps")
    return index


def historical_price_grid_ok(meta, decision, bid, ask):
    """Dated Deribit on-screen BTC/ETH options tick regime; no fill certification.

    Deribit 6 July 2023 change notice: <=0.005 uses 0.0001 after change,
    >0.005 uses 0.0005. Old regime used 0.0005. Exact change-day hour
    is unverified, so the entire UTC change day fails closed.
    """
    if meta is None:
        return False
    day = decision.date()
    change = date(2023, 7, 6)
    if day == change:
        return False
    try:
        if day > change:
            if Decimal(str(meta["tick_size"])) != Decimal("0.0001"):
                return False
            steps = meta.get("tick_size_steps")
            if not isinstance(steps, list) or not any(
                Decimal(str(step["above_price"])) == Decimal("0.005")
                and Decimal(str(step["tick_size"])) == Decimal("0.0005")
                for step in steps if isinstance(step, dict)
            ):
                return False
        for value in (bid, ask):
            price = Decimal(str(value))
            tick = (Decimal("0.0005") if day < change or price > Decimal("0.005")
                    else Decimal("0.0001"))
            if not price.is_finite() or price <= 0 or price % tick:
                return False
        return True
    except (KeyError, ValueError, TypeError, InvalidOperation):
        return False



def synchronized_strikes(quotes):
    """Exact <=1s two-clock, distinct-strike test using microsecond buckets.

    Latest-per-symbol rows usually give one quote per strike. Bucket indexing
    avoids scanning every strike pair on dense historical option chains.
    All neighboring cells are checked against *exact* microseconds; adjacent
    buckets alone never imply a synchronized pair. Duplicates remain correct.
    """
    cells = defaultdict(list)
    window = 1_000_000
    for strike, arrival, event in quotes:
        a, e = arrival // window, event // window
        for ai in (a-1, a, a+1):
            for ei in (e-1, e, e+1):
                for other_strike, other_arrival, other_event in cells.get((ai, ei), ()):
                    if (other_strike != strike
                            and abs(other_arrival-arrival) <= window
                            and abs(other_event-event) <= window):
                        return True
        cells[(a, e)].append((strike, arrival, event))
    return False


def evaluate(root):
    root = Path(root)
    manifest = json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    schema = manifest.get("schema")
    if schema not in ("I1_FULL_TRAIN_SUNDAY_ARCHIVE_V1",
                      "I1_FIXED_TENOR_TRAIN_SUNDAY_ARCHIVE_V1"):
        raise ValueError("BAD_ARCHIVE_SCHEMA")
    fixed_tenor = schema == "I1_FIXED_TENOR_TRAIN_SUNDAY_ARCHIVE_V1"
    if manifest.get("venue") != "deribit" or type(manifest.get("fixture")) is not bool:
        raise ValueError("BAD_VENUE_OR_FIXTURE_FLAG")
    days = manifest.get("days")
    ds = eligible(fixed_tenor)
    native = None if manifest["fixture"] else native_contracts(root)
    if not isinstance(days, list) or len(days) != len(ds):
        raise ValueError("INCOMPLETE_OR_DUPLICATED_DECISION_DAYS")
    if [x.get("date") for x in days] != [
            (d-timedelta(days=1)).strftime("%Y-%m-%d") for d in ds]:
        raise ValueError("NOT_EXACT_FROZEN_SUNDAY_SCHEDULE")
    if len({x.get("file") for x in days}) != len(ds):
        raise ValueError("DUPLICATED_ARCHIVE_FILE")
    fold_edges = [datetime(2021,12,9,tzinfo=UTC),
                  datetime(2022,4,20,4,tzinfo=UTC),
                  datetime(2022,8,30,9,tzinfo=UTC),
                  datetime(2023,1,9,14,tzinfo=UTC),
                  datetime(2023,5,21,19,tzinfo=UTC), END]
    folds = {str(i): {a: 0 for a in ASSETS} for i in range(1,6)}
    synchronized_folds = {str(i): {a: 0 for a in ASSETS} for i in range(1,6)}
    coverage = []
    total_rows = 0
    for d, item in zip(ds, days):
        if item.get("complete_capture") is not True:
            raise ValueError("MISSING_VENDOR_COMPLETENESS_ATTESTATION")
        path = safe_path(root, item["file"])
        if file_digest(path) != item.get("sha256"):
            raise ValueError("ARCHIVE_SHA256_MISMATCH")
        open_fn = gzip.open if path.name.endswith(".gz") else open
        sunday = d - timedelta(days=1)
        lower = int(sunday.timestamp()*1_000_000)
        upper = int(d.timestamp()*1_000_000)
        cutoff = upper - 300_000_000
        latest = {}
        rows = 0
        previous_arrival = None
        with open_fn(path, "rt", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if not set(REQUIRED).issubset(reader.fieldnames or []):
                raise ValueError("MISSING_REQUIRED_QUOTE_COLUMNS")
            for row in reader:
                rows += 1
                if row["exchange"] != "deribit":
                    raise ValueError("UNEXPECTED_EXCHANGE")
                try:
                    arrival = int(row["local_timestamp"])
                    exchange = int(row["timestamp"])
                except (ValueError, TypeError):
                    raise ValueError("INVALID_SOURCE_TIMESTAMP")
                if not lower <= arrival < upper or exchange > arrival:
                    raise ValueError("FUTURE_OR_OUTSIDE_SUNDAY_SOURCE")
                if previous_arrival is not None and arrival < previous_arrival:
                    raise ValueError("OUT_OF_ORDER_ORIGINAL_CAPTURE")
                previous_arrival = arrival
                if arrival < cutoff:
                    continue
                parsed = instrument(row["symbol"])
                if parsed is None:
                    continue
                asset, expiry, strike = parsed
                if not (timedelta(days=(28 if fixed_tenor else 21))
                        <= expiry-d <= timedelta(days=(35 if fixed_tenor else 45))
                        and expiry < END):
                    continue
                try:
                    bid, ask, bs, az = (float(row[k]) for k in
                        ("bid_price","ask_price","bid_amount","ask_amount"))
                    valid = (all(map(math.isfinite,(bid,ask,bs,az)))
                             and 0 < bid < ask and bs > 0 and az > 0
                             and exchange >= cutoff)  # venue event must be fresh too
                except (ValueError, TypeError):
                    valid = False
                if valid and native is not None:
                    metadata = native[asset].get(row["symbol"])
                    valid = bool(metadata is not None
                        and metadata["creation_timestamp"] <= int(d.timestamp()*1000)
                        and metadata["expiration_timestamp"] == int(expiry.timestamp()*1000)
                        and float(metadata["strike"]) == strike
                        and metadata["settlement_currency"] == asset
                        and all(metadata[k] is not None and float(metadata[k]) > 0
                                for k in ("contract_size","min_trade_amount","tick_size"))
                        and historical_price_grid_ok(metadata, d, bid, ask))
                # A newer quote for an unlisted contract must also revoke an older one.
                # Even a malformed newer quote cancels an older good quote.
                # Original CSV capture order is authoritative on timestamp ties.
                # A later invalid/stale update revokes the previous book.
                latest[row["symbol"]] = (arrival,exchange,asset,expiry,
                    strike,valid)
        if rows != item.get("rows"):
            raise ValueError("ARCHIVE_ROW_COUNT_MISMATCH")
        total_rows += rows
        strikes = defaultdict(set)
        timed = defaultdict(list)
        for arrival,exchange,asset,expiry,strike,valid in latest.values():
            if valid:
                strikes[(asset,expiry)].add(strike)
                timed[(asset,expiry)].append((strike,arrival,exchange))
        fold = next(i for i in range(1,6) if fold_edges[i-1] <= d < fold_edges[i])
        good, synchronized = {}, {}
        for asset in ASSETS:
            good[asset] = any(a == asset and len(s) >= 2
                              for (a,_),s in strikes.items())
            synchronized[asset] = any(
                a == asset and synchronized_strikes(rows)
                for (a,_),rows in timed.items())
            folds[str(fold)][asset] += int(good[asset])
            synchronized_folds[str(fold)][asset] += int(synchronized[asset])
        coverage.append({"decision_utc":d.isoformat(),"fold":fold,
                         "BTC":good["BTC"],"ETH":good["ETH"],
                         "synchronized_BTC":synchronized["BTC"],
                         "synchronized_ETH":synchronized["ETH"]})
    pairs = sum(sum(v.values()) for v in folds.values())
    synchronized_pairs = sum(sum(v.values()) for v in synchronized_folds.values())
    return {
        "schema":"I1_FULL_TRAIN_ARCHIVE_INTAKE_RESULT_V1",
        "status":("SYNTHETIC_FIXTURE_ONLY_NO_ECONOMICS" if manifest["fixture"]
                  else "ORIGINAL_ARCHIVE_INPUT_CHECKED_NOT_EXECUTION_CERTIFIED"),
        "source_declared_complete_not_independently_vendor_certified":True,
        "fixture":manifest["fixture"],"native_registry_verified":native is not None,
        "train_decisions":94,
        "source_scope": ("FIXED_28_35D" if fixed_tenor else "LEGACY_21_45D"),
        "maturity_eligible_weeks":len(ds),
        "right_censored_weeks":94-len(ds),
        "required_asset_weeks":2*len(ds),"two_strike_asset_weeks":pairs,
        "synchronized_two_strike_asset_weeks":synchronized_pairs,
        "synchronized_max_skew_us":1_000_000,
        "rows":total_rows,"folds":folds,"synchronized_folds":synchronized_folds,
        "weekly":coverage,
        "economic_train_executed":False,"native_fee_authenticated":False,
        "native_margin_authenticated":False,"fills_authenticated":False,
        "validation_opened":False,"holdout_opened":False,
        "orders_enabled":False,"promotion_authorized":False
    }


def main(root, output):
    result = evaluate(root)
    out = Path(output)
    out.mkdir(parents=True,exist_ok=True)
    (out/"intake.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="weekly"},sort_keys=True))
    assert not result["promotion_authorized"] and not result["economic_train_executed"]


if __name__ == "__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_full_archive_intake ROOT OUT")
    main(sys.argv[1],sys.argv[2])
