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
from datetime import datetime, timedelta, timezone
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


def audit(root, output):
    root=Path(root)
    report=json.loads(Path(output).read_text())
    manifest=json.loads((root/"manifest.json").read_text())
    assert report["schema"]=="I1_FULL_TRAIN_ARCHIVE_INTAKE_RESULT_V1"
    assert manifest["schema"]=="I1_FULL_TRAIN_SUNDAY_ARCHIVE_V1"
    assert report["fixture"]==manifest["fixture"]
    native = None if manifest["fixture"] else original_native_lookup(root)
    assert report["native_registry_verified"] == (native is not None)
    assert report["train_decisions"]==94
    assert report["maturity_eligible_weeks"]==91
    assert report["right_censored_weeks"]==3
    assert report["required_asset_weeks"]==182
    assert len(manifest["days"])==91 and len(report["weekly"])==91
    assert not any(report[k] for k in ("economic_train_executed",
        "native_fee_authenticated","native_margin_authenticated",
        "fills_authenticated","validation_opened","holdout_opened",
        "orders_enabled","promotion_authorized"))
    days=[]
    current=datetime(2021,12,13,tzinfo=UTC)
    while current+timedelta(days=21)<STOP:
        days.append(current)
        current+=timedelta(days=7)
    assert len(days)==91
    computed={str(i):{"BTC":0,"ETH":0} for i in range(1,6)}
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
                if arrival<cutoff: continue
                key=row["symbol"]
                prev=most_recent.get(key)
                if prev is None or (arrival,exchange)>=prev[0]:
                    most_recent[key]=((arrival,exchange),row)
        assert lines==item["rows"]
        count+=lines
        valid=defaultdict(set)
        for (_,r) in most_recent.values():
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
                or not (timedelta(days=21)<=expiry-decision<=timedelta(days=45))
                or expiry>=STOP): continue
            if native is not None:
                meta = native[parts[0]].get(r["symbol"])
                if (meta is None or
                    int(meta["creation_timestamp"]) > int(decision.timestamp()*1000) or
                    int(meta["expiration_timestamp"]) != int(expiry.timestamp()*1000) or
                    float(meta["strike"]) != strike or
                    meta["settlement_currency"] != parts[0] or
                    any(meta.get(k) is None or float(meta[k]) <= 0 for k in
                        ("contract_size","min_trade_amount","tick_size"))):
                    continue
            valid[(parts[0],expiry)].add(strike)
        f=next(i for i in range(1,6) if BOUNDARIES[i-1]<=decision<BOUNDARIES[i])
        assert expected["decision_utc"]==decision.isoformat() and expected["fold"]==f
        for asset in ("BTC","ETH"):
            ok=any(a==asset and len(strikes)>=2
                   for (a,_),strikes in valid.items())
            assert ok==expected[asset], "INDEPENDENT_WEEKLY_QUOTE_MISMATCH"
            computed[str(f)][asset]+=int(ok)
    assert count==report["rows"]
    assert computed==report["folds"], "INDEPENDENT_FOLD_MISMATCH"
    assert sum(sum(x.values()) for x in computed.values())==report["two_strike_asset_weeks"]
    print(json.dumps({"status":"INDEPENDENT_FULL_ARCHIVE_BYTE_TO_DECISION_VERIFIED",
                      "rows":count,"pairs":report["two_strike_asset_weeks"],
                      "folds":computed,"fixture":manifest["fixture"],
                      "economics":False,"promotion":False},sort_keys=True))


if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_full_archive_intake ROOT REPORT")
    audit(sys.argv[1],sys.argv[2])
