"""Independent delivery API pagination drift regression controls (no network)."""
import copy
import unittest
from datetime import date, timedelta
from research.tests.test_v99_r106_i1_original_delivery_to_spine import make_delivery
from research.verification.independent_v99_r106_i1_delivery_price_oracle import verify_archive

FIRST = date(2021, 12, 9)
END = date(2023, 10, 1)


def live_pages(*, shift_days=5, change_train=False):
    data = {}
    for index, price in (("btc_usd", 42000.0), ("eth_usd", 3000.0)):
        records = [
            {"date": (END + timedelta(days=i)).isoformat(),
             "delivery_price": price+1}
            for i in range(shift_days)
        ]
        records += [
            {"date": (FIRST + timedelta(days=i)).isoformat(),
             "delivery_price": price + (1 if change_train and i == 20 else 0)}
            for i in range((END-FIRST).days)
        ]
        records.append({"date": (FIRST-timedelta(days=1)).isoformat(),
                        "delivery_price": price})
        data[index] = sorted(records, key=lambda r:r["date"], reverse=True)

    def fetch(index, offset):
        rows = data[index][offset:offset+100]
        return {"data": rows, "records_total": len(data[index])}
    return fetch


class IndependentDeliveryDateKeyOracleTests(unittest.TestCase):
    def test_live_offset_page_drift_does_not_falsely_reject_same_train(self):
        original = make_delivery()
        result = verify_archive(original, live_pages(shift_days=5))
        self.assertEqual(result["assets"]["btc_usd"]["original_train_dates_verified"], 661)
        self.assertEqual(result["assets"]["eth_usd"]["original_train_dates_verified"], 661)
        self.assertFalse(result["economic_train_run"])

    def test_actual_train_price_change_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "ORIGINAL_TRAIN_DATE_PRICE_CHANGED"):
            verify_archive(make_delivery(), live_pages(shift_days=5, change_train=True))

    def test_missing_historical_date_fails_closed(self):
        original = make_delivery()
        original["assets"]["btc_usd"]["records"].pop(10)
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_ARCHIVED_FIRSTPARTY_TRAIN"):
            verify_archive(original, live_pages())

    def test_archived_source_claim_and_page_hash_required(self):
        original = make_delivery()
        original["assets"]["btc_usd"]["pages"][0]["sha256_canonical_data_rows"] = "BAD"
        with self.assertRaisesRegex(ValueError, "MALFORMED_ARCHIVED_ACQUISITION_PAGE"):
            verify_archive(original, live_pages())
        original = make_delivery()
        original["no_promotion"] = False
        with self.assertRaisesRegex(ValueError, "UNTRUSTED_ARCHIVED_FIRSTPARTY"):
            verify_archive(original, live_pages())


if __name__ == "__main__":
    unittest.main()
