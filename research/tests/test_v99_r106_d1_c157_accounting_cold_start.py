"""C157 independent remote regression: C149/C150 accounting and cold start.
Synthetic fixtures only. No exchange data, ROI, validation, holdout or orders.
"""
import unittest
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal

from research.tools.v99_r106_d1_full_train_guard import START
from research.verification.independent_d1_c149_account_oracle import oracle
from research.verification.independent_d1_c150_cold_start_oracle import cold_start_oracle


def st(cash='1000', btc_spot='0', btc_perp='0'):
    return {'cash_quote': str(cash), 'spot_base': {'BTC': str(btc_spot), 'ETH':'0'},
            'perp_base': {'BTC': str(btc_perp), 'ETH':'0'}}


def fixture(scenario, trade=False, inherited=False):
    marks = {a: {'spot':'100','perp':'100'} for a in ('BTC','ETH')}
    t0 = START - timedelta(hours=1)
    initial = st('1000', '1' if inherited else '0', '-1' if inherited else '0')
    frames = []
    for i in range(168):
        row = {'time': START + timedelta(hours=i), 'marks': deepcopy(marks),
               'before':deepcopy(initial), 'after_mark':deepcopy(initial),
               'after_funding':deepcopy(initial), 'after':deepcopy(initial),
               'fills':[], 'funding':[]}
        frames.append(row)
    fees = Decimal('0')
    if trade:
        stress = Decimal('.0007' if scenario=='severe_model_only' else '.0014')
        one_fee = Decimal('100') * stress
        fees = one_fee * 2
        before = deepcopy(initial)
        after_spot = st(Decimal('900')-one_fee, '1', '0')
        after_perp = st(Decimal('900')-fees, '1', '-1')
        t = START + timedelta(hours=168)
        def fill(leg, side, a, b):
            return {'time':t,'asset':'BTC','leg':leg,'side':side,
                    'base_quantity':'1','execution_price_quote_per_base':'100',
                    'quote_notional':'100','native_fee_quote':'0',
                    'stress_fee_quote':str(one_fee),'base_fee_units':'0',
                    'booked_total_fee_quote':str(one_fee),
                    'before':a,'after':b}
        frames.append({'time':t,'marks':deepcopy(marks),
                       'before':before,'after_mark':deepcopy(before),
                       'after_funding':deepcopy(before),'after':deepcopy(after_perp),
                       'fills':[fill('spot','buy',before,after_spot),
                                fill('perp','sell',after_spot,after_perp)],
                       'funding':[]})
        last = after_perp
    else:
        last = initial
    journal = {'frames':frames,'account_proof':{
        'hours_replayed':len(frames),'fills_replayed':2 if trade else 0,
        'funding_events_modeled':0,'perp_variation_margin_quote':'0',
        'modeled_funding_quote':'0',
        'modeled_native_plus_stress_fees_quote':str(fees),
        'last_declared_account_state':deepcopy(last),
        'modeled_net_nav_delta_quote':str(-fees)}}
    return journal, marks, t0


class IndependentLedgerC157(unittest.TestCase):
    def audit(self, j, m, t, scenario='severe_model_only'):
        return cold_start_oracle(j, m, t, scenario)

    def test_two_scenarios_independently_accounted(self):
        for scenario in ('severe_model_only','supersevere_model_only'):
            with self.subTest(scenario=scenario):
                j,m,t = fixture(scenario,trade=True)
                result=self.audit(j,m,t,scenario)
                self.assertEqual(result['hours'],169)
                self.assertEqual(result['modeled_fills'],2)
                self.assertEqual(result['max_accounting_residual'],'0')
                self.assertEqual(result['flat_warmup_hours_verified'],168)
                for flag in ('exchange_authenticated','historical_roi_authorized',
                             'validation_opened','holdout_opened','promotion_authorized',
                             'orders_enabled'):
                    self.assertFalse(result[flag])

    def test_balanced_inherited_position_old_oracle_accepts_cold_start_rejects(self):
        j,m,t=fixture('severe_model_only',inherited=True)
        self.assertEqual(oracle(j,m,t,'severe_model_only')['max_accounting_residual'],'0')
        with self.assertRaisesRegex(ValueError,'C150_INHERITED_POSITION'):
            self.audit(j,m,t)

    def test_early_fill_rejected(self):
        j,m,t=fixture('severe_model_only')
        j['frames'][0]['fills'].append({'invalid':'early'})
        with self.assertRaisesRegex(ValueError,'C150_PREDECISION_FILL'):
            self.audit(j,m,t)

    def test_warmup_capital_forgery_rejected(self):
        j,m,t=fixture('severe_model_only')
        j['frames'][5]['after']['cash_quote']='999'
        with self.assertRaisesRegex(ValueError,'C150_WARMUP_CAPITAL'):
            self.audit(j,m,t)

    def test_wrong_scenario_fee_rejected(self):
        j,m,t=fixture('severe_model_only',trade=True)
        with self.assertRaisesRegex(ValueError,'C149_FILL_FEE_OR_MARK'):
            self.audit(j,m,t,'supersevere_model_only')

    def test_fee_tampering_rejected(self):
        j,m,t=fixture('severe_model_only',trade=True)
        j['frames'][-1]['fills'][0]['stress_fee_quote']='0'
        with self.assertRaisesRegex(ValueError,'C149_FILL_FEE_OR_MARK'):
            self.audit(j,m,t)

    def test_missing_hour_rejected(self):
        j,m,t=fixture('severe_model_only')
        j['frames'][12]['time']+=timedelta(hours=1)
        with self.assertRaisesRegex(ValueError,'C150_WARMUP_TIME_GAP'):
            self.audit(j,m,t)

    def test_full_train_not_faked_by_short_fixture(self):
        j,m,t=fixture('severe_model_only')
        with self.assertRaisesRegex(ValueError,'C150_FULL_TRAIN_BOUNDARY'):
            cold_start_oracle(j,m,t,'severe_model_only',full_train=True)

    def test_wrong_summary_proof_rejected(self):
        j,m,t=fixture('severe_model_only',trade=True)
        j['account_proof']['modeled_native_plus_stress_fees_quote']='0'
        with self.assertRaisesRegex(ValueError,'C149_SUMMARY_PROOF'):
            self.audit(j,m,t)

    def test_cash_inventory_chain_break_rejected(self):
        j,m,t=fixture('severe_model_only',trade=True)
        j['frames'][-1]['fills'][1]['before']['cash_quote']='999'
        with self.assertRaisesRegex(ValueError,'C149_FILL_CHAIN'):
            self.audit(j,m,t)

    def test_sealed_partition_and_no_promotion_contract(self):
        from research.tools.v99_r106_d1_basis_carry_preregistered import report_permissions
        p=report_permissions()
        for k in ('historical_train_economics_run','validation_opened',
                  'final_holdout_opened','promotion_authorized',
                  'real_orders_enabled','paper_publication_authorized'):
            self.assertFalse(p[k])


if __name__=='__main__':
    unittest.main()
