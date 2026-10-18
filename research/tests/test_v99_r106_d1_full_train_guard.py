"""Synthetic structural TRAIN calendar gate. No market access, no economics."""
import unittest
from copy import deepcopy
from research.tools.v99_r106_d1_full_train_guard import check_complete_train

class CompleteTrainCalendar(unittest.TestCase):
    def setUp(self):
        a = {'first_hour':'2021-12-09T00:00:00+00:00',
             'last_hour':'2023-09-30T23:00:00+00:00',
             'paired_hours':15864, 'funding_rows':1983}
        self.audit = {'status':'STRUCTURAL_ONLY_NOT_AUTHENTICATED',
                      'assets':{'BTC':deepcopy(a),'ETH':deepcopy(a)}}

    def test_complete_metadata_does_not_authorize_pnl(self):
        r = check_complete_train(self.audit)
        self.assertEqual(r['expected_funding_fixes_per_asset'],1983)
        self.assertEqual(r['paired_hours_per_asset'],15864)
        for key in ('exchange_authenticated','historical_economics_authorized',
                    'validation_opened','holdout_opened','promotion_authorized'):
            self.assertIs(r[key],False)

    def test_funding_undercoverage_rejected(self):
        for n in (0,3,1982):
            with self.subTest(n=n):
                a=deepcopy(self.audit)
                a['assets']['BTC']['funding_rows']=n
                with self.assertRaisesRegex(ValueError,'FUNDING'):
                    check_complete_train(a)

    def test_funding_overcoverage_rejected(self):
        self.audit['assets']['ETH']['funding_rows']=1984
        with self.assertRaisesRegex(ValueError,'FUNDING'):
            check_complete_train(self.audit)

    def test_boolean_and_string_counts_rejected(self):
        for n in (True,'1983',1983.0):
            with self.subTest(n=n):
                a=deepcopy(self.audit)
                a['assets']['ETH']['funding_rows']=n
                with self.assertRaisesRegex(ValueError,'FUNDING'):
                    check_complete_train(a)

    def test_incomplete_train_rejected(self):
        self.audit['assets']['BTC']['paired_hours']=200
        with self.assertRaisesRegex(ValueError,'GRID'):
            check_complete_train(self.audit)

    def test_shift_into_sealed_validation_rejected(self):
        self.audit['assets']['BTC']['last_hour']='2023-10-01T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError,'GRID'):
            check_complete_train(self.audit)

    def test_naive_time_rejected(self):
        self.audit['assets']['BTC']['first_hour']='2021-12-09T00:00:00'
        with self.assertRaisesRegex(ValueError,'UTC'):
            check_complete_train(self.audit)

    def test_funding_only_metadata_not_receipts(self):
        r=check_complete_train(self.audit)
        self.assertEqual(r['status'],'COMPLETE_CALENDAR_STRUCTURAL_ONLY')
        self.assertFalse(r['exchange_authenticated'])

if __name__ == '__main__':
    unittest.main()
