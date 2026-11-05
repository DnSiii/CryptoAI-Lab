#!/usr/bin/env python3
"""Synthetic-only D1 causality regression. NOT economic evidence."""
import csv
import datetime as dt
import importlib.util
import tempfile
from pathlib import Path

MODULE = Path(__file__).with_name("v99_r106_d1_train_only.py")
spec = importlib.util.spec_from_file_location("d1", MODULE)
d1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d1)

def write_csv(path, n=181, last_price=100.0):
    fields = d1.FIELDS
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for i in range(n):
            price = last_price if i == n-1 else 100.0
            w.writerow(dict(date=(dt.date(2022,1,1)+dt.timedelta(days=i)).isoformat(),
                btc_close=price, atm_iv=0.5, relative_spread=0.001,
                straddle_hedged_net_return=0.01,
                execution_verified="true", funding_verified="true",
                source_receipt_sha256="a"*64, execution_receipt_sha256="b"*64,
                funding_receipt_sha256="c"*64))

def main():
    with tempfile.TemporaryDirectory() as temp:
        p = Path(temp)/"synthetic.csv"
        write_csv(p, 181, 100)
        baseline = d1.evaluate(p)
        assert baseline["traded_days"] == 150, baseline
        assert len(baseline["fold_returns"]) == 5
        assert baseline["promotion"] is False
        # A future last-row close must not change the FIRST signal.
        # With the old i=30 start, rows[-1] contaminated the initial 30-return window.
        write_csv(p, 181, 1000000)
        changed = d1.evaluate(p)
        assert changed["traded_days"] == baseline["traded_days"], (baseline, changed)
        # No observation at or beyond sealed validation may enter TRAIN.
        write_csv(p, 180, 100)
        try:
            d1.evaluate(p)
        except ValueError as exc:
            assert "insufficient TRAIN" in str(exc)
        else:
            raise AssertionError("short TRAIN was accepted")
    print("D1 synthetic causality regression PASS; NOT economic validation")

if __name__ == "__main__":
    main()
