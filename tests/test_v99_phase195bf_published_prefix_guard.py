import io, json, unittest, zipfile
from scripts.v99_phase195bf_published_prefix_guard import TRACKS, audit, strict_index


def fixture(rewrite=False, missing=False):
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        for t in TRACKS:
            name=f'paper_{t}_ledger.json'
            row={'timestamp':'2026-10-01T16:00:00+00:00','capital_brl':10000}
            z.writestr('reports/published_baseline/'+name,json.dumps({'mode':'PAPER_ONLY','equity_curve':[row]}))
            new=[] if missing else [{**row,'capital_brl':9999 if rewrite else 10000}]
            z.writestr('reports/'+name,json.dumps({'mode':'PAPER_ONLY','equity_curve':new}))
    b.seek(0)
    return zipfile.ZipFile(b)


class PrefixGuardTests(unittest.TestCase):
    def test_identical_prefix(self):
        r=audit(fixture());self.assertEqual(r['status'],'PREFIX_PASS_NOT_PROMOTION')
        self.assertFalse(r['publication_authorized'])
    def test_rewrite_fails_closed(self):
        r=audit(fixture(rewrite=True));self.assertEqual(r['status'],'DATA_ONLY_HOLD')
        self.assertEqual(sum(len(t['rewritten_published']) for t in r['tracks'].values()),8)
    def test_missing_fails_closed(self):
        self.assertEqual(audit(fixture(missing=True))['status'],'DATA_ONLY_HOLD')
    def test_duplicate_fails(self):
        with self.assertRaises(ValueError):strict_index([{'timestamp':'2026-10-01T16:00:00Z'}]*2)
    def test_hour_gap_fails(self):
        with self.assertRaises(ValueError):strict_index([{'timestamp':'2026-10-01T16:00:00Z'},
                                                         {'timestamp':'2026-10-01T18:00:00Z'}])
    def test_naive_timestamp_fails(self):
        with self.assertRaises(ValueError):strict_index([{'timestamp':'2026-10-01T16:00:00'}])


if __name__=='__main__':unittest.main()
