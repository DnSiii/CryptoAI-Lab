"""Independent raw-gzip minute replay; never trusts primary parser or summary."""
from __future__ import annotations
import gzip
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

DAYS = ("2022-05-01", "2023-01-01")
P = re.compile(r"^(BTC|ETH)-(\d{1,2}[A-Z]{3}\d{2})-(\d+(?:\.\d+)?)-P$")
END = datetime(2023,10,1,tzinfo=timezone.utc)


def dt(s):
    return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)


def verify(root):
    root = Path(root)
    report = json.loads((root/"report.json").read_text())
    assert report["schema"] == "V99_I1_ORIGINAL_TARDIS_FREE_SUNDAY_TICKER_PILOT_V1"
    assert [d["day"] for d in report["days"]] == list(DAYS)
    assert report["max_possible_sample_asset_weeks"] == 4
    assert report["full_train_asset_weeks_required"] == 182
    for field in ("historical_fee_margin_certified", "holding_period_quotes_certified",
                  "historical_economic_train_executed", "validation_opened", "holdout_opened",
                  "orders_enabled", "promotion_authorized"):
        assert report[field] is False
    total = 0
    for day in report["days"]:
        midnight = dt(day["day"]+"T00:00:00Z")
        decision = midnight+timedelta(days=1)
        end_us = int(decision.timestamp()*1000000)
        cutoff = end_us-300000000
        assert day["decision_utc"] == decision.isoformat()
        assert [r["offset"] for r in day["original_receipts"]] == list(range(1435,1440))
        assert day["minutes_complete"] == 5
        previous = None
        latest = {}
        rows = tickers = 0
        for receipt in day["original_receipts"]:
            offset = receipt["offset"]
            assert receipt["file"] == f"{day['day']}_{offset}.ndjson.gz"
            raw = (root/receipt["file"]).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == receipt["sha256"]
            assert len(raw) == receipt["compressed_bytes"]
            start_us = int((midnight+timedelta(minutes=offset)).timestamp()*1000000)
            for line in gzip.decompress(raw).decode("utf-8").splitlines():
                if not line.strip():
                    continue
                arrival, sep, encoded = line.partition(" ")
                assert sep
                us = int(dt(arrival).timestamp()*1000000)
                assert start_us <= us < start_us+60000000
                assert previous is None or previous <= us
                previous = us
                rows += 1
                obj = json.loads(encoded)
                params = obj.get("params")
                if not isinstance(params,dict) or not str(params.get("channel","")).startswith("ticker."):
                    continue
                v = params.get("data")
                if not isinstance(v,dict):
                    continue
                tickers += 1
                sym = v.get("instrument_name")
                m = P.fullmatch(sym) if isinstance(sym,str) else None
                if not m:
                    continue
                try:
                    expiry = datetime.strptime(m[2],"%d%b%y").replace(hour=8,tzinfo=timezone.utc)
                    strike = Decimal(m[3])
                except ValueError:
                    continue
                if not (strike>0 and timedelta(days=21)<=expiry-decision<=timedelta(days=45)
                        and expiry<END):
                    continue
                try:
                    bid,ask,bs,az = (Decimal(str(v[k])) for k in
                                      ("best_bid_price","best_ask_price","best_bid_amount","best_ask_amount"))
                    ex_us = int(Decimal(str(v["timestamp"]))*1000)
                    valid = (all(x.is_finite() and x>0 for x in (bid,ask,bs,az))
                             and bid<ask and cutoff<=ex_us<=us<end_us)
                except (KeyError, ValueError, ArithmeticError):
                    valid = False
                    ex_us = -1
                latest[sym] = ({"asset":m[1], "symbol":sym,"expiry":expiry.isoformat(),
                    "strike":str(strike), "arrival_us":us,"exchange_us":ex_us,
                    "bid_coin":str(bid),"ask_coin":str(ask),
                    "bid_size_source_units":str(bs),"ask_size_source_units":str(az)}
                    if valid else None)
        books = sorted((b for b in latest.values() if b is not None),key=lambda b:b["symbol"])
        assert rows == day["raw_messages"] and tickers == day["ticker_messages"]
        assert books == day["last_eligible_books"]
        pairs = {}
        for asset in ("BTC","ETH"):
            exp = {}
            for b in books:
                if b["asset"]==asset:
                    exp.setdefault(b["expiry"],set()).add(b["strike"])
            pairs[asset] = any(len(strikes)>=2 for strikes in exp.values())
        assert pairs == day["two_strike_pairs"]
        total += sum(pairs.values())
    assert total == report["real_source_asset_weeks_with_two_strikes"]
    return total


if __name__ == "__main__":
    print(json.dumps({"independent_verified_sample_asset_weeks":verify(
        Path(sys.argv[1]) if len(sys.argv)>1 else "research_evidence/i1_free_sunday_ticker"),
        "economic_train":False,"promotion":False}))
