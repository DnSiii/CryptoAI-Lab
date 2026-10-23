#!/usr/bin/env python3
"""V98 Phase1011: independent synthetic 16-corner bisection oracle for O governor."""
from __future__ import annotations
import unittest
import numpy as np
from phase1006_o_sevenslot_source import robust_scale, verify_corners, waterfill


def independent_safe(w, dn, up, k):
    """Direct equity and corner accounting, no reuse of O governor algebra."""
    positions = w * k[:,None]
    cash = 1 - positions.sum(axis=1)
    safe = np.ones(len(k), dtype=bool)
    for bits in range(16):
        f = np.array([1+up[:,j] if (bits>>j)&1 else 1-dn[:,j] for j in range(4)]).T
        value = positions*f
        eq = cash+value.sum(axis=1)
        safe &= eq >= .10-1e-11
        safe &= value.sum(axis=1) <= 1.75*eq+1e-11
        safe &= np.all(value <= .70*eq[:,None]+1e-11,axis=1)
    return safe


class OGovernorOracleTests(unittest.TestCase):
    def test_3000_seeded_independent_maximal_retention_oracle(self):
        rng=np.random.default_rng(1011)
        n=3000
        scores=rng.uniform(.001,1,(n,4))
        gross=rng.uniform(.20,1.50,n)
        w=np.vstack([waterfill(scores[i],float(gross[i])) for i in range(n)])
        dn=rng.uniform(0,.8,(n,4))
        up=rng.uniform(0,.8,(n,4))
        k=robust_scale(w,dn,up)
        self.assertTrue(verify_corners(w*k[:,None],dn,up))
        self.assertTrue(independent_safe(w,dn,up,k).all())
        left=np.zeros(n)
        right=np.ones(n)
        for _ in range(40):
            mid=(left+right)/2
            safe=independent_safe(w,dn,up,mid)
            left=np.where(safe,mid,left)
            right=np.where(safe,right,mid)
        self.assertLessEqual(float(np.max(np.abs(k-left))),1e-8)
        self.assertTrue((k<=1).all())
        self.assertTrue((k>=0).all())

    def test_extreme_shock_still_fails_closed(self):
        w=np.array([[.7,.4,.2,.1]])
        dn=np.full((1,4),.99)
        up=np.full((1,4),10.)
        k=robust_scale(w,dn,up)
        self.assertTrue(verify_corners(w*k[:,None],dn,up))
        self.assertLess(float(k[0]),1.)

    def test_nonfinite_and_invalid_witnesses(self):
        w=np.array([[.4,.2,.1,0.]])
        dn=np.full((1,4),.1)
        up=np.full((1,4),.1)
        with self.assertRaises(ValueError):
            robust_scale(np.array([[.8,0.,0.,0.]]),dn,up)
        with self.assertRaises(ValueError):
            robust_scale(w,np.full((1,4),1.),up)
        nan=np.full((1,4),np.nan)
        k=robust_scale(w,nan,nan)
        self.assertEqual(float(k[0]),0.)
        self.assertTrue(verify_corners(w*k[:,None],nan,nan))


if __name__=="__main__":
    unittest.main()
