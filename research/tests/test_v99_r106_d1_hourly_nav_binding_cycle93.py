"""C93 independent NAV bridge adversarial checks; synthetic TRAIN only."""
import unittest
from dataclasses import replace
from decimal import Decimal
from research.verification.independent_d1_hourly_nav_binding_cycle93 import verify_hourly_nav_binding
from research.tests.test_v99_r106_d1_hourly_native_account_cycle56 import opened_state, args
from research.tools.v99_r106_d1_hourly_native_account_cycle56 import mark_and_settle_next_hour
from research.tests.test_v99_r106_d1_two_active_cycle73 import fixture
from research.tools.v99_r106_d1_complete_hourly_router_cycle74 import advance_d1_hour


def bind_mark():
    before = opened_state(); kw = args(before)
    after, _ = mark_and_settle_next_hour(**kw)
    return dict(before=before, after=after, at=kw['at'], scenario='severe_model_only',
                spot_open=kw['spot_open'], perp_open=kw['perp_open'],
                completed_ranges=kw['completed_ranges'], contract_specs=kw['contract_specs'],
                funding_fixes=kw.get('funding_fixes'), funding_marks=kw.get('funding_marks'),
                reported_modeled_nav='1000.0')


def bind_active(mode='resize-enter', scenario='severe_model_only'):
    kw = fixture(mode); kw['scenario'] = scenario
    after, proof = advance_d1_hour(**kw)
    b = dict(before=kw['state'], after=after, at=kw['at'], scenario=scenario,
             spot_open=kw['spot_open'], perp_open=kw['perp_open'],
             completed_ranges=kw['completed_ranges'], contract_specs=kw['contract_specs'],
             funding_fixes=kw.get('funding_fixes'), funding_marks=kw.get('funding_marks'),
             transitions=kw['transitions'], reported_modeled_nav=proof['modeled_nav_quote'])
    return b


class C93NativeNAVBinding(unittest.TestCase):
    def test_mark_only_oracle(self):
        b=bind_mark()
        # Independent ledger is the source of truth, not the guessed fixture NAV.
        from research.oracles.v99_r106_d1_cycle82_independent_mark_ledger import independently_verify_mark
        p=independently_verify_mark(**{k:b[k] for k in ('before','after','at','spot_open','perp_open',
                      'completed_ranges','contract_specs','funding_fixes','funding_marks')})
        b['reported_modeled_nav']=p['nav']
        out=verify_hourly_nav_binding(**b)
        self.assertEqual(out['oracle'],'C82_MARK_ONLY_ORACLE')
        self.assertFalse(out['historical_economics_authorized'])

    def test_active_both_costs_and_three_routes(self):
        for scenario in ('severe_model_only','supersevere_model_only'):
            for mode in ('resize-enter','resize-exit','resize-resize'):
                with self.subTest(scenario=scenario,mode=mode):
                    b=bind_active(mode,scenario)
                    out=verify_hourly_nav_binding(**b)
                    self.assertEqual(out['oracle'],'C83_ACTIVE_FILL_ORACLE')
                    self.assertFalse(out['real_fills_authenticated'])

    def test_forged_hourly_nav_rejected_without_changing_trade_pf(self):
        b=bind_active()
        b['reported_modeled_nav']=str(Decimal(b['reported_modeled_nav'])+Decimal('5'))
        with self.assertRaisesRegex(ValueError,'HOURLY_NAV_UNBOUND'):
            verify_hourly_nav_binding(**b)

    def test_forged_hourly_nav_below_oracle_rejected(self):
        b=bind_active()
        b['reported_modeled_nav']=str(Decimal(b['reported_modeled_nav'])-Decimal('5'))
        with self.assertRaisesRegex(ValueError,'HOURLY_NAV_UNBOUND'):
            verify_hourly_nav_binding(**b)

    def test_missing_perp_unrealized_rejected(self):
        b=bind_active()
        nav=Decimal(b['reported_modeled_nav'])
        perp_unrealized=Decimal('0')
        for a in ('BTC','ETH'):
            spec=b['contract_specs'][a]
            contracts=Decimal(dict(b['after'].quote.perp_contracts)[a])
            base=contracts*Decimal(str(spec.contract_value_base))*Decimal(str(spec.multiplier))
            perp_unrealized+=base*(Decimal(str(b['perp_open'][a]))-
                                     Decimal(str(dict(b['after'].quote.perp_mark_anchor)[a])))
        if perp_unrealized:
            b['reported_modeled_nav']=str(nav-perp_unrealized)
            with self.assertRaisesRegex(ValueError,'HOURLY_NAV_UNBOUND'):
                verify_hourly_nav_binding(**b)
        else:
            self.skipTest('fixture had no open-vs-fill perp unrealized difference')

    def test_tampered_active_cash_rejected_by_independent_oracle(self):
        from research.tools.v99_r106_d1_stateful_quote_bridge_cycle54 import D1NativeQuoteState
        b=bind_active(); q=b['after'].quote
        corrupt=D1NativeQuoteState(str(Decimal(q.cash_quote)+Decimal('.1')),
            dict(q.spot_base),dict(q.perp_contracts),dict(q.perp_mark_anchor),q.last_fill_at)
        b['after']=replace(b['after'],quote=corrupt)
        with self.assertRaisesRegex(ValueError,'LEDGER_MISMATCH'):
            verify_hourly_nav_binding(**b)

    def test_forged_scenario_rejected_by_fee_oracle(self):
        b=bind_active();b['scenario']='supersevere_model_only'
        with self.assertRaisesRegex(ValueError,'LEDGER_MISMATCH'):
            verify_hourly_nav_binding(**b)

    def test_noncanonical_float_claim_rejected(self):
        b=bind_active();b['reported_modeled_nav']=float(b['reported_modeled_nav'])
        with self.assertRaisesRegex(ValueError,'EXACT_DECIMAL'):
            verify_hourly_nav_binding(**b)

    def test_no_promotion_even_on_valid_binding(self):
        b=bind_active(); out=verify_hourly_nav_binding(**b)
        for k in ('promotion_authorized','orders_enabled','validation_opened','final_holdout_opened'):
            self.assertFalse(out[k])

