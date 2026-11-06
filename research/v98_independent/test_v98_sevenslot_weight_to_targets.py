import csv
import tempfile
import unittest
from pathlib import Path
from research.v98_independent.v98_sevenslot_weight_to_targets import convert,FIELDS
from research.v98_independent.phase243_native_funding_cashflow import ASSETS,HOUR_MS

class SevenSlotTransportTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="v98_independent_")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"v98_independent"
        self.root.mkdir()
        self.source=self.root/"slots.csv"
        self.dest=self.root/"targets.csv"
        self.start=1672531200000

    def write(self,mutate=None):
        with self.source.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=FIELDS)
            w.writeheader()
            for i in range(3):
                for a in ASSETS:
                    r=dict(asset=a,hour_open_ms=self.start+i*HOUR_MS,
                           growth_core=".1",opportunity=".05",relative_value="-.02",
                           stress_recovery=".02",regime_router="1",
                           dynamic_allocator="1",risk_governor=".25")
                    if mutate:mutate(r,i,a)
                    w.writerow(r)

    def test_all_seven_slots_and_fixed_capital(self):
        self.write()
        self.assertEqual(convert(self.source,self.dest,fixed_capital_usd=10000),12)
        with self.dest.open(newline="") as f: rows=list(csv.DictReader(f))
        self.assertEqual([float(x["target_notional_usd"]) for x in rows],[1500.]*12)

    def test_governor_rejects_exposure(self):
        self.write(lambda r,i,a:r.update(risk_governor=".1") if i==1 and a==ASSETS[0] else None)
        with self.assertRaisesRegex(ValueError,"RISK_GOVERNOR_BREACH"):
            convert(self.source,self.dest,fixed_capital_usd=10000)

    def test_grid_rejects_duplicates(self):
        self.write()
        with self.source.open("a") as f:
            f.write(f"{ASSETS[0]},{self.start},.1,.05,-.02,.02,1,1,.25\n")
        with self.assertRaisesRegex(ValueError,"DUPLICATE_ASSET_HOUR"):
            convert(self.source,self.dest,fixed_capital_usd=10000)

    def test_no_future_hours(self):
        self.write(lambda r,i,a:r.update(hour_open_ms=1767225600000+i*HOUR_MS))
        with self.assertRaisesRegex(ValueError,"INVALID_ASSET_OR_TRAINING_HOUR"):
            convert(self.source,self.dest,fixed_capital_usd=10000)

if __name__=="__main__":unittest.main()
