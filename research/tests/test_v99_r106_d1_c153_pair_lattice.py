"""C153 deterministic algebraic proofs; no historical prices or OKX access."""
import unittest
from fractions import Fraction
from research.verification.independent_d1_c153_pair_lattice import common_step, pair_lattice

BASE=dict(spot_lot_base='0.000001',swap_contract_base='0.01',
          swap_lot_contracts='1',spot_fee_rate='0.001',
          spot_min_base='0.000001',swap_min_contracts='1',
          max_pair_base='0.5')

class PairLattice(unittest.TestCase):
    def case(self, **kwargs):
        return pair_lattice(**(BASE | kwargs))
    def test_quote_fee_exact_hedge_is_one_contract(self):
        p=self.case(spot_fee_currency='QUOTE',spot_side='buy')
        self.assertEqual(Fraction(p['first_exact_hedge_base']),Fraction(1,100))
        self.assertTrue(p['fits_declared_pair_cap'])
    def test_base_buy_fee_requires_999_hypothetical_btc(self):
        p=self.case(spot_fee_currency='BASE',spot_side='buy')
        self.assertEqual(Fraction(p['first_exact_hedge_base']),Fraction(999,100))
        self.assertFalse(p['fits_declared_pair_cap'])
    def test_base_sell_fee_requires_1001_hypothetical_btc(self):
        p=self.case(spot_fee_currency='BASE',spot_side='sell')
        self.assertEqual(Fraction(p['first_exact_hedge_base']),Fraction(1001,100))
        self.assertFalse(p['fits_declared_pair_cap'])
    def test_zero_fee_works_for_both_sides(self):
        for side in ('buy','sell'):
            self.assertEqual(Fraction(self.case(spot_fee_currency='BASE',spot_side=side,spot_fee_rate='0')['first_exact_hedge_base']),Fraction(1,100))
    def test_minimums_raise_first_executable_quantity(self):
        p=self.case(spot_fee_currency='QUOTE',spot_side='buy',swap_min_contracts='3')
        self.assertEqual(Fraction(p['first_exact_hedge_base']),Fraction(3,100))
    def test_fractional_lcm_independent_example(self):
        self.assertEqual(common_step(Fraction(3,20),Fraction(1,10)),Fraction(3,10))
    def test_rejects_bad_declared_specs(self):
        for kw in ({'spot_lot_base':'0'}, {'spot_fee_rate':'1'},
                   {'spot_fee_rate':'NaN'}, {'spot_fee_currency':'UNKNOWN'},
                   {'max_pair_base':'-1'}):
            with self.assertRaises(ValueError): self.case(**({'spot_fee_currency':'BASE','spot_side':'buy'} | kw))
    def test_independent_small_integer_enumeration(self):
        proof=self.case(spot_lot_base='0.05',swap_contract_base='0.1',
                        spot_fee_rate='0.2',spot_fee_currency='BASE',spot_side='buy',
                        spot_min_base='0.05',swap_min_contracts='1')
        self.assertEqual(Fraction(proof['first_exact_hedge_base']),Fraction(1,5))
        candidates={Fraction(n,20)*Fraction(4,5) for n in range(1,20)}
        contracts={Fraction(n,10) for n in range(1,20)}
        self.assertEqual(min(candidates & contracts),Fraction(1,5))
    def test_never_promotes(self):
        p=self.case(spot_fee_currency='QUOTE',spot_side='buy')
        for k in ('exchange_authenticated','historical_roi_authorized','validation_opened','holdout_opened','promotion_authorized','orders_enabled'):
            self.assertFalse(p[k])

if __name__=='__main__': unittest.main()
