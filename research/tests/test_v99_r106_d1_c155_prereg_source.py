"""C155 source-only D1 prereg regression: no market data, no orders, no PnL."""
import unittest
from datetime import datetime, timedelta, timezone
from research.tools.v99_r106_d1_basis_carry_preregistered import (
    PairedBar, FundingFix, FeeEvidence, decide, historical_source_gate,
    report_permissions, COST_SHOCKS, TRAIN_END,
)

UTC = timezone.utc
T = datetime(2022, 1, 1, tzinfo=UTC)


def bars(asset, *, count=168, last=T-timedelta(hours=1), basis=.005):
    start = last-timedelta(hours=count-1)
    price = 1000. if asset == 'BTC' else 100.
    return [PairedBar(start+timedelta(hours=i), asset, price, price*(1+basis),
                      'OKX', 'OKX', start+timedelta(hours=i)) for i in range(count)]


def fixes(asset, rate=.003):
    inst = asset+'-USDT-SWAP'
    return [FundingFix(asset, T-timedelta(hours=h), T-timedelta(hours=h),
                       rate, 'OKX', inst) for h in (17, 9, 1)]


class D1PreregisteredSourceOnly(unittest.TestCase):
    def test_distinct_severe_vs_supersevere_cash_decision(self):
        b = {a: bars(a) for a in ('BTC', 'ETH')}
        f = {a: fixes(a) for a in ('BTC', 'ETH')}
        severe = decide(T, b, f, COST_SHOCKS['severe_model_only'])
        supersevere = decide(T, b, f, COST_SHOCKS['supersevere_model_only'])
        self.assertEqual((severe.btc_pair_weight, severe.eth_pair_weight), (.25, .25))
        self.assertEqual((supersevere.btc_pair_weight, supersevere.eth_pair_weight), (0., 0.))
        self.assertEqual(severe.feature_max_time, T-timedelta(hours=1))
        self.assertEqual(severe.funding_asof, T-timedelta(hours=1))

    def test_sealed_decision_rejected(self):
        b = {a: bars(a, last=TRAIN_END-timedelta(hours=1)) for a in ('BTC', 'ETH')}
        f = {a: fixes(a) for a in ('BTC', 'ETH')}
        with self.assertRaisesRegex(ValueError, 'TRAIN_ONLY'):
            decide(TRAIN_END, b, f, COST_SHOCKS['severe_model_only'])

    def test_missing_t_minus_one_hour_rejected(self):
        b = {a: bars(a) for a in ('BTC', 'ETH')}
        b['BTC'] = bars('BTC', last=T-timedelta(hours=2))
        with self.assertRaisesRegex(ValueError, 'MISSING_CAUSAL_WARMUP'):
            decide(T, b, {a: fixes(a) for a in ('BTC', 'ETH')}, .0007)

    def test_unregistered_cost_rejected(self):
        with self.assertRaisesRegex(ValueError, 'UNPREREGISTERED'):
            decide(T, {}, {}, .0008)

    def test_wrong_funding_instrument_rejected(self):
        with self.assertRaisesRegex(ValueError, 'INSTRUMENT'):
            FundingFix('BTC', T-timedelta(hours=1), T-timedelta(hours=1),
                       .003, 'OKX', 'ETH-USDT-SWAP')

    def test_stale_or_wrong_interval_funding_rejected(self):
        b = {a: bars(a) for a in ('BTC', 'ETH')}
        f = {a: fixes(a) for a in ('BTC', 'ETH')}
        f['BTC'][1] = FundingFix('BTC', T-timedelta(hours=8), T-timedelta(hours=8),
                                 .003, 'OKX', 'BTC-USDT-SWAP')
        with self.assertRaisesRegex(ValueError, 'FUNDING_INTERVAL'):
            decide(T, b, f, .0007)

    def test_structural_labels_are_not_authenticated(self):
        b = {a: bars(a, count=193) for a in ('BTC', 'ETH')}
        f = {a: fixes(a) for a in ('BTC', 'ETH')}
        tier = FeeEvidence('OKX', .001, .001, T-timedelta(days=365),
                           T+timedelta(days=1), 'unverified-example')
        result = historical_source_gate(b, f, tier)
        self.assertTrue(result['structural_consistency'])
        self.assertFalse(result['exchange_authenticated'])
        self.assertFalse(result['historical_economics_authorized'])

    def test_permissions_never_authorize_promotion_or_orders(self):
        p = report_permissions()
        for k in ('historical_train_economics_run', 'validation_opened',
                  'final_holdout_opened', 'settled_funding_authenticated',
                  'fills_authenticated', 'native_fee_tier_authenticated',
                  'promotion_authorized', 'real_orders_enabled',
                  'paper_publication_authorized'):
            self.assertIs(p[k], False)


if __name__ == '__main__':
    unittest.main()
