"""V98 native funding edge coverage: no silent zero-funding source truncation."""
import unittest
from research.v98_independent.v98_phase243_training_reader import (
    START_MS, END_MS, HOUR_MS, validate_funding_edges,
)


class FundingEdgeCoverage(unittest.TestCase):
    def test_valid_native_boundary_events(self):
        validate_funding_edges({t: 0.0001 for t in range(START_MS, END_MS, 8 * HOUR_MS)}, "BTCUSDT")

    def test_missing_interior_settlement_rejected(self):
        events = {t: 0.0001 for t in range(START_MS, END_MS, 8 * HOUR_MS)}
        del events[START_MS + 80 * HOUR_MS]
        with self.assertRaisesRegex(ValueError, "INTERIOR_COVERAGE"):
            validate_funding_edges(events, "BTCUSDT")

    def test_noncanonical_settlement_hour_rejected(self):
        events = {t: 0.0001 for t in range(START_MS, END_MS, 8 * HOUR_MS)}
        events[START_MS + HOUR_MS] = 0.0001
        with self.assertRaisesRegex(ValueError, "INTERIOR_COVERAGE"):
            validate_funding_edges(events, "ETHUSDT")

    def test_nine_hour_early_truncation_rejected(self):
        with self.assertRaisesRegex(ValueError, "EDGE_COVERAGE"):
            validate_funding_edges({START_MS + 9 * HOUR_MS: 0.0001,
                                    END_MS - 8 * HOUR_MS: -0.0001}, "BTCUSDT")

    def test_nine_hour_late_truncation_rejected(self):
        with self.assertRaisesRegex(ValueError, "EDGE_COVERAGE"):
            validate_funding_edges({START_MS + 8 * HOUR_MS: 0.0001,
                                    END_MS - 9 * HOUR_MS: -0.0001}, "ETHUSDT")

    def test_missing_early_events_rejected(self):
        with self.assertRaisesRegex(ValueError, "EDGE_COVERAGE"):
            validate_funding_edges({START_MS + 25 * HOUR_MS: 0.0001,
                                    END_MS - HOUR_MS: 0.0001}, "BTCUSDT")

    def test_missing_late_events_rejected(self):
        with self.assertRaisesRegex(ValueError, "EDGE_COVERAGE"):
            validate_funding_edges({START_MS: 0.0001,
                                    END_MS - 25 * HOUR_MS: 0.0001}, "ETHUSDT")

    def test_out_of_training_events_rejected(self):
        for events in ({START_MS - HOUR_MS: 0.1, END_MS - HOUR_MS: 0.1},
                       {START_MS: 0.1, END_MS: 0.1}):
            with self.assertRaisesRegex(ValueError, "OUT_OF_TRAINING"):
                validate_funding_edges(events, "SOLUSDT")

    def test_empty_rejected(self):
        with self.assertRaisesRegex(ValueError, "EMPTY_FUNDING"):
            validate_funding_edges({}, "BNBUSDT")


if __name__ == "__main__":
    unittest.main()
