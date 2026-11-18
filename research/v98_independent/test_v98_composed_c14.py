"""C14 deterministic invariants only, not an economic validation."""
import math
import unittest
from research.v98_independent.phase243_native_funding_cashflow import ASSETS
from research.v98_independent.v98_composed_c14 import WARMUP,REBALANCE,composed_c14_sleeves,c14_router,c14_allocator
class C14Invariants(unittest.TestCase):
    def history(self,slope):
        return {a:[100*math.exp(slope*i) for i in range(WARMUP+REBALANCE+1)] for a in ASSETS}
    def test_assets(self):
        h=self.history(.0002);del h[next(iter(ASSETS))]
        with self.assertRaisesRegex(ValueError,"C14_CLEAN4_ONLY"):composed_c14_sleeves()(h)
    def test_flat(self):
        s=composed_c14_sleeves()(self.history(0))
        self.assertTrue(all(all(x==0 for x in v) for v in s.values()))
    def test_caps_and_governor(self):
        h=self.history(.0002);s=composed_c14_sleeves()(h);r={a:c14_router(h[a][:WARMUP+1]) for a in ASSETS}
        hi=c14_allocator(s,r,1);lo=c14_allocator(s,r,.25)
        self.assertLessEqual(sum(hi.values()),.90+1e-12)
        self.assertTrue(all(0<=lo[a]<=hi[a]+1e-12 and hi[a]<=.40+1e-12 for a in ASSETS))
    def test_no_rebalance(self):
        h=self.history(.0002);f=composed_c14_sleeves()
        x=f({a:v[:WARMUP+1] for a,v in h.items()})
        y=f({a:v[:WARMUP+2] for a,v in h.items()})
        self.assertEqual(x,y)
if __name__=="__main__":unittest.main()
