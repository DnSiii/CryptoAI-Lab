"""Synthetic C140 multi-hour ledger tests; NEVER ROI or exchange receipts."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from decimal import Decimal
import unittest
from research.tools.v99_r106_d1_c140_hourly_journal import build_journal
from research.tools.v99_r106_d1_basis_carry_preregistered import Decision, PairedBar, FundingFix, FeeEvidence
from research.tools.v99_r106_d1_native_fee_veto_cycle136 import fee_bound_intent, CausalFeeTier

START=datetime(2023,9,28,tzinfo=timezone.utc)
BASE_MARKS={'BTC':{'spot':'100','perp':'101'},'ETH':{'spot':'50','perp':'51'}}
INITIAL={'cash_quote':'1000','spot_base':{'BTC':'0','ETH':'0'},'perp_base':{'BTC':'0','ETH':'0'}}
SCHEDULE={a:[{'start':datetime(2021,12,9,tzinfo=timezone.utc),
              'end':datetime(2023,10,1,tzinfo=timezone.utc),
              'spot_taker':'0.001','perp_taker':'0.0005',
              'spot_fee_currency':'BASE' if a=='BTC' else 'QUOTE',
              'account_tier':'SYNTHETIC_NOT_AUTHENTICATED',
              'observed_at':datetime(2021,12,8,tzinfo=timezone.utc)}] for a in ('BTC','ETH')}

def build_inputs(hours=48):
    rows=[]
    expected={a:[] for a in ('BTC','ETH')}
    for i in range(hours):
        t=START+timedelta(hours=i)
        marks={'BTC':{'spot':str(100+Decimal(i)/100),'perp':str(101+Decimal(i)/100)},
               'ETH':{'spot':str(50+Decimal(i)/200),'perp':str(51+Decimal(i)/200)}}
        funding=[]
        if t.hour in (0,8,16):
            for a in ('BTC','ETH'):
                expected[a].append(t)
                funding.append({'asset':a,'time':t,'rate':'0.0002',
                                'source':'OKX','instrument':a+'-USDT-SWAP'})
        rows.append({'time':t,'marks':marks,'funding':funding})
    decisions={}
    for i in range(0,hours,24):
        t=START+timedelta(hours=i)
        decisions[t]=Decision(t,.25,.25,'SIDEWAYS__LOW_VOLATILITY',
                              t-timedelta(hours=1),t-timedelta(hours=1),
                              'C136_FEE_VETO_MODEL_ONLY_NO_ROI')
    return {'rows':rows,'decisions':decisions,'expected_funding_schedule':expected,
            'initial_marks':BASE_MARKS,'initial_marks_time':START-timedelta(hours=1),
            'initial_state':deepcopy(INITIAL),'native_fee_schedule':deepcopy(SCHEDULE)}

class TestC140(unittest.TestCase):
    def run_case(self,scenario='severe_model_only',**changes):
        inp=build_inputs();inp.update(changes)
        return build_journal(scenario=scenario,**inp)
    def test_48h_both_scenarios_independent_replay(self):
        for scenario in ('severe_model_only','supersevere_model_only'):
            r=self.run_case(scenario)
            self.assertEqual(r['account_proof']['hours_replayed'],48)
            self.assertEqual(r['funding_proof']['observed_fixes'],12)
            self.assertEqual(r['account_proof']['funding_events_modeled'],12)
            self.assertGreaterEqual(r['account_proof']['fills_replayed'],4)
            self.assertFalse(r['economic_roi_authorized'])
            self.assertFalse(r['orders_enabled'])
    def test_no_validation(self):
        inp=build_inputs(hours=73)
        with self.assertRaisesRegex(ValueError,'SEALED'):
            build_journal(scenario='severe_model_only',**inp)
    def test_missing_funding_fix(self):
        inp=build_inputs();inp['rows'][8]['funding']=[]
        with self.assertRaisesRegex(ValueError,'FUNDING_FIX'):
            build_journal(scenario='severe_model_only',**inp)
    def test_invented_funding_fix(self):
        inp=build_inputs();inp['rows'][1]['funding']=[{'asset':'BTC','time':START+timedelta(hours=1),
            'rate':'0.0002','source':'OKX','instrument':'BTC-USDT-SWAP'}]
        with self.assertRaisesRegex(ValueError,'FUNDING_FIX'):
            build_journal(scenario='severe_model_only',**inp)
    def test_fee_asof_future_rejected(self):
        inp=build_inputs();inp['native_fee_schedule']['BTC'][0]['observed_at']=START
        with self.assertRaisesRegex(ValueError,'FEE_NOT_KNOWN'):
            build_journal(scenario='severe_model_only',**inp)
    def test_future_decision_rejected(self):
        inp=build_inputs();t=START
        # Bypass Decision constructor to ensure the journal independently rejects tampering.
        forged=object.__new__(Decision)
        for key,value in {'time':t,'btc_pair_weight':.25,'eth_pair_weight':.25,
                          'regime':'SIDEWAYS__LOW_VOLATILITY','feature_max_time':t,
                          'funding_asof':t,'status':'C136_FEE_VETO_MODEL_ONLY_NO_ROI'}.items():
            object.__setattr__(forged,key,value)
        inp['decisions'][t]=forged
        with self.assertRaisesRegex(ValueError,'NONCAUSAL'):
            build_journal(scenario='severe_model_only',**inp)
    def test_hourly_gap_rejected(self):
        inp=build_inputs();inp['rows'].pop(4)
        with self.assertRaisesRegex(ValueError,'NONCONTIGUOUS'):
            build_journal(scenario='severe_model_only',**inp)
    def test_preregistered_c136_decision_to_c139_to_c129_replay(self):
        # Entire causal chain on SYNTHETIC history; no source authentication.
        inp=build_inputs()
        bars={}
        funding={}
        for a in ('BTC','ETH'):
            px=100 if a=='BTC' else 50
            bars[a]=[PairedBar(START-timedelta(hours=168-i),a,px,px*1.005,
                               'OKX','OKX',START-timedelta(hours=168-i))
                     for i in range(168)]
            funding[a]=[FundingFix(a,START-timedelta(hours=h),
                                   START-timedelta(hours=h),.01,'OKX',a+'-USDT-SWAP')
                        for h in (24,16,8)]
        fee=FeeEvidence('OKX',.001,.0005,datetime(2021,12,9,tzinfo=timezone.utc),
                        datetime(2023,10,1,tzinfo=timezone.utc),'SYNTHETIC_NOT_AUTHENTICATED')
        tiers={a:CausalFeeTier(fee,START-timedelta(hours=169)) for a in ('BTC','ETH')}
        for scenario in ('severe_model_only','supersevere_model_only'):
            intent=fee_bound_intent(time=START,bars=bars,funding=funding,
                                    scenario=scenario,fee_tiers=tiers)
            self.assertEqual(intent['decision'].btc_pair_weight,.25)
            inp['decisions'][START]=intent['decision']
            r=build_journal(scenario=scenario,**inp)
            self.assertEqual(r['account_proof']['hours_replayed'],48)
            self.assertEqual(r['account_proof']['funding_events_modeled'],12)
            self.assertFalse(r['economic_roi_authorized'])
            self.assertFalse(intent['historical_economics_authorized'])

    def test_six_regime_contract_rejects_unknown(self):
        inp=build_inputs();t=START
        inp['decisions'][t]=Decision(t,.25,.25,'UNKNOWN_REGIME',
                                   t-timedelta(hours=1),t-timedelta(hours=1),
                                   'C136_FEE_VETO_MODEL_ONLY_NO_ROI')
        with self.assertRaisesRegex(ValueError,'NONCAUSAL_OR_UNFROZEN'):
            build_journal(scenario='severe_model_only',**inp)

    def test_cash_margin_call_rejected(self):
        inp=build_inputs()
        inp['rows'][1]['marks']['BTC']['perp']='10000000'
        with self.assertRaisesRegex(ValueError,'NEGATIVE_CASH'):
            build_journal(scenario='severe_model_only',**inp)
    def test_decision_outside_rows_rejected(self):
        inp=build_inputs();t=START-timedelta(hours=24)
        inp['decisions'][t]=Decision(t,0,0,'SIDEWAYS__LOW_VOLATILITY',t-timedelta(hours=1),t-timedelta(hours=1),'C136_FEE_VETO_MODEL_ONLY_NO_ROI')
        with self.assertRaisesRegex(ValueError,'UNUSED'):
            build_journal(scenario='severe_model_only',**inp)

if __name__=='__main__': unittest.main()
