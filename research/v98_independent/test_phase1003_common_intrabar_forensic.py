"""V98 Phase1003 no-network static corner risk tests."""
import unittest
import numpy as np
from phase1003_common_intrabar_forensic import static_corners


class StaticForensicTests(unittest.TestCase):
    def test_cash_only_survives_every_corner(self):
        corners=static_corners([0]*4,[1]*4,[.8]*4,[1.2]*4)
        self.assertEqual(len(corners),6)
        self.assertTrue(all(x["survives"] for x in corners))

    def test_concentration_shock_is_detected(self):
        corners=static_corners([.7,0,0,0],[1]*4,[1]*4,[1.5,1,1,1])
        self.assertTrue(any(not x["survives"] for x in corners))

    def test_cash_short_gross_shock_is_detected(self):
        corners=static_corners([.5,.5,.5,.25],[1]*4,[.5]*4,[1.8]*4)
        self.assertTrue(any(not x["survives"] for x in corners))


if __name__=="__main__":
    unittest.main()
