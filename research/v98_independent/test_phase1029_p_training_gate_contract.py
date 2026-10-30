#!/usr/bin/env python3
"""P 90-cell growth decision oracle with synthetic receipt fixtures only."""
import ast,copy,math,unittest
from pathlib import Path
SRC=Path(__file__).with_name('phase1029_p_training_gate.py').read_text()
fn=next(x for x in ast.parse(SRC).body if isinstance(x,ast.FunctionDef) and x.name=='growth_gate')
namespace={'math':math,'PATHS':('P_core_only','P_full','P_minus_opportunity','P_minus_relative_value','P_minus_recovery'),
           'FEE_TIERS':{'base':.0007,'severe':.0012,'supersevere':.002},
           'ORDERS':('carried_before_fill','new_after_fill'),
           'CAPITAL_MODES':{'immediate':1e6,'capacity_1m':1e6,'capacity_10m':1e7}}
exec(compile(ast.Module(body=[fn],type_ignores=[]),'<P-growth-gate>','exec'),namespace)
growth_gate=namespace['growth_gate']

def matrix():
    cases={}
    for p in namespace['PATHS']:
        cases[p]={}
        for fee in namespace['FEE_TIERS']:
            cases[p][fee]={}
            for order in namespace['ORDERS']:
                cases[p][fee][order]={}
                for mode in namespace['CAPITAL_MODES']:
                    wealth=.20 if p=='P_full' else .10
                    cases[p][fee][order][mode]={'survived':True,'folds':{
                        '2023':{'days':365,'log_wealth':wealth},
                        '2024':{'days':366,'log_wealth':wealth}}}
    return {'cells_attempted':90,'cells_survived':90,'failures':[],'cases':cases}

class PTrainingGate(unittest.TestCase):
    def test_90_cell_growth_pass(self):
        self.assertTrue(growth_gate(matrix())['passed'])
    def test_failed_survival_rejected(self):
        m=matrix();m['failures'].append({'reason':'INTRABAR'})
        self.assertFalse(growth_gate(m)['passed'])
    def test_nonpositive_marginal_rejected(self):
        m=matrix();m['cases']['P_minus_recovery']['base']['carried_before_fill']['immediate']['folds']['2023']['log_wealth']=.30
        self.assertFalse(growth_gate(m)['passed'])
    def test_incomplete_fold_rejected(self):
        m=matrix();m['cases']['P_full']['base']['carried_before_fill']['immediate']['folds']['2024']['days']=365
        self.assertFalse(growth_gate(m)['passed'])
    def test_supersevere_survival_required(self):
        m=matrix();m['failures'].append({'path':'P_full','tier':'supersevere'})
        self.assertFalse(growth_gate(m)['passed'])

if __name__=='__main__':unittest.main()
