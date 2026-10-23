"""C158 15,864-hour synthetic scorecard integration and adversarial controls."""
import unittest
from datetime import timedelta
from research.tools.v99_r106_d1_full_train_guard import START, HOURS
from research.tools.v99_r106_d1_basis_carry_preregistered import Decision
from research.verification.independent_d1_c148_risk_fold_scorecard import (
    score_full_train_model_only, SCENARIOS)


def fixture():
    marks={a:{'spot':'100','perp':'100'} for a in ('BTC','ETH')}
    account={'cash_quote':'1000','spot_base':{'BTC':'0','ETH':'0'},
             'perp_base':{'BTC':'0','ETH':'0'}}
    frames=[{'time':START+timedelta(hours=i),'marks':marks,'funding':[],
             'before':account,'after':account} for i in range(HOURS)]
    decisions={START+timedelta(hours=i):Decision(
        START+timedelta(hours=i),0,0,'SIDEWAYS__LOW_VOLATILITY',
        START+timedelta(hours=i-1),START+timedelta(hours=i-1),
        'PREREGISTERED_RESEARCH_INTENT_ONLY') for i in range(168,HOURS,24)}
    journals={s:{'frames':list(frames),
        'c146_full_feature_funding_proof':{'decision_hours_checked':654},
        'account_proof':{'hours_replayed':HOURS}} for s in SCENARIOS}
    return journals,{s:dict(decisions) for s in SCENARIOS}


class RiskFoldC158(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.j,cls.d=fixture()

    def test_full_train_five_fold_both_scenarios_are_model_only(self):
        r=score_full_train_model_only(self.j,self.d)
        self.assertEqual(r['hours'],15864)
        self.assertEqual(r['daily_decisions'],654)
        self.assertEqual(r['fold_hours'],[3172,3173,3173,3173,3173])
        self.assertFalse(r['all_six_regimes_observed'])
        self.assertEqual(sum(r['regime_counts'].values()),654)
        for s in SCENARIOS:
            self.assertEqual(r['scenarios'][s]['model_only_positive_folds'],0)
            self.assertEqual(r['scenarios'][s]['model_only_max_drawdown'],'0')
        for key in ('exchange_authenticated','historical_roi_authorized',
                    'promotion_authorized','validation_opened','holdout_opened',
                    'orders_enabled'):
            self.assertFalse(r[key])

    def test_exogenous_price_mismatch_fails_closed(self):
        j={s:dict(v) for s,v in self.j.items()}
        j[SCENARIOS[1]]['frames']=list(j[SCENARIOS[1]]['frames'])
        fr=dict(j[SCENARIOS[1]]['frames'][500])
        fr['marks']={a:dict(v) for a,v in fr['marks'].items()}
        fr['marks']['BTC']['spot']='101'
        j[SCENARIOS[1]]['frames'][500]=fr
        with self.assertRaisesRegex(ValueError,'C148_EXOGENOUS'):
            score_full_train_model_only(j,self.d)

    def test_missing_cost_path_rejected(self):
        with self.assertRaisesRegex(ValueError,'C148_BOTH_SCENARIOS'):
            score_full_train_model_only({SCENARIOS[0]:self.j[SCENARIOS[0]]},self.d)

    def test_noncausal_decision_rejected(self):
        ds={s:dict(v) for s,v in self.d.items()}
        t=next(iter(ds[SCENARIOS[1]]))
        bad=Decision(t,0,0,'SIDEWAYS__LOW_VOLATILITY',
                     t-timedelta(hours=1),t-timedelta(hours=1),
                     'PREREGISTERED_RESEARCH_INTENT_ONLY')
        object.__setattr__(bad,'feature_max_time',t)
        ds[SCENARIOS[1]][t]=bad
        with self.assertRaises(ValueError):
            score_full_train_model_only(self.j,ds)

    def test_shortened_train_rejected(self):
        j={s:dict(v) for s,v in self.j.items()}
        j[SCENARIOS[0]]['frames']=j[SCENARIOS[0]]['frames'][:-1]
        with self.assertRaisesRegex(ValueError,'C148_INCOMPLETE_TRAIN'):
            score_full_train_model_only(j,self.d)

if __name__=='__main__':
    unittest.main()
