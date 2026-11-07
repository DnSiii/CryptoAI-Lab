import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research.v98_independent.v98_seven_slot_economic_replay import replay

class ReplayTest(unittest.TestCase):
    def test_three_scenarios_share_identical_positions(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root=Path(d)/"v98_independent"
            root.mkdir()
            slots=root/"slots.csv"
            slots.write_text("frozen slots")
            out=root/"out"
            def fake_convert(source,dest,**kw):
                dest.write_text("targets")
                return 4
            def fake_bridge(source,prices,dest):
                dest.write_text("positions")
                return 4
            def fake_run(positions,funding,output,**kw):
                import hashlib
                return {"positions_sha256":hashlib.sha256(positions.read_bytes()).hexdigest(),
                        "cost_multiplier":kw["cost_multiplier"]}
            with patch("research.v98_independent.v98_seven_slot_economic_replay.convert",side_effect=fake_convert), \
                 patch("research.v98_independent.v98_seven_slot_economic_replay.bridge",side_effect=fake_bridge), \
                 patch("research.v98_independent.v98_seven_slot_economic_replay.run",side_effect=fake_run):
                result=replay(slots,root,root/"prices.json",root,out,1000,5,2)
            self.assertEqual([result["receipts"][k]["cost_multiplier"] for k in
                ("baseline","severe","supersevere")],[1,2,4])
            self.assertTrue((out/"scenario_summary.json").exists())

    def test_invalid_cost_scenarios_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root=Path(d)/"v98_independent"
            root.mkdir()
            with self.assertRaisesRegex(ValueError,"INVALID_COST_SCENARIOS"):
                replay(root,root,root,root,root,1000,5,2,multipliers=(1,4,2))

    def test_cost_stress_cannot_masquerade_as_severe(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root=Path(d)/"v98_independent"
            root.mkdir()
            for multipliers in ((1,1,4),(1,2,2),(0.5,2,4),(2,3,4),(1,0.9,4)):
                with self.subTest(multipliers=multipliers):
                    with self.assertRaisesRegex(ValueError,"INVALID_COST_SCENARIOS"):
                        replay(root,root,root,root,root,1000,5,2,multipliers=multipliers)

    def test_nonfinite_multiplier_rejected(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root=Path(d)/"v98_independent"
            root.mkdir()
            for bad in (float("nan"),float("inf")):
                with self.assertRaisesRegex(ValueError,"INVALID_COST_SCENARIOS"):
                    replay(root,root,root,root,root,1000,5,2,multipliers=(1,2,bad))

    def test_invalid_economic_inputs_rejected_before_io(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root=Path(d)/"v98_independent"
            root.mkdir()
            cases=((0,5,2,1,2),(1000,-1,2,1,2),(1000,5,-1,1,2),
                   (1000,5,2,2,1),(float("nan"),5,2,1,2))
            for capital,fee,slip,gross,leverage in cases:
                with self.assertRaisesRegex(ValueError,"INVALID_ECONOMIC_INPUTS"):
                    replay(root,root,root,root,root,capital,fee,slip,gross,leverage)

if __name__=="__main__":
    unittest.main()
