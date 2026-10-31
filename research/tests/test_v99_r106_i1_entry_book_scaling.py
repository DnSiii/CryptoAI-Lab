"""Source-only entry-book scaling regression; no native economics or orders."""
import hashlib
import random
import tempfile
import unittest
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import synchronized_strikes
from research.verification.independent_v99_r106_i1_full_archive_intake import independent_atomic
from research.verification.independent_v99_r106_i1_entry_book_export import independent_stream_digest


class EntryBookScalingTests(unittest.TestCase):
    @staticmethod
    def brute(rows):
        return any(
            a[0] != b[0]
            and abs(a[1] - b[1]) <= 1_000_000
            and abs(a[2] - b[2]) <= 1_000_000
            for i, a in enumerate(rows) for b in rows[i + 1:]
        )

    def test_two_independent_matchers_against_bruteforce(self):
        rng = random.Random(20261031)
        for _ in range(600):
            rows = [(rng.randrange(8), rng.randrange(10_000_000),
                     rng.randrange(10_000_000))
                    for _ in range(rng.randrange(2, 35))]
            truth = self.brute(rows)
            self.assertEqual(synchronized_strikes(rows), truth)
            self.assertEqual(independent_atomic(rows), truth)

    def test_large_sparse_original_strike_book_and_exact_boundary(self):
        rows = [(i, 3_000_007 * i, 3_000_007 * i) for i in range(12000)]
        self.assertFalse(synchronized_strikes(rows))
        self.assertFalse(independent_atomic(rows))
        rows.append((12001, 3_000_007 * 11000 + 1_000_000,
                     3_000_007 * 11000 + 1_000_000))
        self.assertTrue(synchronized_strikes(rows))
        self.assertTrue(independent_atomic(rows))
        rows[-1] = (12001, 3_000_007 * 11000 + 1_000_001,
                    3_000_007 * 11000 + 1_000_000)
        self.assertFalse(synchronized_strikes(rows))
        self.assertFalse(independent_atomic(rows))

    def test_independent_stream_digest_detects_late_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.csv.gz"
            content = bytes(range(256)) * 32769
            path.write_bytes(content)
            self.assertEqual(independent_stream_digest(path),
                             hashlib.sha256(content).hexdigest())
            with path.open("r+b") as fp:
                fp.seek(-1, 2)
                fp.write(b"X")
            self.assertNotEqual(independent_stream_digest(path),
                                hashlib.sha256(content).hexdigest())


if __name__ == "__main__":
    unittest.main()
