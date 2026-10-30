import unittest
import numpy as np
from test_phase1189_ad_online_core_router import sample
from phase1191_ad_funding_event_opportunity import opportunity_intents


def fixture(n=1100):
    f=sample(n)
    f[5].iloc[800,0]=.02
    f[3].iloc[800,0]*=1.1
    f[1].iloc[800,0]=max(f[1].iloc[800,0],f[3].iloc[800,0])*1.01
    return f


class OpportunityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=fixture()
        cls.out,cls.diag=opportunity_intents(*cls.f,diagnostics=True)

    def test_crowded_long_short_direction(self):
        self.assertEqual(self.out[800,0],-1)
        self.assertEqual(self.out[799,0],0)

    def test_sixteen_hour_expiry(self):
        self.assertTrue((self.out[800:816,0]==-1).all())
        self.assertEqual(self.out[816,0],0)

    def test_funding_trigger_requires_native_event(self):
        f=[x.copy() for x in self.f]
        f[3].iloc[801,1]*=1.2
        f[1].iloc[801,1]=max(f[1].iloc[801,1],f[3].iloc[801,1])*1.01
        np.testing.assert_array_equal(self.out,opportunity_intents(*f))

    def test_negative_funding_and_divergence_go_long(self):
        f=sample(1100)
        f[5].iloc[800,1]=-.02
        f[3].iloc[800,1]*=.9
        f[2].iloc[800,1]=min(f[2].iloc[800,1],f[3].iloc[800,1])*.99
        self.assertEqual(opportunity_intents(*f)[800,1],1)

    def test_cooldown_blocks_second_settlement(self):
        f=[x.copy() for x in self.f]
        f[5].iloc[824,0]=.08
        f[3].iloc[824,0]*=1.2
        f[1].iloc[824,0]=max(f[1].iloc[824,0],f[3].iloc[824,0])*1.01
        out=opportunity_intents(*f)
        self.assertTrue((out[816:848,0]==0).all())

    def test_prefix_causality(self):
        f=[x.copy() for x in self.f]
        f[5].iloc[904,0]=.1
        out=opportunity_intents(*f)
        np.testing.assert_array_equal(out[:904],self.out[:904])

    def test_future_extension(self):
        f=fixture(1300)
        out=opportunity_intents(*f)
        np.testing.assert_array_equal(out[:1100],self.out)

    def test_no_signal_before_90_event_warmup(self):
        self.assertTrue((self.out[:720]==0).all())

    def test_signed_integer_intents_and_no_pnl(self):
        self.assertEqual(self.out.dtype,np.int8)
        self.assertTrue(np.isin(self.out,[-1,0,1]).all())
        self.assertFalse(self.diag['historical_system_pnl_computed'])
        self.assertFalse(self.diag['validation_2025_read'])
        self.assertFalse(self.diag['external_benchmarks_used'])


if __name__=='__main__':unittest.main()
