"""V98 Phase1002 independent synthetic LP witness/stress tests, no PnL."""
import hashlib
import unittest
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from phase1002_lp_opening_repair import repair_open_lp


def oracle(cash, units, opening, quote, fee):
    v = np.asarray(units)*np.asarray(opening)
    eq = float(cash+v.sum())
    if eq<=0:
        return None
    a = [[-(1-1.75*fee)]*4]
    b = [1.75*eq-float(v.sum())]
    for i in range(4):
        row = [.7*fee]*4
        row[i] -= 1.
        a.append(row)
        b.append(.7*eq-float(v[i]))
    r = linprog(np.ones(4), A_ub=a, b_ub=b,
                bounds=[(0.,float(min(v[i],.05*quote[i]))) for i in range(4)],
                method="highs")
    return r.x if r.success else None


def postcheck(cash, units, opening, quote, fee, sold):
    v = np.asarray(units)*np.asarray(opening)
    quote = np.asarray(quote, dtype=float)
    eq = float(cash+v.sum()-fee*sum(sold))
    post = v-sold
    tol = 1e-8*max(1.,eq)
    return (eq>0 and post.sum()<=1.75*eq+tol and post.max()<=.7*eq+tol
            and np.all(sold>=-tol) and np.all(sold<=np.minimum(v,.05*quote)+tol))


class Phase1002Tests(unittest.TestCase):
    def test_first_known_frozen_false_reject_witness(self):
        cash=-.7202662722218487
        units=[.5412912354161488,.4806826563859366,.40354461273394204,.2947477676858214]
        opening=[.521971928769377,.8909223872488171,.9751890297701439,.5557234772182785]
        quote=[6.998301376662904,5.429355246602696,1.8218868654585496,1.327270982415965]
        _,_,sold,ok=repair_open_lp(cash,units,opening,quote,.002)
        self.assertTrue(ok)
        self.assertTrue(postcheck(cash,units,opening,quote,.002,sold))

    def test_second_known_frozen_false_reject_witness(self):
        cash=-.7385183481980049
        units=[.5454144986389852,.45229924143851424,.449131946109143,.29167266201136266]
        opening=[.5038281743239417,.4272478528253305,.5927907881420715,1.2252131515608515]
        quote=[3.542891199302763,7.425270954273352,9.690242226978778,12.60996429143994]
        _,_,sold,ok=repair_open_lp(cash,units,opening,quote,.002)
        self.assertTrue(ok)
        self.assertTrue(postcheck(cash,units,opening,quote,.002,sold))

    def test_zero_exposure_and_causality(self):
        cash,u,s,ok=repair_open_lp(1.,[0]*4,[1]*4,[0]*4,.0007)
        self.assertTrue(ok)
        self.assertEqual(cash,1.)
        self.assertEqual(sum(s),0.)

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            repair_open_lp(1.,[0,0,np.nan,0],[1]*4,[1]*4,.0007)

    def test_frozen_phase915_sha_unchanged(self):
        file=Path(__file__).resolve().parent/"phase915_n_open_repair.py"
        self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),
                         "9275cb642863d4dc0a79ac15ee0e31058ad5ea7caac1173278046c4b5c6bdcbd")

    def test_preregistered_12000_gap_scenarios(self):
        rng=np.random.default_rng(1195)
        eligible=feasible=reject=accept=excess=0
        for _ in range(12000):
            gross=float(rng.uniform(1.1,1.75))
            weights=rng.dirichlet(np.ones(4)*rng.uniform(1,8))*gross
            if weights.max()>.7:
                continue
            eligible+=1
            cash=1-gross
            opening=np.exp(rng.normal(0,rng.uniform(.05,.45),4))
            quote=(weights*opening)/.05*rng.uniform(.2,2,4)
            fee=float(rng.choice([.0007,.0012,.002]))
            opt=oracle(cash,weights,opening,quote,fee)
            _,_,sold,ok=repair_open_lp(cash,weights,opening,quote,fee)
            if opt is None:
                accept+=int(ok)
                continue
            feasible+=1
            if not ok:
                reject+=1
                continue
            self.assertTrue(postcheck(cash,weights,opening,quote,fee,sold))
            if sold.sum()>opt.sum()+1e-5:
                excess+=1
        print({"eligible":eligible,"lp_feasible":feasible,
               "false_accept":accept,"false_reject":reject,"excess_turnover":excess})
        self.assertEqual(accept,0)
        self.assertEqual(excess,0)
        self.assertEqual(reject,0)


if __name__=="__main__":
    unittest.main()
