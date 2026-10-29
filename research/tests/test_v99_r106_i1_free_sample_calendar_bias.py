"""Independent calendar arithmetic; no market data, fees, fills or PnL."""
import calendar
import unittest
from datetime import datetime, timedelta, timezone

from research.tools.v99_r106_i1_free_sample_calendar_bias import (
    SCHEMA, audit, last_friday, monthlies, monthly_tenor,
)
from research.tools.v99_r106_i1_full_archive_intake import eligible


def independent_month_end_friday(y, m):
    # Independent construction: last Friday in monthcalendar(), not backward
    # arithmetic from the final calendar day used in production.
    fridays = [week[calendar.FRIDAY] for week in calendar.monthcalendar(y, m)
               if week[calendar.FRIDAY] != 0]
    return datetime(y, m, fridays[-1], 8, tzinfo=timezone.utc)


class CalendarBiasTests(unittest.TestCase):
    def test_independent_last_friday_for_all_months(self):
        for y in range(2021, 2025):
            for m in range(1, 13):
                self.assertEqual(last_friday(y, m), independent_month_end_friday(y, m))

    def test_original_free_sample_mondays_are_both_25_and_one_third_days(self):
        expiries = monthlies()
        for y, m, d in ((2022, 5, 2), (2023, 1, 2)):
            r = monthly_tenor(datetime(y, m, d, tzinfo=timezone.utc), expiries)
            self.assertAlmostEqual(r["next_monthly_days"], 25 + 8/24)
            self.assertFalse(r["monthly_tenor_calendar_possible"])
            self.assertEqual(r["monthly_tenor_days"], [])

    def test_positive_calendar_controls(self):
        expiries = monthlies()
        for y, m, d in ((2022, 4, 25), (2023, 1, 23)):
            r = monthly_tenor(datetime(y, m, d, tzinfo=timezone.utc), expiries)
            self.assertTrue(r["monthly_tenor_calendar_possible"])
            self.assertAlmostEqual(r["monthly_tenor_days"][0], 32 + 8/24)

    def test_no_shifted_or_weekend_decisions(self):
        for when in ((2022, 5, 2, 1), (2022, 5, 1, 0), (2022, 5, 2, 12)):
            with self.assertRaises(ValueError):
                monthly_tenor(datetime(*when, tzinfo=timezone.utc), monthlies())

    def test_independent_full_grid_reconstruction(self):
        start = datetime(2021, 12, 9, tzinfo=timezone.utc)
        end = datetime(2023, 10, 1, tzinfo=timezone.utc)
        first = start + timedelta(days=4)  # first Monday: Dec 13
        independently = [first + timedelta(days=7*i) for i in range(94)]
        independently = [d for d in independently if d + timedelta(days=28) < end]
        self.assertEqual(independently, eligible(True))
        self.assertEqual(len(independently), 90)
        count = 0
        for monday in independently:
            possible = any(28 <= (independent_month_end_friday(y, m)-monday).total_seconds()/86400 <= 35
                           for y in range(2021, 2025) for m in range(1, 13))
            count += int(possible)
        self.assertEqual(count, 21)

    def test_fail_closed_source_only_result(self):
        r = audit()
        self.assertEqual(r["schema"], SCHEMA)
        self.assertEqual(r["fixed_monday_decisions"], 90)
        self.assertEqual(r["monthly_tenor_calendar_possible_mondays"], 21)
        self.assertEqual(r["monthly_tenor_calendar_impossible_mondays"], 69)
        self.assertTrue(r["both_negative_samples_calendar_ineligible"])
        self.assertEqual(len(r["samples"]), 2)
        self.assertEqual(r["historical_option_lifecycles_certified"], 0)
        for field in ("historical_listings_authenticated",
                      "historical_executable_books_authenticated",
                      "economic_train_executed", "roi_calculated",
                      "strategy_rules_modified", "validation_opened",
                      "holdout_opened", "orders_enabled", "promotion_authorized"):
            self.assertIs(r[field], False, field)


if __name__ == "__main__":
    unittest.main()
