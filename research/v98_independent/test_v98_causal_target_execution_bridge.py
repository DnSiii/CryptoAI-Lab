import csv
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from research.v98_independent.v98_causal_target_execution_bridge import bridge
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS

class CausalBridgeTest(unittest.TestCase):
    def test_next_open_and_inventory_roll(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root=Path(d)/"v98_independent";root.mkdir()
            prices=root/"prices";prices.mkdir()
            start=datetime(2023,1,1,tzinfo=timezone.utc)
            hours=[int((start+timedelta(hours=i)).timestamp()*1000) for i in range(3)]
            for a in ASSETS:
                with (prices/f"{a}_1h.csv").open("w",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=["open_time","open","close"])
                    w.writeheader()
                    for i in range(3):
                        w.writerow({"open_time":(start+timedelta(hours=i)).isoformat(),
                                    "open":100,"close":110})
            targets=root/"targets.csv"
            with targets.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["asset","hour_open_ms","target_notional_usd"])
                w.writeheader()
                for t in hours:
                    for a in ASSETS:
                        w.writerow({"asset":a,"hour_open_ms":t,"target_notional_usd":50 if t==hours[0] else 70})
            out=root/"positions.csv"
            self.assertEqual(bridge(targets,prices,out),12)
            with out.open(newline="") as f:rows=list(csv.DictReader(f))
            x=[r for r in rows if r["asset"]==ASSETS[0]]
            self.assertEqual([float(r["target_notional_usd"]) for r in x],[0,50,70])
            self.assertEqual([float(r["pre_trade_notional_usd"]) for r in x],[0,0,50])
            # A previous close of 110 followed by a new open of 100 must not
            # fabricate 10% inventory value; units are conserved across the gap.
            self.assertEqual([int(r["decision_time_ms"]) for r in x],[h-HOUR_MS for h in hours])

    def test_future_price_row_rejected_before_execution(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root=Path(d)/"v98_independent";root.mkdir()
            prices=root/"prices";prices.mkdir()
            for a in ASSETS:
                (prices/f"{a}_1h.csv").write_text(
                    "open_time,open,close\n2026-01-01T00:00:00+00:00,100,101\n")
            targets=root/"targets.csv"
            targets.write_text("asset,hour_open_ms,target_notional_usd\n")
            with self.assertRaisesRegex(ValueError,"TRAINING_BOUNDARY"):
                bridge(targets,prices,root/"positions.csv")

    def test_nonfinite_price_rejected(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root=Path(d)/"v98_independent";root.mkdir()
            prices=root/"prices";prices.mkdir()
            for a in ASSETS:
                (prices/f"{a}_1h.csv").write_text(
                    "open_time,open,close\n2023-01-01T00:00:00+00:00,nan,101\n")
            targets=root/"targets.csv"
            targets.write_text("asset,hour_open_ms,target_notional_usd\n")
            with self.assertRaisesRegex(ValueError,"INVALID_PRICE"):
                bridge(targets,prices,root/"positions.csv")

if __name__=="__main__":unittest.main()
