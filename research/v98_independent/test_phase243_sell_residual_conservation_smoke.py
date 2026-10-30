"""V98 Independent Phase243 deterministic adversarial seller conservation tests."""
import unittest
from phase243_sell_residual_conservation import audit_trade_side_conservation

class SellerConservationTests(unittest.TestCase):
    def test_valid_seller(self):
        result=audit_trade_side_conservation([99.],[101.],[10.],[1000.],[5.],[500.])
        self.assertEqual(result['checked_bars'],1)
    def test_impossible_seller(self):
        with self.assertRaises(ValueError):
            audit_trade_side_conservation([99.],[101.],[10.],[1000.],[9.9],[980.1])

if __name__ == '__main__':
    unittest.main()
