#!/usr/bin/env python3
"""A3 causal prefix-invariance regression: future prices cannot rewrite earlier orders."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research.v98_independent import v98_sevenslot_preregistered_a3 as a3

class A3PrefixInvariance(unittest.TestCase):
    def test_future_price_shock_cannot_rewrite_prior_decisions(self):
        assets = tuple(a3.ASSETS)
        n, boundary = 900, 800
        def market(shock):
            bars = {}
            for k, asset in enumerate(assets):
                rows = []
                for i in range(n):
                    price = (100 + k * 20) * (1 + 0.0003 * i)
                    if shock and i >= boundary:
                        price *= 1.7 if k % 2 else 0.45
                    rows.append((0, 0, 0, price))
                bars[asset] = rows
            return {"hours": n, "bars": bars}
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as tmp:
            root = Path(tmp) / "v98_independent"
            root.mkdir()
            outputs = []
            for shock in (False, True):
                target = root / ("shocked.csv" if shock else "baseline.csv")
                with patch.object(a3, "load", return_value=market(shock)):
                    a3.generate(root, root, root, target)
                with target.open(newline="") as f:
                    outputs.append(list(csv.DictReader(f)))
            self.assertEqual(len(outputs[0]), n * len(assets))
            self.assertEqual(len(outputs[1]), n * len(assets))
            for old, new in zip(*outputs):
                self.assertEqual(old["hour_open_ms"], new["hour_open_ms"])
                if int(old["hour_open_ms"]) < a3.START_MS + boundary * a3.HOUR_MS:
                    self.assertEqual(old, new, "Future shock changed past decision")

if __name__ == "__main__":
    unittest.main()
