import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from research.tools.v99_r106_fresh_pair_selector import select

NOW = datetime(2026, 11, 10, 22, 45, tzinfo=timezone.utc)

class TestFreshPair(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for stream in ("markets", "terms"):
            (self.root / stream).mkdir()

    def pair(self, bucket):
        for stream in ("markets", "terms"):
            (self.root / stream / bucket).mkdir()

    def report(self, market, terms):
        b = market.name
        return {"market_acquired_utc": b + ":10:00+00:00",
                "terms_acquired_utc": b + ":20:00+00:00",
                "paper_publication_authorized": False,
                "promotion_authorized": False}

    def test_latest_fresh(self):
        self.pair("2026-11-10T22")
        self.assertEqual(select(self.root, now=NOW, audit_fn=self.report)["bucket"], "2026-11-10T22")

    def test_newest_bad_older_valid_within_budget(self):
        self.pair("2026-11-10T22")
        self.pair("2026-11-10T21")
        def checker(m,t):
            if m.name.endswith("22"):
                raise ValueError("raw hash mismatch")
            return self.report(m,t)
        out = select(self.root, now=NOW, audit_fn=checker)
        self.assertEqual(out["bucket"], "2026-11-10T21")
        self.assertEqual(len(out["rejected_newer_buckets"]), 1)

    def test_all_bad_fails_closed(self):
        self.pair("2026-11-10T22")
        with self.assertRaisesRegex(ValueError, "NO_FRESH_VERIFIED_PAIR"):
            select(self.root, now=NOW, audit_fn=lambda m,t: (_ for _ in ()).throw(ValueError("forged hash")))

    def test_stale_rejected(self):
        self.pair("2026-11-10T19")
        with self.assertRaisesRegex(ValueError, "NO_FRESH_VERIFIED_PAIR"):
            select(self.root, now=NOW, audit_fn=self.report)

    def test_cross_hour_never_paired(self):
        (self.root / "markets" / "2026-11-10T22").mkdir()
        (self.root / "terms" / "2026-11-10T21").mkdir()
        with self.assertRaisesRegex(ValueError, "NO_FRESH_VERIFIED_PAIR"):
            select(self.root, now=NOW, audit_fn=self.report)

    def test_skew_rejected(self):
        self.pair("2026-11-10T22")
        def checker(m,t):
            r = self.report(m,t)
            r["terms_acquired_utc"] = "2026-11-10T22:40:00+00:00"
            return r
        with self.assertRaisesRegex(ValueError, "NO_FRESH_VERIFIED_PAIR"):
            select(self.root, now=NOW, audit_fn=checker)

    def test_no_authorization_leak(self):
        self.pair("2026-11-10T22")
        def checker(m,t):
            r = self.report(m,t)
            r["promotion_authorized"] = True
            return r
        with self.assertRaisesRegex(ValueError, "NO_FRESH_VERIFIED_PAIR"):
            select(self.root, now=NOW, audit_fn=checker)

if __name__ == "__main__":
    unittest.main()
