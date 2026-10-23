"""V98 Independent Phase991: deterministic source-only regression tests."""
import unittest
from phase991_source_triangulation import TIMES, inspect, diff, ALL_COLS

def candle(t):
    return [str(t), '100', '110', '90', '105', '0', str(t+3599999), '0', '0', '0', '0', '0']

class SourceOnlyTests(unittest.TestCase):
    def setUp(self):
        self.rows = [candle(t) for t in TIMES]

    def test_valid_month(self):
        report, mapped = inspect(self.rows, TIMES)
        self.assertEqual(report['fault_count'], 0)
        self.assertEqual(len(mapped), 672)

    def test_first_fault_timestamp(self):
        self.rows[149][2] = '99'
        report, _ = inspect(self.rows, TIMES)
        self.assertEqual(report['first_faults'][0]['index'], 149)
        self.assertEqual(report['first_faults'][0]['faults'], ['OHLC_GEOMETRY'])

    def test_numeric_and_full_row_provenance(self):
        _, original = inspect(self.rows, TIMES)
        changed = [r.copy() for r in self.rows]
        changed[10][7] = '1'
        _, observed = inspect(changed, TIMES)
        self.assertEqual(diff(original, observed)['different_rows'], 0)
        self.assertEqual(diff(original, observed, ALL_COLS)['different_rows'], 1)

if __name__ == '__main__':
    unittest.main()
