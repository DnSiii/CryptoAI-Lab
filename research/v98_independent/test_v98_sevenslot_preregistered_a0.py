"""Deterministic causality and seven-slot schema checks for preregistered A0."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research.v98_independent.phase243_native_funding_cashflow import ASSETS
from research.v98_independent.v98_sevenslot_preregistered_a0 import generate

class TestA0(unittest.TestCase):
    def test_causality_schema_and_warmup(self):
        n=200
        bars={a:[(100+i*.1,101+i*.1,99+i*.1,100+i*.1,1.) for i in range(n)] for a in ASSETS}
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as tmp:
            path=Path(tmp)/"v98_independent"/"a0.csv"
            with patch("research.v98_independent.v98_sevenslot_preregistered_a0.load",
                       return_value={"bars":bars,"hours":n,"funding":{}}):
                result=generate(None,None,None,path)
            self.assertEqual(result["rows"],n*len(ASSETS))
            with path.open(newline="") as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),n*len(ASSETS))
            self.assertTrue(all(float(row["growth_core"])==0 for row in rows[:168*len(ASSETS)]))
            self.assertTrue(any(float(row["growth_core"])>0 for row in rows[168*len(ASSETS):]))
            # Mutating the future cannot change past decisions.
            for a in ASSETS:
                for i in range(190,n):
                    bars[a][i]=(10000.,10001.,9999.,10000.,1.)
            with patch("research.v98_independent.v98_sevenslot_preregistered_a0.load",
                       return_value={"bars":bars,"hours":n,"funding":{}}):
                generate(None,None,None,path)
            with path.open(newline="") as f:
                altered=list(csv.DictReader(f))
            self.assertEqual(rows[:190*len(ASSETS)],altered[:190*len(ASSETS)])

if __name__=="__main__":
    unittest.main()
