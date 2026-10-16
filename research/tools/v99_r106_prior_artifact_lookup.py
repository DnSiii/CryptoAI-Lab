"""Discover recent scheduled OKX market artifacts without unrelated-paper first-page bias.

Discovery hint only. Downloaded bytes MUST pass raw hash, clock, causal t-1,
source-identity and native-pair gates before scientific use. DATA_ONLY/HOLD.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone

SOURCE_WORKFLOWS = {
    'V99 R106 hourly OKX as-of source receipts',
    'V99 R106 hourly first-party OKX source-only receipts',
    'V99 R106 atomic paired OKX market and terms DATA_ONLY',
}
PREFIXES = ('v99-r106-okx-firstparty-', 'v99-r106-hourly-okx-')


def choose(runs, artifacts_for, *, current_run_id, now_utc=None, max_age_hours=6):
    """Choose a scheduled completed original source, never a paper artifact."""
    if not isinstance(runs, list):
        raise ValueError('invalid_run_listing')
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError('explicit_utc_now_required')
    if not isinstance(max_age_hours, int) or not 1 <= max_age_hours <= 24:
        raise ValueError('invalid_source_age_limit')
    candidates = []
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError('malformed_run')
        if (run.get('name') not in SOURCE_WORKFLOWS or
                run.get('event') != 'schedule' or
                run.get('head_branch') != 'main' or
                run.get('status') != 'completed' or
                run.get('conclusion') != 'success'):
            continue
        rid = run.get('id')
        if type(rid) is not int or rid <= 0 or rid == current_run_id:
            continue
        created = run.get('created_at')
        if not isinstance(created, str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', created):
            raise ValueError('invalid_source_run_time')
        created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
        if created_dt > now or now - created_dt > timedelta(hours=max_age_hours):
            continue
        candidates.append((created, rid))
    for _, rid in sorted(candidates, reverse=True):
        artifacts = artifacts_for(rid)
        if not isinstance(artifacts, list):
            raise ValueError('invalid_artifact_listing')
        valid = [a for a in artifacts if isinstance(a, dict) and
                 a.get('name') in {p + str(rid) for p in PREFIXES} and
                 a.get('expired') is False and
                 type(a.get('size_in_bytes')) is int and a['size_in_bytes'] > 0]
        if len(valid) > 1:
            raise ValueError('ambiguous_original_market_artifacts')
        if valid:
            return {'run_id': rid, 'artifact_name': valid[0]['name'],
                    'status': 'UNVERIFIED_DISCOVERY_HINT_DATA_ONLY',
                    'paper_publication_authorized': False,
                    'promotion_authorized': False}
    raise ValueError('no_recent_scheduled_source_artifact_fail_closed')


def github_api(path):
    p = subprocess.run(['gh', 'api', path], check=True, capture_output=True, text=True)
    return json.loads(p.stdout)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repository', required=True)
    p.add_argument('--current-run-id', type=int, required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repository):
        raise ValueError('invalid_repository')
    # Scheduled-run search avoids first-page unrelated paper artifact crowding.
    url = f'repos/{args.repository}/actions/runs?event=schedule&per_page=100'
    runs = github_api(url)['workflow_runs']
    result = choose(runs, lambda rid: github_api(
        f'repos/{args.repository}/actions/runs/{rid}/artifacts?per_page=100')['artifacts'],
        current_run_id=args.current_run_id)
    from pathlib import Path
    Path(args.out).write_text(json.dumps(result, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
