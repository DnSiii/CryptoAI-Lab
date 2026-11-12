import unittest
from research.v98_independent.v98_b0_independent_arithmetic_audit import reconcile, ASSETS
from research.v98_independent.v98_b0_ledger_diagnostics import diagnose

def entry(i, equity=10000., gross=0., funding=0., cost=0.):
    w = {a: 0. for a in ASSETS}
    return dict(index=i, equity=equity*(1-cost), pre_fill_equity=equity,
                weights_before_fill=w, weights_after_fill=w,
                gross_return=gross, funding_return=funding,
                turnover=0., cost_return=cost, drawdown=0.)

class ArithmeticAuditTests(unittest.TestCase):
    def test_reconciles_identity_and_final_mark(self):
        e = [entry(1, 10000., cost=.01), entry(2, 9900.)]
        r = reconcile(e, dict(hours=3, final_equity=10000.))
        self.assertEqual(r["observations"], 2)
        self.assertAlmostEqual(r["final_mark_return"], 10000./9900.-1)

    def test_detects_fabricated_pre_fill_equity(self):
        e = [entry(1, 10000.)]
        e[0]["pre_fill_equity"] = 11000.
        with self.assertRaisesRegex(ValueError, "LEDGER_RECONCILIATION_FAILED"):
            reconcile(e, dict(hours=2, final_equity=10000.))

    def test_detects_wrong_turnover_and_nonfinite(self):
        e = [entry(1)]
        e[0]["turnover"] = 1.
        with self.assertRaisesRegex(ValueError, "LEDGER_RECONCILIATION_FAILED"):
            reconcile(e, dict(hours=2, final_equity=10000.))
        e[0]["turnover"] = float("nan")
        with self.assertRaisesRegex(ValueError, "NONFINITE_LEDGER"):
            reconcile(e, dict(hours=2, final_equity=10000.))

    def test_detects_wrong_length(self):
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_LEDGER"):
            reconcile([entry(1)], dict(hours=4, final_equity=10000.))

class CalendarDiagnosticsTests(unittest.TestCase):
    def test_utc_midnight_is_new_day_not_previous_day(self):
        rows = [entry(i) for i in range(1, 26)]
        rows[22]["equity"] = 10100.  # Dec 1, 23:00 UTC
        rows[23]["equity"] = 10200.  # Dec 2, 00:00 UTC
        rows[24]["equity"] = 10300.  # Dec 2, 01:00 UTC
        result = diagnose(rows, final_equity=10300.)
        self.assertEqual(result["observed_days"], 2)
        self.assertEqual(result["positive_days"], 2)
        self.assertAlmostEqual(result["daily_return_max"], 10300./10100.-1)
        self.assertIn("2022", result["utc_year_returns_including_warmup"])

    def test_final_close_mark_is_in_last_utc_day(self):
        rows = [entry(i) for i in range(1, 25)]
        result = diagnose(rows, final_equity=9900.)
        self.assertEqual(result["observed_days"], 2)
        self.assertAlmostEqual(result["utc_year_returns_including_warmup"]["2022"], -.01)

if __name__ == "__main__":
    unittest.main()
