"""Synthetic invariance and fail-closed checks; not market validation."""
import unittest
from research.v98_independent.v98_c27_variable_horizon_kernel import continue_replay
from research.v98_independent.v98_composed_c26 import WARMUP
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")

def fixture():
    start=WARMUP+2
    state=dict(equity=10000.,peak=10000.,decision_equity=10000.,
               decision_peak=10000.,absolute_index=start,
               weights={a:0. for a in ASSETS},
               queued={a:0. for a in ASSETS},
               histories={a:[100.]*start for a in ASSETS},
               previous_open={a:100. for a in ASSETS})
    bars={a:[(100.,102.,99.,101.,1.),(101.,103.,100.,102.,1.),
             (102.,104.,101.,103.,1.),(103.,105.,102.,104.,1.)] for a in ASSETS}
    funding={a:{} for a in ASSETS}
    return state,bars,funding

class ContinuationTests(unittest.TestCase):
    def test_flat_book_remains_flat(self):
        s,b,f=fixture()
        out=continue_replay(b,f,1.,s)
        self.assertEqual(out["hours"],4)
        self.assertEqual(out["final_equity"],10000.)
        self.assertEqual(len(out["ledger"]),4)
        self.assertEqual(out["carry_out"]["absolute_index"],s["absolute_index"]+4)

    def test_split_horizon_equals_unsplit_without_strategic_order(self):
        s,b,f=fixture()
        full=continue_replay(b,f,1.,s)
        first=continue_replay({a:b[a][:2] for a in ASSETS},f,1.,s)
        second=continue_replay({a:b[a][2:] for a in ASSETS},f,1.,first["carry_out"])
        self.assertEqual(full["final_equity"],second["final_equity"])
        self.assertEqual(full["carry_out"]["weights"],second["carry_out"]["weights"])

    def test_rejects_bad_state_and_missing_asset(self):
        s,b,f=fixture()
        s["peak"]=9999.
        with self.assertRaisesRegex(ValueError,"PEAK"):
            continue_replay(b,f,1.,s)
        s,b,f=fixture()
        del b["SOLUSDT"]
        with self.assertRaisesRegex(ValueError,"ASSETS"):
            continue_replay(b,f,1.,s)

if __name__=="__main__":
    unittest.main()