if __name__=='__main__': unittest.main()

class C93IntegratedHourlyJournal(unittest.TestCase):
    def _case(self):
        from datetime import timedelta
        from research.tools.v99_r106_d1_train_scoring_gate import Hour, Journal
        from research.verification.independent_d1_hourly_nav_binding_cycle93 import bind_two_scenario_hourly_journals
        frames={};journals={}
        for s in ('severe_model_only','supersevere_model_only'):
            b=bind_active('resize-enter',s)
            frames[s]=({k:v for k,v in b.items() if k not in ('reported_modeled_nav','scenario')},)
            h=Hour(b['at'],float(b['reported_modeled_nav']),'SIDEWAYS__LOW_VOLATILITY',
                   {k:100. for k in ('cash','passive_btc','equal_weight_btc_eth','carry_no_carry')})
            journals[s]=Journal(s,{'severe_model_only':.0007,'supersevere_model_only':.0014}[s],
                                (h,),(.01,),100.,h.benchmark_nav)
        a=frames['severe_model_only'][0]
        return bind_two_scenario_hourly_journals, dict(severe=journals['severe_model_only'],
               supersevere=journals['supersevere_model_only'],evidence_by_scenario=frames,
               start=a['at'],end=a['at']+timedelta(hours=1),fixture_only=True)

    def test_two_scenario_journal_nav_bound(self):
        f,kw=self._case();out=f(**kw)
        self.assertEqual(out['independent_native_hour_checks'],2)
        self.assertFalse(out['historical_economics_authorized'])

    def test_scorer_nav_spoof_rejected(self):
        from dataclasses import replace
        f,kw=self._case(); j=kw['severe']; h=j.hours[0]
        kw['severe']=replace(j,hours=(replace(h,nav=h.nav+1.),))
        with self.assertRaisesRegex(ValueError,'HOURLY_NAV_UNBOUND'):
            f(**kw)

    def test_exogenous_scenario_price_divergence_rejected(self):
        f,kw=self._case(); e=kw['evidence_by_scenario']
        bad=dict(e['supersevere_model_only'][0]);bad['spot_open']=dict(bad['spot_open'],BTC='999')
        kw['evidence_by_scenario']=dict(e,supersevere_model_only=(bad,))
        with self.assertRaisesRegex(ValueError,'EXOGENOUS_DIVERGENCE'):
            f(**kw)

    def test_partial_evidence_rejected(self):
        f,kw=self._case();kw['evidence_by_scenario']['severe_model_only']=()
        with self.assertRaisesRegex(ValueError,'COVERAGE_REQUIRED'):
            f(**kw)

    def test_nonfixture_short_window_rejected(self):
        f,kw=self._case();kw['fixture_only']=False
        with self.assertRaisesRegex(ValueError,'NONFROZEN_SCORING'):
            f(**kw)
