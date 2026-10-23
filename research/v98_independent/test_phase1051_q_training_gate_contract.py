import unittest
from pathlib import Path
from unittest.mock import patch
from phase1051_q_training_gate import growth_gate,verify_freeze,PATHS,FEE_TIERS,ORDERS,CAPITAL_MODES


def fake_matrix(full=2.,alt=1.,breach=False):
    cases={}
    for name in PATHS:
        cases[name]={}
        for tier in FEE_TIERS:
            cases[name][tier]={}
            for order in ORDERS:
                cases[name][tier][order]={}
                for mode in CAPITAL_MODES:
                    val=full if name=='Q_full' else alt
                    cases[name][tier][order][mode]={'survived':True,'folds':{
                        '2023':{'days':365,'log_wealth':val},
                        '2024':{'days':366,'log_wealth':val}}}
    return {'cells_attempted':90,'cells_survived':90 if not breach else 89,
            'failures':[] if not breach else [{'reason':'synthetic_breach'}],
            'cases':cases}

class QGateTests(unittest.TestCase):
    def test_all_five_paths_positive_marginal(self):
        self.assertTrue(growth_gate(fake_matrix())['passed'])
    def test_reject_nonpositive_marginal(self):
        self.assertFalse(growth_gate(fake_matrix(full=1,alt=2))['passed'])
    def test_reject_one_failed_cell(self):
        self.assertEqual(growth_gate(fake_matrix(breach=True))['reason'],'incomplete_or_failed_survival')
    def test_reject_incomplete_fold(self):
        m=fake_matrix();m['cases']['Q_full']['base']['carried_before_fill']['immediate']['folds']['2024']['days']=365
        self.assertFalse(growth_gate(m)['passed'])
    def test_no_manifest_fails_closed(self):
        with patch('phase1051_q_training_gate.MANIFEST',Path('/tmp/v98_q_nonexistent_manifest_1051.json')):
            with self.assertRaises(PermissionError):verify_freeze()

if __name__=='__main__':unittest.main()
