"""Adversarial synthetic tests for the read-only legacy journal conservation audit."""
import copy
import datetime
import unittest
from research.tools import v99_r106_legacy_self_financing_audit as audit


def sample():
    start = datetime.datetime(2022, 1, 3, tzinfo=datetime.timezone.utc)
    rows = []
    for i in range(3):
        rows.append({
            "time": (start + datetime.timedelta(hours=i)).isoformat(),
            "btc_weight": "0.5", "eth_weight": "0.25",
            "turnover": "0.75" if i == 0 else "0.0",
            "fee": "0.000525" if i == 0 else "0.0",
        })
    rows[-1]["next_prices"] = (130., 40.)
    opens = [(100., 50.), (110., 45.), (120., 40.)]
    return rows, opens


class SelfFinancingAudit(unittest.TestCase):
    def test_quantity_rebalance_even_when_legacy_turnover_zero(self):
        rows, opens = sample()
        trace = audit.replay_targets(rows, opens, .0007)
        self.assertEqual(len(trace), 3)
        self.assertTrue(audit.verify_trace(trace, .0007))
        self.assertGreater(trace[1]["notional_turn"], 0.)
        self.assertEqual(trace[1]["legacy_turn"], 0.)
        self.assertGreater(trace[1]["fee"], 0.)

    def test_conservation_after_price_and_target_change(self):
        rows, opens = sample()
        rows[1]["btc_weight"] = "-0.2"
        rows[2]["eth_weight"] = "0.0"
        trace = audit.replay_targets(rows, opens, .0014)
        self.assertTrue(audit.verify_trace(trace, .0014))
        for row in trace:
            self.assertGreater(row["nav_post_fee"], 0.)
            self.assertGreater(row["nav_next"], 0.)

    def test_independent_oracle_catches_fee_tamper(self):
        rows, opens = sample()
        trace = audit.replay_targets(rows, opens, .0007)
        bad = copy.deepcopy(trace)
        bad[1]["fee"] *= .5
        with self.assertRaisesRegex(ValueError, "self_financing_mismatch_fee"):
            audit.verify_trace(bad, .0007)

    def test_independent_oracle_catches_contract_tamper(self):
        rows, opens = sample()
        trace = audit.replay_targets(rows, opens, .0007)
        bad = copy.deepcopy(trace)
        q = list(bad[1]["q_new"])
        q[0] *= 1.1
        bad[1]["q_new"] = tuple(q)
        with self.assertRaises(ValueError):
            audit.verify_trace(bad, .0007)

    def test_independent_oracle_catches_price_tamper(self):
        rows, opens = sample()
        trace = audit.replay_targets(rows, opens, .0007)
        bad = copy.deepcopy(trace)
        bad[1]["prices"] = (111., 45.)
        with self.assertRaises(ValueError):
            audit.verify_trace(bad, .0007)

    def test_incomplete_or_invalid_source_rejected(self):
        rows, opens = sample()
        with self.assertRaisesRegex(ValueError, "target_price_coverage"):
            audit.replay_targets(rows[:-1], opens, .0007)
        with self.assertRaisesRegex(ValueError, "invalid_market_price"):
            audit.replay_targets(rows, [(0., 50.), *opens[1:]], .0007)

    def test_insufficient_equity_and_bad_gross_rejected(self):
        with self.assertRaisesRegex(ValueError, "insufficient_equity"):
            audit.fee_solution(1., (1e9, 0.), (100., 50.), (.5, .2), .0007)
        with self.assertRaisesRegex(ValueError, "invalid_self_financing_input"):
            audit.fee_solution(1., (0., 0.), (100., 50.), (1., 1.), .0007)

    def test_original_weight_delta_fee_understates_drift_rebalancing(self):
        rows, opens = sample()
        trace = audit.replay_targets(rows, opens, .0007)
        legacy = sum(x["legacy_turn"] for x in trace)
        quantity = sum(x["notional_turn"] / x["nav_pre"] for x in trace)
        self.assertGreater(quantity, legacy)
        self.assertGreater(sum(x["fee"] for x in trace), 0.)

    def test_cannot_fabricate_final_hour_open(self):
        rows, opens = sample()
        del rows[-1]["next_prices"]
        with self.assertRaises(KeyError):
            audit.replay_targets(rows, opens, .0007)


if __name__ == "__main__":
    unittest.main()
