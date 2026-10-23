"""C162 synthetic full-TRAIN fee-veto replay, never real OKX PnL."""
import unittest
from datetime import timedelta
from research.tests.test_v99_r106_d1_c161_causal_decision_oracle import fixture
from research.tools.v99_r106_d1_basis_carry_preregistered import (
    Decision, FeeEvidence, FundingFix,
)
from research.tools.v99_r106_d1_native_fee_veto_cycle136 import (
    CausalFeeTier, fee_bound_intent,
)
from research.tools.v99_r106_d1_full_train_guard import START, END
from research.verification.independent_d1_c162_exact_native_fee_reexecution import (
    verify_exact_fee_veto as check,
    SCENARIOS,
)


def setup():
    _, _, _, _, evidence = fixture()
    fee = FeeEvidence('OKX', .001, .0005,
                      START-timedelta(days=60), END,
                      'SYNTHETIC_NOT_FIRST_PARTY')
    tier = CausalFeeTier(fee, START-timedelta(days=61))
    fees = {t:{a:tier for a in ('BTC','ETH')} for t in evidence}
    decisions = {s:{} for s in SCENARIOS}
    for t, ev in evidence.items():
        for s in SCENARIOS:
            decisions[s][t] = fee_bound_intent(
                time=t, bars=ev['bars'], funding=ev['funding'],
                scenario=s, fee_tiers=fees[t])['decision']
    return decisions, evidence, fees


class C162NativeFeeReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decisions, cls.evidence, cls.fees = setup()

    def test_full_train_654x2_exact_replay_no_roi(self):
        result=check(self.decisions,self.evidence,self.fees)
        self.assertEqual(result['decision_scenarios_checked'],1308)
        self.assertEqual(result['asset_scenario_decisions_checked'],2616)
        self.assertFalse(result['native_fee_first_party_authenticated'])
        self.assertFalse(result['historical_economics_authorized'])

    def test_forged_positive_exposure_rejected(self):
        s=SCENARIOS[0]; t=next(iter(self.evidence))
        original=self.decisions[s][t]
        fake=Decision(t,.25,0,original.regime,original.feature_max_time,
                      original.funding_asof,original.status)
        d={**self.decisions,s:{**self.decisions[s],t:fake}}
        with self.assertRaisesRegex(ValueError,'C162_EXACT_C136_DECISION_MISMATCH'):
            check(d,self.evidence,self.fees)

    def test_fee_not_known_at_decision_rejected(self):
        t=next(iter(self.evidence)); old=self.fees[t]
        bad=CausalFeeTier(old['BTC'].evidence,t+timedelta(hours=1))
        f={**self.fees,t:{**old,'BTC':bad}}
        with self.assertRaisesRegex(ValueError,'C162_FUTURE_OR_MISSING_NATIVE_TIER'):
            check(self.decisions,self.evidence,f)

    def test_missing_decision_hour_rejected(self):
        s=SCENARIOS[0]; t=next(iter(self.evidence))
        d={**self.decisions,s:{k:v for k,v in self.decisions[s].items() if k!=t}}
        with self.assertRaisesRegex(ValueError,'C162_EXACT_FULL_TRAIN'):
            check(d,self.evidence,self.fees)

    def test_cost_scenarios_diverge_under_native_fee_hurdle(self):
        t=next(iter(self.evidence)); old=self.evidence[t]
        funding={a:[FundingFix(a,f.announced_at,f.settled_at,.004,
                               'OKX',f.instrument)
                    for f in old['funding'][a]] for a in ('BTC','ETH')}
        ev={**self.evidence,t:{**old,'funding':funding}}
        d={s:dict(self.decisions[s]) for s in SCENARIOS}
        for s in SCENARIOS:
            d[s][t]=fee_bound_intent(time=t,bars=old['bars'],funding=funding,
                                     scenario=s,fee_tiers=self.fees[t])['decision']
        self.assertEqual(d[SCENARIOS[0]][t].btc_pair_weight,.25)
        self.assertEqual(d[SCENARIOS[1]][t].btc_pair_weight,0)
        result=check(d,ev,self.fees)
        self.assertEqual(result['vetoed_asset_scenario_decisions'],2)
        swapped={s:dict(d[s]) for s in SCENARIOS}
        swapped[SCENARIOS[0]][t]=d[SCENARIOS[1]][t]
        with self.assertRaisesRegex(ValueError,'C162_EXACT_C136_DECISION_MISMATCH'):
            check(swapped,ev,self.fees)


if __name__=='__main__': unittest.main()
