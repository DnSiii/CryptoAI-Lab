"""Synthetic native OHLCV invariant tests; no paper, network, or holdout."""
import unittest
from datetime import datetime, timezone
from research.tools import v99_r106_native_volume_integrity as v

OBSERVED = "2026-10-14T20:18:12+00:00"
CLOSED = "2026-10-14T20:00:00+00:00"

def rows(multiplier="0.01"):
    data=[]
    for h in (20, 19, 18, 17):
        stamp = int(datetime(2026, 10, 14, h, tzinfo=timezone.utc).timestamp() * 1000)
        base = str(v.decimal("2") * v.decimal(multiplier))
        data.append([str(stamp), "100", "105", "95", "102", "2", base,
                     str(v.decimal(base) * 100), "0" if h == 20 else "1"])
    return data

class NativeVolume(unittest.TestCase):
    def test_native_multiplier_and_tminus1(self):
        for value in ("0.01", "0.1", "1", "100", "1000"):
            self.assertEqual(v.audit_rows(rows(value), value, OBSERVED, CLOSED), 3)
    def test_wrong_native_multiplier_fails(self):
        with self.assertRaisesRegex(ValueError, "contract-to-base"):
            v.audit_rows(rows("0.01"), "0.1", OBSERVED, CLOSED)
    def test_quote_turnover_outside_range_fails(self):
        r=rows();r[1][7]="999999"
        with self.assertRaisesRegex(ValueError, "turnover"):
            v.audit_rows(r, "0.01", OBSERVED, CLOSED)
    def test_unconfirmed_old_candle_fails(self):
        r=rows();r[1][8]="0"
        with self.assertRaisesRegex(ValueError, "confirmed"):
            v.audit_rows(r, "0.01", OBSERVED, CLOSED)
    def test_reordered_source_fails(self):
        r=rows();r[1],r[2]=r[2],r[1]
        with self.assertRaisesRegex(ValueError, "reordered"):
            v.audit_rows(r, "0.01", OBSERVED, CLOSED)
    def test_future_candle_fails(self):
        r=rows();r[0][0]=str(int(datetime(2026,10,14,21,tzinfo=timezone.utc).timestamp()*1000))
        with self.assertRaisesRegex(ValueError, "future"):
            v.audit_rows(r, "0.01", OBSERVED, CLOSED)
    def test_nonfinite_rejected(self):
        r=rows();r[1][6]="NaN"
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            v.audit_rows(r, "0.01", OBSERVED, CLOSED)

if __name__ == "__main__": unittest.main()
