"""C161 adversarial synthetic feature binding tests; never market ROI."""
import unittest
from datetime import timedelta
from research.tools.v99_r106_d1_full_train_guard import START, HOURS
from research.tools.v99_r106_d1_basis_carry_preregistered import Decision, PairedBar, FundingFix
from research.verification.independent_d1_c148_risk_fold_scorecard import SCENARIOS
from research.verification.independent_d1_c161_causal_decision_oracle import (
    check_causal_decision_evidence, verify_c161_integrated_structural_only)

ASSETS=('BTC','ETH')


def fixture():
    marks={a:{'spot':'100','perp':'100'} for a in ASSETS}
    cash={'cash_quote':'1000','spot_base':{a:'0' for a in ASSETS},
          'perp_base':{a:'0' for a in ASSETS}}
    schedule={a:[] for a in ASSETS}; frames=[]
    for i in range(HOURS):
        t=START+timedelta(hours=i); funding=[]
        if i%8==0:
            for a in ASSETS:
                schedule[a].append(t)
                funding.append({'asset':a,'time':t,'rate':'0',
                                'source':'OKX','instrument':a+'-USDT-SWAP'})
        frames.append({'time':t,'marks':marks,'funding':funding,
                       'before':cash,'after_mark':cash,'after_funding':cash,
                       'after':cash,'fills':[]})
    decisions={}; evidence={}
    for i in range(168,HOURS,24):
        t=START+timedelta(hours=i)
        decisions[t]=Decision(t,0,0,'SIDEWAYS__LOW_VOLATILITY',
                              t-timedelta(hours=1),t-timedelta(hours=1),
                              'PREREGISTERED_RESEARCH_INTENT_ONLY')
        evidence[t]={'bars':{a:[PairedBar(frames[j]['time'],a,100.,100.,
                                      'OKX','OKX',frames[j]['time'])
                                  for j in range(i-168,i)] for a in ASSETS},
                     'funding':{a:[FundingFix(a,tt,tt,0.,'OKX',a+'-USDT-SWAP')
                                   for tt in schedule[a] if tt<t][-3:] for a in ASSETS}}
    proof={'hours_replayed':HOURS,'fills_replayed':0,
           'funding_events_modeled':3966,
           'perp_variation_margin_quote':'0','modeled_funding_quote':'0',
           'modeled_native_plus_stress_fees_quote':'0',
           'last_declared_account_state':cash,'modeled_net_nav_delta_quote':'0'}
    journals={s:{'frames':frames,'account_proof':proof,
                 'c146_full_feature_funding_proof':{'decision_hours_checked':654}}
              for s in SCENARIOS}
    return journals,{s:decisions for s in SCENARIOS},schedule,marks,evidence


class C161CausalDecisionOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.j,cls.d,cls.schedule,cls.marks,cls.ev=fixture()

    def test_full_train_causal_binding_and_integrated_accounting(self):
        r=verify_c161_integrated_structural_only(
            self.j,self.d,self.schedule,self.marks,
            START-timedelta(hours=1),self.ev)
        p=r['c161_causal_feature_check']
        self.assertEqual(p['asset_hour_pairs_checked'],219744)
        self.assertEqual(p['last_three_funding_fixes_checked'],3924)
        self.assertEqual(p['decision_hours_checked'],654)
        self.assertFalse(r['historical_roi_authorized'])
        self.assertFalse(p['fee_veto_exactly_reexecuted'])

    def test_forged_early_feature_rejected_even_if_last_bar_matches(self):
        t=next(iter(self.ev)); old=self.ev[t]
        bars={**old['bars'],'BTC':list(old['bars']['BTC'])}
        original=bars['BTC'][0]
        bars['BTC'][0]=PairedBar(original.time,'BTC',101.,100.,'OKX','OKX',original.time)
        ev={**self.ev,t:{**old,'bars':bars}}
        with self.assertRaisesRegex(ValueError,'C161_EARLY_FEATURE_BAR_MISMATCH'):
            check_causal_decision_evidence(self.j,self.d,ev)

    def test_forged_last_funding_fix_rejected(self):
        t=next(iter(self.ev)); old=self.ev[t]
        fixes={**old['funding'],'ETH':list(old['funding']['ETH'])}
        f=fixes['ETH'][-1]
        fixes['ETH'][-1]=FundingFix('ETH',f.announced_at,f.settled_at,.002,'OKX',f.instrument)
        ev={**self.ev,t:{**old,'funding':fixes}}
        with self.assertRaisesRegex(ValueError,'C161_SETTLED_FUNDING_MISMATCH'):
            check_causal_decision_evidence(self.j,self.d,ev)

    def test_positive_exposure_without_funding_edge_rejected(self):
        t=next(iter(self.ev)); modified={}
        for s in SCENARIOS:
            original=self.d[s]
            modified[s]={**original,t:Decision(t,.25,0,'SIDEWAYS__LOW_VOLATILITY',
                         t-timedelta(hours=1),t-timedelta(hours=1),
                         'PREREGISTERED_RESEARCH_INTENT_ONLY')}
        with self.assertRaisesRegex(ValueError,'C161_UNSUPPORTED_POSITIVE_EXPOSURE'):
            check_causal_decision_evidence(self.j,modified,self.ev)

    def test_forged_regime_rejected_even_when_both_cost_paths_agree(self):
        t=next(iter(self.ev)); modified={}
        for s in SCENARIOS:
            original=self.d[s]
            modified[s]={**original,t:Decision(t,0,0,'BULL__LOW_VOLATILITY',
                         t-timedelta(hours=1),t-timedelta(hours=1),
                         'PREREGISTERED_RESEARCH_INTENT_ONLY')}
        with self.assertRaisesRegex(ValueError,'C161_REGIME_OR_CAUSAL_DECISION_MISMATCH'):
            check_causal_decision_evidence(self.j,modified,self.ev)

    def test_missing_decision_evidence_rejected(self):
        t=next(iter(self.ev)); ev={k:v for k,v in self.ev.items() if k!=t}
        with self.assertRaisesRegex(ValueError,'C161_EXACT_654_DECISION_EVIDENCE_REQUIRED'):
            check_causal_decision_evidence(self.j,self.d,ev)


if __name__=='__main__':unittest.main()
