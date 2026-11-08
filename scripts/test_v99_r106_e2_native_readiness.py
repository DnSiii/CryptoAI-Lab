#!/usr/bin/env python3
"""Adversarial readiness checks only; synthetic fixtures never represent economic evidence."""
import csv
import datetime as dt
import hashlib
import tempfile
from pathlib import Path
from v99_r106_e2_native_readiness import readiness

START = dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc)
def write(path, columns, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        bars, funding, fees, fills = (root / (n + ".csv") for n in ("bars", "funding", "fees", "fills"))
        bcols = ["timestamp","symbol","market_type","open","high","low","close","volume"]
        records = []
        for i in range(875):
            timestamp = (START + dt.timedelta(hours=i)).isoformat()
            for symbol in ("BTC", "ETH"):
                records.append(dict(timestamp=timestamp,symbol=symbol,market_type="perpetual",open="100",high="101",low="99",close="100",volume="1"))
        bsha = write(bars,bcols,records)
        t = START.isoformat()
        fcols = ["timestamp","symbol","funding_rate","source_id"]
        frows = [dict(timestamp=t,symbol=s,funding_rate="0.0001",source_id="fund-"+s) for s in ("BTC","ETH")]
        fee_cols = ["timestamp","symbol","fee_tier","fee_rate","source_id"]
        fee_rows = [dict(timestamp=t,symbol=s,fee_tier="tier1",fee_rate="0.001",source_id="fee-"+s) for s in ("BTC","ETH")]
        fill_cols = ["timestamp","symbol","price","quantity","fee","source_id"]
        fill_rows = [dict(timestamp=t,symbol=s,price="100",quantity="0.01",fee="0.01",source_id="fill-"+s) for s in ("BTC","ETH")]
        def check(fr=frows, fer=fee_rows, fir=fill_rows, expected=None, bars_digest=bsha):
            fh=write(funding,fcols,fr)
            feh=write(fees,fee_cols,fer)
            fih=write(fills,fill_cols,fir)
            try:
                result=readiness(bars,bars_digest,funding,fh,fees,feh,fills,fih)
                if expected: raise AssertionError("FAILED OPEN: "+expected)
                assert result["promotion"] is False
                assert result["five_fold_economics_run"] is False
                assert result["orders"] == 0
                assert result["historical_hypothetical_fills_exchange_certified"] is False
            except (ValueError, OverflowError):
                if not expected: raise
                print("EXPECTED REJECTION:",expected)
        check()
        check(expected="bad bar hash",bars_digest="0"*64)
        check(fr=[],expected="empty funding")
        check(fr=frows[:1],expected="ETH funding missing")
        check(fer=fee_rows[:1],expected="ETH fee tier missing")
        check(fir=fill_rows[:1],expected="ETH execution receipts missing")
        check(fir=[dict(fill_rows[0],fee="-0.01"),fill_rows[1]],expected="negative execution fee")
        check(fr=frows*2,expected="duplicate funding id")
        check(fr=[dict(frows[0],timestamp="2023-10-01T00:00:00+00:00")],expected="TRAIN boundary")
        check(fer=[dict(fee_rows[0],fee_rate="nan")],expected="nonfinite fee")
        check(fer=[dict(fee_rows[0],fee_rate="-0.1")],expected="negative fee rate")
        check(fir=[dict(fill_rows[0],quantity="0")],expected="zero fill quantity")
        check(fir=[dict(fill_rows[0],price="-1")],expected="negative fill price")
        print("E2 NATIVE READINESS ADVERSARIAL PASS; FIXTURES ONLY; NO ECONOMICS; NO PROMOTION")
if __name__ == "__main__":
    main()
