import unittest
from scripts.v99_phase195bl_crossartifact_pit_audit import audit

def paper(ops=None):
    return {'variants': {k: {'operations': (ops or []) if k == 'f1' else []}
            for k in ('r98','f1','f3','f7','f12')}}

class TestCrossArtifact(unittest.TestCase):
    def test_later_receipt_is_not_proof(self):
        old=paper()
        new=paper([{'timestamp':'2026-09-28T09:00:00Z','symbol':'MINAUSDT'}])
        u={'symbols': {'MINAUSDT': {'source':'dynamic_binance_discovery',
                                    'discovered_at_utc':'2026-10-10T10:11:55Z'}}}
        x=audit(old,new,[u])
        self.assertEqual(len(x['variants']['f1']['new_only_before_later_observed_receipt']),1)
        self.assertFalse(x['publication_authorized'])
        self.assertFalse(x['promotion_authorized'])
        self.assertTrue(x['later_observed_receipt_is_not_original_asof_proof'])

    def test_no_retroactive_conflict_without_source(self):
        x=audit(paper(),paper([{'timestamp':'2026-09-28T09:00:00Z','symbol':'OTHERUSDT'}]),[{'symbols':{}}])
        self.assertFalse(x['variants']['f1']['new_only_before_later_observed_receipt'])
        self.assertEqual(x['status'],'DATA_ONLY_HOLD')

    def test_reissued_first_seen(self):
        u=lambda t: {'symbols': {'MINAUSDT': {'source':'dynamic_binance_discovery','discovered_at_utc':t}}}
        x=audit(paper(),paper(),[u('2026-10-10T10:11:55Z'),u('2026-10-10T10:35:25Z')])
        self.assertIn('MINAUSDT',x['receipt_reissued_symbols'])

if __name__=='__main__':
    unittest.main()
