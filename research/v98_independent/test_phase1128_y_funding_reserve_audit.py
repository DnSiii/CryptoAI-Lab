import unittest
from phase1128_y_funding_reserve_audit import audit
class TestYReserveAudit(unittest.TestCase):
    def test_formal_stop_funding_reserve_gap(self):
        x=audit()
        self.assertTrue(x['source_accepts'])
        self.assertTrue(x['uncertified_exit'])
        self.assertLess(x['true_exit_after_reserve'],x['floor'])
        self.assertFalse(x['historical_pnl_computed'])
if __name__=='__main__':unittest.main()
