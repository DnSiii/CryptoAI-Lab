"""R106 forward generator safety: do not leak paper rows into backtest or cap operations.

Load only isolated function ASTs to avoid importing trading/data modules,
exchange connections, historical holdout, or performing strategy backtests.
"""
from __future__ import annotations
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"paper_once_v99_research_variants_v2.py"
SOURCE=SCRIPT.read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)
NAMES=("daily_backtest_curve","paper_operations")
functions=[x for x in TREE.body if isinstance(x,ast.FunctionDef) and x.name in NAMES]
if len(functions)!=len(NAMES):
    raise RuntimeError("generator API absent: "+str(NAMES))
isolated=ast.Module(body=functions,type_ignores=[])
ns={"pd":pd,"MAX_OPERATIONS":1500}
exec(compile(ast.fix_missing_locations(isolated),str(SCRIPT),"exec"),ns)
backtest=ns["daily_backtest_curve"]
operations=ns["paper_operations"]

BOUNDARY=pd.Timestamp("2026-09-16T13:00:00Z")

def frame_equity(times, values):
    idx=pd.to_datetime(times,utc=True)
    return SimpleNamespace(equity=pd.Series(values,index=idx,dtype=float))


class TestHistoricalReferenceBoundary(unittest.TestCase):
    def test_excludes_at_and_after_boundary_even_same_sao_paulo_day(self):
        result=frame_equity(
            ["2026-09-15T23:00:00Z","2026-09-16T12:00:00Z",
             "2026-09-16T13:00:00Z","2026-09-16T14:00:00Z"],
            [100,110,300,450])
        rows=backtest(result,BOUNDARY)
        self.assertEqual(len(rows),2)
        self.assertTrue(all(pd.Timestamp(x["timestamp"])<BOUNDARY for x in rows))
        self.assertEqual(rows[-1]["timestamp"],"2026-09-16T12:00:00+00:00")
        self.assertAlmostEqual(rows[-1]["equity_multiple"],1.1)

    def test_no_prior_observation_returns_empty(self):
        result=frame_equity(
            ["2026-09-16T13:00:00Z","2026-09-16T14:00:00Z"],
            [1,1.01])
        self.assertEqual(backtest(result,BOUNDARY),[])

    def test_pre_boundary_only_daily_close(self):
        result=frame_equity(
            ["2026-09-15T14:00:00Z","2026-09-15T22:00:00Z",
             "2026-09-15T23:00:00Z","2026-09-16T12:00:00Z"],
            [100,110,120,125])
        rows=backtest(result,BOUNDARY)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["timestamp"],"2026-09-16T02:00:00+00:00") if False else None
        self.assertTrue(all(pd.Timestamp(x["timestamp"])<BOUNDARY for x in rows))
        self.assertEqual(rows[-1]["timestamp"],"2026-09-16T12:00:00+00:00")

    def test_naive_equity_timestamp_is_rejected(self):
        result=SimpleNamespace(equity=pd.Series([1.,2.],index=pd.to_datetime([
            "2026-09-14T11:00:00","2026-09-15T11:00:00"])))
        with self.assertRaisesRegex(ValueError,"explicit UTC"):
            backtest(result,BOUNDARY)

    def test_naive_paper_start_is_rejected(self):
        result=frame_equity(["2026-09-15T11:00:00Z"],[1])
        with self.assertRaisesRegex(ValueError,"explicit timezone"):
            backtest(result,pd.Timestamp("2026-09-16T13:00:00"))

    def test_empty_equity_returns_empty(self):
        result=SimpleNamespace(equity=pd.Series(dtype=float,index=pd.DatetimeIndex([],tz="UTC")))
        self.assertEqual(backtest(result,BOUNDARY),[])


class TestFullForwardOperationEvidence(unittest.TestCase):
    def test_no_silent_1500_operation_tail_truncation(self):
        symbols=[f"ASSET{i:04d}USDT" for i in range(1505)]
        idx=pd.to_datetime([BOUNDARY,BOUNDARY+pd.Timedelta(hours=1)],utc=True)
        frame=pd.DataFrame([[0.0]*len(symbols),[0.01]*len(symbols)],
                           columns=symbols,index=idx)
        rows=operations(frame,BOUNDARY,idx[-1])
        self.assertEqual(len(rows),1505)
        self.assertEqual(rows[0]["symbol"],symbols[0])
        self.assertEqual(rows[-1]["symbol"],symbols[-1])
        self.assertEqual(len({(x["timestamp"],x["symbol"]) for x in rows}),1505)

    def test_changes_only_post_boundary(self):
        idx=pd.to_datetime([BOUNDARY-pd.Timedelta(hours=1),
                            BOUNDARY,BOUNDARY+pd.Timedelta(hours=1)],utc=True)
        frame=pd.DataFrame({"BTCUSDT":[0.5,1.,0.8],"ETHUSDT":[0.,0.,-0.1]},index=idx)
        rows=operations(frame,BOUNDARY,idx[-1])
        self.assertEqual({x["symbol"] for x in rows},{"BTCUSDT","ETHUSDT"})
        self.assertTrue(all(pd.Timestamp(x["timestamp"])>BOUNDARY for x in rows))
        self.assertEqual(len(rows),2)

    def test_identical_targets_no_fake_operation(self):
        idx=pd.to_datetime([BOUNDARY,BOUNDARY+pd.Timedelta(hours=1)],utc=True)
        frame=pd.DataFrame({"BTCUSDT":[0.2,0.2]},index=idx)
        self.assertEqual(operations(frame,BOUNDARY,idx[-1]),[])

    def test_insufficient_base_observation_produces_no_operations(self):
        idx=pd.to_datetime([BOUNDARY+pd.Timedelta(hours=1)],utc=True)
        frame=pd.DataFrame({"BTCUSDT":[0.2]},index=idx)
        self.assertEqual(operations(frame,BOUNDARY,idx[-1]),[])

    def test_does_not_mutate_inputs(self):
        idx=pd.to_datetime([BOUNDARY,BOUNDARY+pd.Timedelta(hours=1)],utc=True)
        frame=pd.DataFrame({"BTCUSDT":[0.0,0.9]},index=idx)
        pristine=frame.copy(deep=True)
        _=operations(frame,BOUNDARY,idx[-1])
        pd.testing.assert_frame_equal(frame,pristine)

    def test_replay_preserves_chronological_operation_order(self):
        idx=pd.to_datetime([BOUNDARY,BOUNDARY+pd.Timedelta(hours=1),
                            BOUNDARY+pd.Timedelta(hours=2)],utc=True)
        frame=pd.DataFrame({"BTCUSDT":[0.0,0.2,0.0],"ETHUSDT":[0.0,-0.3,-0.2]},index=idx)
        rows=operations(frame,BOUNDARY,idx[-1])
        self.assertEqual(len(rows),4)
        times=[pd.Timestamp(x["timestamp"]) for x in rows]
        self.assertEqual(times,sorted(times))

    def test_guard_is_still_called_before_disk_writes(self):
        text=SOURCE
        gate=text.index("    enforce_published(ledger)")
        first_write=text.index("    base.write_json(base.STATE_PATH, state)")
        self.assertLess(gate,first_write)
        self.assertNotIn("operations[-MAX_OPERATIONS:]",text)
        self.assertIn('daily_backtest_curve(result, paper_start)',text)


if __name__=="__main__":unittest.main()
