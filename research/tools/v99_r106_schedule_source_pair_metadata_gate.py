"""Read-only GitHub Actions metadata triage; never proves native bytes or PnL.

An OKX market ZIP and terms ZIP from separate scheduled workflow runs are NOT
an atomic observation, even if their run timestamps share a UTC hour.
Only the dedicated same-job atomic workflow can be an attestation candidate.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ATOMIC = 'V99 R106 atomic paired OKX market and terms DATA_ONLY'
SPLIT = 'V99 R106 hourly first-party OKX source-only receipts'
PREFIX = {'market': 'v99-r106-hourly-okx-', 'terms': 'v99-r106-hourly-terms-'}
SPLIT_PREFIX = {'market': 'v99-r106-okx-firstparty-', 'terms': 'v99-r106-okx-terms-'}


def utc_hour(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value):
        raise ValueError('invalid_run_utc_timestamp')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo != timezone.utc:
        raise ValueError('non_utc_timestamp')
    return dt.strftime('%Y-%m-%dT%H')


def valid_artifacts(run_id, artifacts, prefixes):
    if not isinstance(artifacts, list):
        raise ValueError('missing_artifact_listing')
    found = {}
    for typ, prefix in prefixes.items():
        matches = [a for a in artifacts if isinstance(a, dict)
                   and a.get('name') == prefix + str(run_id)]
        if len(matches) > 1:
            raise ValueError('duplicate_source_artifact:' + typ)
        if not matches:
            continue
        a = matches[0]
        if (a.get('expired') is not False or type(a.get('id')) is not int
                or a['id'] <= 0 or type(a.get('size_in_bytes')) is not int
                or a['size_in_bytes'] <= 0
                or (a.get('workflow_run') is not None and
                    a['workflow_run'].get('id') != run_id)):
            raise ValueError('invalid_source_artifact:' + typ)
        found[typ] = a['id']
    if len(found) == 2 and found['market'] == found['terms']:
        raise ValueError('same_artifact_id_two_streams')
    return found


def audit(runs, artifact_lookup):
    if not isinstance(runs, list):
        raise ValueError('invalid_run_listing')
    atomic_candidates = []
    split_by_hour = {}
    seen_runs = set()
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError('invalid_run_metadata')
        if (run.get('name') not in (ATOMIC, SPLIT)
                or run.get('event') != 'schedule'
                or run.get('head_branch') != 'main'
                or run.get('status') != 'completed'
                or run.get('conclusion') != 'success'):
            continue
        rid = run.get('id')
        if type(rid) is not int or rid <= 0 or rid in seen_runs:
            raise ValueError('duplicate_or_invalid_source_run_id')
        seen_runs.add(rid)
        hour = utc_hour(run.get('created_at'))
        artifacts = artifact_lookup(rid)
        if run['name'] == ATOMIC:
            found = valid_artifacts(rid, artifacts, PREFIX)
            if set(found) == {'market', 'terms'}:
                atomic_candidates.append({'run_id': rid, 'created_hour_utc': hour,
                                          'market_artifact_id': found['market'],
                                          'terms_artifact_id': found['terms'],
                                          'status': 'UNVERIFIED_ATOMIC_METADATA_CANDIDATE'})
            elif found:
                raise ValueError('incomplete_atomic_source_run:' + str(rid))
        else:
            found = valid_artifacts(rid, artifacts, SPLIT_PREFIX)
            if found:
                by_stream = split_by_hour.setdefault(hour, {'market': [], 'terms': []})
                for typ, aid in found.items():
                    by_stream[typ].append({'run_id': rid, 'artifact_id': aid})
    collisions = [{'created_hour_utc': hour, 'market': streams['market'],
                   'terms': streams['terms'],
                   'reason': 'DISTINCT_RUNS_NOT_ATOMIC'}
                  for hour, streams in sorted(split_by_hour.items())
                  if streams['market'] and streams['terms']
                  and not set(x['run_id'] for x in streams['market'])
                          .intersection(x['run_id'] for x in streams['terms'])]
    return {'schema': 'V99_R106_ACTIONS_SOURCE_METADATA_GATE_V1',
            'status': 'DATA_ONLY_METADATA_TRIAGE_NO_SOURCE_CONTINUITY_CLAIM',
            'atomic_metadata_candidates': atomic_candidates,
            'split_run_same_created_hour_collisions': collisions,
            'created_hour_is_not_acquisition_hour': True,
            'requires_original_zip_sha_and_native_tminus1_attestation': True,
            'requires_two_adjacent_authenticated_acquisition_hours': True,
            'native_fee_tier_authenticated': False,
            'position_funding_cashflows_authenticated': False,
            'minimum_two_consecutive_atomic_hours_authenticated': False,
            'paper_publication_authorized': False, 'promotion_authorized': False,
            'real_orders_enabled': False, 'holdout_accessed': False,
            'economic_trials': 0}


def gh(path):
    p = subprocess.run(['gh', 'api', path], check=True, capture_output=True, text=True)
    return json.loads(p.stdout)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repository', required=True)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repository):
        raise ValueError('invalid_repository')
    if not os.environ.get('GH_TOKEN'):
        raise ValueError('read_only_gh_token_required')
    root = 'repos/' + args.repository + '/actions/'
    runs = gh(root + 'runs?event=schedule&per_page=100')['workflow_runs']
    relevant = [r for r in runs if r.get('name') in (ATOMIC, SPLIT)]
    result = audit(relevant, lambda rid: gh(root + f'runs/{rid}/artifacts?per_page=100')['artifacts'])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result['status'],
                      'atomic_metadata_candidates': len(result['atomic_metadata_candidates']),
                      'split_run_collisions': len(result['split_run_same_created_hour_collisions']),
                      'promotion_authorized': False}))


if __name__ == '__main__':
    main()
