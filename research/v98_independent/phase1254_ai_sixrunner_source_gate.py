#!/usr/bin/env python3
"""V98 AI1254 six independent runner exact source hash and numeric audit."""
from __future__ import annotations
import argparse
import glob
import json
from phase1253_ai_crossos_numeric_forensics import compare, SOURCE_NAMES

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input-glob',required=True)
    p.add_argument('--output',default='ai1254_sixrunner.json')
    args=p.parse_args()
    files=sorted(glob.glob(args.input_glob))
    if len(files)!=6:
        raise ValueError('AI1254_EXPECT_SIX_RECEIPTS:'+str(files))
    loaded=[]
    for path in files:
        with open(path) as f: data=json.load(f)
        loaded.append((path,data))
    ref=loaded[0][1]
    outcome={'phase':1254,'synthetic_only':True,
             'historical_system_pnl_computed':False,
             'runner_files':files,'comparisons':[],
             'exact_source_hash_pass':True,'numeric_pass':True}
    for path,item in loaded[1:]:
        audit=compare(ref,item)
        exact=True
        for label in ('benign','crisis'):
            for name in SOURCE_NAMES:
                if (ref['fixtures'][label]['raw_sha'][name] !=
                    item['fixtures'][label]['raw_sha'][name]):
                    exact=False
            if (ref['fixtures'][label]['state_sha'] !=
                item['fixtures'][label]['state_sha']):
                exact=False
        outcome['comparisons'].append({
            'path':path,'exact_raw_sha':exact,
            'numeric_diagnostic_pass':audit['numeric_diagnostic_pass'],
            'detail':audit['fixtures']})
        outcome['exact_source_hash_pass'] &= exact
        outcome['numeric_pass'] &= audit['numeric_diagnostic_pass']
        for label,fixture in audit['fixtures'].items():
            for name,v in fixture['sources'].items():
                if not v['raw_hash_equal'] or v['different_elements']:
                    print('AI1254_DIFFERENCE',path,label,name,
                          'different_elements',v['different_elements'],
                          'max_abs_diff',v['max_abs_diff'],
                          'first_differences',v['first_differences'],
                          'rounded_hash_equal',v['rounded_hash_equal'])
        print('AI1254_PAIR',path,'exact',exact,
              'numeric',audit['numeric_diagnostic_pass'])
    outcome['decision']=(
        'PASS_AI_SIX_RUNNER_EXACT_SOURCE_ONLY_NOT_ECONOMIC'
        if outcome['exact_source_hash_pass'] and outcome['numeric_pass']
        else 'FAIL_AI_SIX_RUNNER_SOURCE_REPRODUCIBILITY')
    with open(args.output,'w') as f:
        json.dump(outcome,f,sort_keys=True,indent=2,allow_nan=False)
    print('AI1254_DECISION',outcome['decision'])
    print('AI1254_SIX_RUNNERS',len(files))
    if not outcome['decision'].startswith('PASS'):
        raise SystemExit(2)

if __name__=='__main__':
    main()
