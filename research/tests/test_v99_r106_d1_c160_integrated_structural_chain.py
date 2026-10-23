"""C160 full TRAIN integration negative controls: SYNTHETIC, no ROI claims."""
import unittest
from datetime import timedelta

from research.tools.v99_r106_d1_full_train_guard import START, HOURS
from research.tools.v99_r106_d1_basis_carry_preregistered import Decision
from research.verification.independent_d1_c148_risk_fold_scorecard import SCENARIOS
from research.verification.independent_d1_c160_integrated_structural_chain import (
    verify_integrated_train_structural_only as check,
)


def fixture():
    marks = {a: {'spot': '100', 'perp': '100'} for a in ('BTC', 'ETH')}
    cash = {'cash_quote': '1000', 'spot_base': {'BTC': '0', 'ETH': '0'},
            'perp_base': {'BTC': '0', 'ETH': '0'}}
    schedule = {a: [] for a in ('BTC', 'ETH')}
    frames = []
    for i in range(HOURS):
        t = START + timedelta(hours=i)
        funding = []
        if i % 8 == 0:
            for a in schedule:
                schedule[a].append(t)
                funding.append({'asset': a, 'time': t, 'rate': '0',
                                'source': 'OKX', 'instrument': a + '-USDT-SWAP'})
        frames.append({'time': t, 'marks': marks, 'funding': funding,
                       'before': cash, 'after_mark': cash,
                       'after_funding': cash, 'after': cash, 'fills': []})
    decisions = {}
    for i in range(168, HOURS, 24):
        t = START + timedelta(hours=i)
        decisions[t] = Decision(
            t, 0, 0, 'SIDEWAYS__LOW_VOLATILITY',
            t - timedelta(hours=1), t - timedelta(hours=1),
            'PREREGISTERED_RESEARCH_INTENT_ONLY'
        )
    proof = {'hours_replayed': HOURS, 'fills_replayed': 0,
             'funding_events_modeled': 3966,
             'perp_variation_margin_quote': '0',
             'modeled_funding_quote': '0',
             'modeled_native_plus_stress_fees_quote': '0',
             'last_declared_account_state': cash,
             'modeled_net_nav_delta_quote': '0'}
    journals = {
        s: {'frames': frames, 'account_proof': proof,
            'c146_full_feature_funding_proof': {'decision_hours_checked': 654}}
        for s in SCENARIOS
    }
    return journals, {s: decisions for s in SCENARIOS}, schedule, marks


def replace_frame(journals, scenario, index, **changes):
    old = journals[scenario]
    copy = dict(old)
    copy['frames'] = list(old['frames'])
    copy['frames'][index] = {**copy['frames'][index], **changes}
    return {**journals, scenario: copy}


class C160IntegratedChain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.j, cls.d, cls.schedule, cls.marks = fixture()

    def audit(self, journals=None):
        return check(self.j if journals is None else journals, self.d,
                     self.schedule, self.marks, START - timedelta(hours=1))

    def test_full_15864h_two_scenario_chain_is_still_not_economic(self):
        r = self.audit()
        self.assertEqual(r['train_hours_per_scenario'], 15864)
        self.assertEqual(r['daily_decisions'], 654)
        self.assertEqual(r['funding_events_per_scenario'], 3966)
        self.assertEqual(r['chronological_folds'], [3172,3173,3173,3173,3173])
        for s in SCENARIOS:
            self.assertEqual(r['independent_account_hours_per_scenario'][s], HOURS)
            self.assertEqual(r['independent_account_residuals'][s], '0')
            self.assertEqual(r['risk_model_only']['scenarios'][s]['model_only_positive_folds'], 0)
        for key in ('independent_c146_feature_reexecution',
                    'first_party_okx_receipts_authenticated',
                    'native_historical_fee_and_fills_authenticated',
                    'historical_roi_authorized', 'validation_opened',
                    'holdout_opened', 'promotion_authorized', 'orders_enabled'):
            self.assertIs(r[key], False, key)

    def test_scenario_specific_initial_capital_is_rejected(self):
        # Previously a C148 scorecard could use scenario-1's baseline for
        # both paths. Reject before risk scoring even if books are balanced.
        other = SCENARIOS[1]
        modified = replace_frame(self.j, other, 0,
            before={'cash_quote':'1100',
                    'spot_base':{'BTC':'0','ETH':'0'},
                    'perp_base':{'BTC':'0','ETH':'0'}})
        with self.assertRaisesRegex(ValueError, 'C160_SCENARIO_INITIAL_CAPITAL_MISMATCH'):
            self.audit(modified)

    def test_missing_one_funding_fix_rejected(self):
        other = SCENARIOS[0]
        fr = self.j[other]['frames'][800]
        modified = replace_frame(self.j, other, 800,
                                 funding=[ev for ev in fr['funding'] if ev['asset']!='ETH'])
        # Tamper the summary too, so C149 cannot catch the missing event
        # by its total count; the independent C133 schedule must still fail.
        changed = dict(modified[other])
        changed['account_proof'] = {**changed['account_proof'], 'funding_events_modeled': 3965}
        modified = {**modified, other: changed}
        with self.assertRaisesRegex(ValueError, 'C132_UNSCHEDULED_OR_MISSING_FUNDING_FIX'):
            self.audit(modified)

    def test_scenario_specific_market_price_rejected(self):
        other = SCENARIOS[1]
        modified = replace_frame(self.j, other, 500,
            marks={'BTC':{'spot':'101','perp':'100'},
                   'ETH':{'spot':'100','perp':'100'}})
        with self.assertRaisesRegex(ValueError, 'C148_EXOGENOUS_PRICE_OR_FUNDING_DIVERGENCE'):
            self.audit(modified)

    def test_sealed_hour_rejected(self):
        other = SCENARIOS[1]
        modified = replace_frame(self.j, other, HOURS-1,
                                 time=START + timedelta(hours=HOURS))
        with self.assertRaises(ValueError):
            self.audit(modified)

    def test_missing_scenario_rejected(self):
        with self.assertRaisesRegex(ValueError, 'C160_TWO_COST_PATHS_REQUIRED'):
            self.audit({SCENARIOS[0]:self.j[SCENARIOS[0]]})


if __name__ == '__main__':
    unittest.main()
