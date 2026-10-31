"""Independent ORIGINAL byte/quote-to-week oracle for I1 full-tape intake.

No import of the primary parser, calendar, folds or grouping algorithm.
No economic claims, live orders, validation or holdout.
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

UTC=timezone.utc
BEGIN=datetime(2021,12,9,tzinfo=UTC)
STOP=datetime(2023,10,1,tzinfo=UTC)
BOUNDARIES=[
    BEGIN,datetime(2022,4,20,4,tzinfo=UTC),
    datetime(2022,8,30,9,tzinfo=UTC),
    datetime(2023,1,9,14,tzinfo=UTC),
    datetime(2023,5,21,19,tzinfo=UTC),STOP
]


def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as fp:
        while True:
            part=fp.read(65536)
            if not part: break
            h.update(part)
    return h.hexdigest()


def original_native_lookup(root):
    """Separate raw-exchange reparse, no import of primary intake or registry gate."""
    path = root / "native_instrument_registry.json"
    if not path.is_file() or path.is_symlink():
        raise AssertionError("INDEPENDENT_NATIVE_ORIGINAL_REGISTRY_MISSING")
    report = json.loads(path.read_text())
    assert report["schema"] == "V99_I1_DERIBIT_HISTORICAL_INSTRUMENT_REGISTRY_V1"
    assert report["train_start_ms"] == 1639008000000
    assert report["train_end_exclusive_ms"] == 1696118400000
    assert set(report["registry"]) == {"BTC","ETH"}
    index = {}
    for asset in ("BTC","ETH"):
        info = report["sources"][asset]
        assert info["endpoint"] == "https://history.deribit.com/api/v2/public/get_instruments"
        source_path = root / info["original_gzip"]
        assert source_path.is_file() and not source_path.is_symlink()
        original = gzip.decompress(source_path.read_bytes())
        assert hashlib.sha256(original).hexdigest() == info["original_raw_sha256"]
        assert len(original) == info["original_response_bytes"]
        raw_rows = json.loads(original)["result"]
        assert len(raw_rows) == info["original_instruments"]
        subset = {}
        for row in raw_rows:
            if row.get("kind") != "option" or row.get("option_type") != "put":
                continue
            expiry = row.get("expiration_timestamp")
            if expiry is None or not 1639008000000 <= int(expiry) < 1696118400000:
                continue
            name = row["instrument_name"]
            assert name not in subset
            subset[name] = row
        fields = ("instrument_name","creation_timestamp","expiration_timestamp",
                  "strike","option_type","settlement_currency","contract_size",
                  "min_trade_amount","tick_size")
        listed = {row["instrument_name"]: row for row in report["registry"][asset]}
        assert set(subset) == set(listed)
        for name, row in listed.items():
            assert row == {k: subset[name].get(k) for k in fields}
        index[asset] = subset
    return index



def independently_check_historical_ticks(native_record, when, prices):
    """Independent Decimal grid reconstruction from dated venue notice."""
    if native_record is None or when.date() == date(2023, 7, 6):
        return False
    try:
        if when.date() > date(2023, 7, 6):
            if Decimal(str(native_record["tick_size"])) != Decimal("0.0001"):
                return False
            steps = native_record.get("tick_size_steps")
            if not isinstance(steps, list):
                return False
            valid_step = False
            for step in steps:
                if not isinstance(step, dict):
                    continue
                if (Decimal(str(step["above_price"])) == Decimal("0.005")
                        and Decimal(str(step["tick_size"])) == Decimal("0.0005")):
                    valid_step = True
            if not valid_step:
                return False
        for v in prices:
            p = Decimal(str(v))
            grid = Decimal("0.0005")
            if when.date() > date(2023, 7, 6) and p <= Decimal("0.005"):
                grid = Decimal("0.0001")
            if not p.is_finite() or p <= 0 or p % grid != 0:
                return False
        return True
    except (KeyError, ValueError, TypeError, InvalidOperation):
        return False



def independent_atomic(ticks):
    """Independent raw-byte replay: exact two-clock pair in neighboring cells.

    Event-clock coordinate is deliberately the primary key, unlike the
    production arrival-first grouping. Check exact timestamps and strikes
    after bucket lookup to avoid boundary false positives.
    """
    by_event_arrival = defaultdict(list)
    for strike, arrival, event in ticks:
        event_cell, arrival_cell = event // 1_000_000, arrival // 1_000_000
        for event_neighbor in range(event_cell-1, event_cell+2):
            for arrival_neighbor in range(arrival_cell-1, arrival_cell+2):
                for prior in by_event_arrival.get((event_neighbor, arrival_neighbor), ()):
                    if (prior[0] != strike
                            and abs(prior[1] - arrival) <= 1_000_000
                            and abs(prior[2] - event) <= 1_000_000):
                        return True
        by_event_arrival[(event_cell, arrival_cell)].append(
            (strike, arrival, event))
    return False


def audit(root, output):
    root=Path(root)
    report=json.loads(Path(output).read_text())
    manifest=json.loads((root/"manifest.json").read_text())
    assert report["schema"]=="I1_FULL_TRAIN_ARCHIVE_INTAKE_RESULT_V1"
    assert manifest["schema"] in ("I1_FULL_TRAIN_SUNDAY_ARCHIVE_V1",
        "I1_FIXED_TENOR_TRAIN_SUNDAY_ARCHIVE_V1")
    fixed = manifest["schema"] == "I1_FIXED_TENOR_TRAIN_SUNDAY_ARCHIVE_V1"
    assert report["source_scope"] == ("FIXED_28_35D" if fixed else "LEGACY_21_45D")
    assert report["fixture"]==manifest["fixture"]
    native = None if manifest["fixture"] else original_native_lookup(root)
    assert report["native_registry_verified"] == (native is not None)
    assert report["train_decisions"]==94
    assert report["maturity_eligible_weeks"]==(90 if fixed else 91)
    assert report["right_censored_weeks"]==(4 if fixed else 3)
    assert report["required_asset_weeks"]==(180 if fixed else 182)
    assert len(manifest["days"])==(90 if fixed else 91)
    assert len(report["weekly"])==(90 if fixed else 91)
    assert not any(report[k] for k in ("economic_train_executed",
        "native_fee_authenticated","native_margin_authenticated",
        "fills_authenticated","validation_opened","holdout_opened",
        "orders_enabled","promotion_authorized"))
    days=[]
    current=datetime(2021,12,13,tzinfo=UTC)
    while current+timedelta(days=(28 if fixed else 21))<STOP:
        days.append(current)
        current+=timedelta(days=7)
    assert len(days)==(90 if fixed else 91)
    computed={str(i):{"BTC":0,"ETH":0} for i in range(1,6)}
    synchronized={str(i):{"BTC":0,"ETH":0} for i in range(1,6)}
    assert report["synchronized_max_skew_us"] == 1_000_000
    count=0
    for decision,item,expected in zip(days,manifest["days"],report["weekly"]):
        sunday=decision-timedelta(days=1)
        assert item["date"]==sunday.strftime("%Y-%m-%d")
        assert item["complete_capture"] is True
        filename=item["file"]
        assert filename==Path(filename).name
        path=root/filename
        assert path.is_file() and not path.is_symlink()
        assert digest(path)==item["sha256"]
        open_file=gzip.open if filename.endswith(".gz") else open
        cutoff=int(decision.timestamp()*1_000_000)-300_000_000
        lower=int(sunday.timestamp()*1_000_000)
        end=int(decision.timestamp()*1_000_000)
        most_recent={}
        lines=0
        last_seen_arrival=None
        with open_file(path,"rt",encoding="utf-8",newline="") as fp:
            reader=csv.DictReader(fp)
            assert set(("exchange","symbol","timestamp","local_timestamp",
                "bid_price","ask_price","bid_amount","ask_amount")).issubset(reader.fieldnames)
            for row in reader:
                lines+=1
                assert row["exchange"]=="deribit"
                arrival=int(row["local_timestamp"])
                exchange=int(row["timestamp"])
                assert lower<=arrival<end and exchange<=arrival
                assert last_seen_arrival is None or arrival>=last_seen_arrival, (
                    "INDEPENDENT_OUT_OF_ORDER_ORIGINAL_CAPTURE")
                last_seen_arrival=arrival
                if arrival<cutoff: continue
                # Independently reconstruct last physical CSV row, not max venue timestamp.
                most_recent[row["symbol"]]=((arrival,exchange),row)
        assert lines==item["rows"]
        count+=lines
        valid=defaultdict(set)
        timed=defaultdict(list)
        for ((arrival,event),r) in most_recent.values():
            parts=r["symbol"].split("-")
            if len(parts)!=4 or parts[0] not in ("BTC","ETH") or parts[3]!="P":
                continue
            try:
                expiry=datetime.strptime(parts[1],"%d%b%y").replace(hour=8,tzinfo=UTC)
                strike=float(parts[2])
                bid=float(r["bid_price"]);ask=float(r["ask_price"])
                bs=float(r["bid_amount"]);az=float(r["ask_amount"])
            except (ValueError,TypeError): continue
            if not all(math.isfinite(x) for x in (strike,bid,ask,bs,az)):
                continue
            if (strike<=0 or not (0<bid<ask and bs>0 and az>0)
                or int(r["timestamp"])<cutoff  # independent exchange-time bound
                or not (timedelta(days=(28 if fixed else 21))
                        <=expiry-decision<=timedelta(days=(35 if fixed else 45)))
                or expiry>=STOP): continue
            if native is not None:
                meta = native[parts[0]].get(r["symbol"])
                if (meta is None or
                    int(meta["creation_timestamp"]) > int(decision.timestamp()*1000) or
                    int(meta["expiration_timestamp"]) != int(expiry.timestamp()*1000) or
                    float(meta["strike"]) != strike or
                    meta["settlement_currency"] != parts[0] or
                    any(meta.get(k) is None or float(meta[k]) <= 0 for k in
                        ("contract_size","min_trade_amount","tick_size")) or
                    not independently_check_historical_ticks(meta, decision, (bid, ask))):
                    continue
            valid[(parts[0],expiry)].add(strike)
            timed[(parts[0],expiry)].append((strike,arrival,event))
        f=next(i for i in range(1,6) if BOUNDARIES[i-1]<=decision<BOUNDARIES[i])
        assert expected["decision_utc"]==decision.isoformat() and expected["fold"]==f
        for asset in ("BTC","ETH"):
            ok=any(a==asset and len(strikes)>=2
                   for (a,_),strikes in valid.items())
            assert ok==expected[asset], "INDEPENDENT_WEEKLY_QUOTE_MISMATCH"
            computed[str(f)][asset]+=int(ok)
            # Separate independent replay of the predeclared <=1s
            # two-leg arrival AND exchange-event simultaneity requirement.
            atomic=any(a==asset and independent_atomic(q)
                for (a,_),q in timed.items())
            assert expected["synchronized_"+asset] == atomic, (
                "INDEPENDENT_SYNCHRONIZED_WEEK_MISMATCH")
            synchronized[str(f)][asset]+=int(atomic)
    assert count==report["rows"]
    assert computed==report["folds"], "INDEPENDENT_FOLD_MISMATCH"
    assert synchronized==report["synchronized_folds"], "INDEPENDENT_SYNC_FOLD_MISMATCH"
    assert sum(sum(x.values()) for x in computed.values())==report["two_strike_asset_weeks"]
    assert sum(sum(x.values()) for x in synchronized.values())==report["synchronized_two_strike_asset_weeks"]
    print(json.dumps({"status":"INDEPENDENT_FULL_ARCHIVE_BYTE_TO_DECISION_VERIFIED",
                      "rows":count,"pairs":report["two_strike_asset_weeks"],
                      "synchronized_pairs":report["synchronized_two_strike_asset_weeks"],
                      "folds":computed,"fixture":manifest["fixture"],
                      "economics":False,"promotion":False},sort_keys=True))


if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_full_archive_intake ROOT REPORT")
    audit(sys.argv[1],sys.argv[2])
