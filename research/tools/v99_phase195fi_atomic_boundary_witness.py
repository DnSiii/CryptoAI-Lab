"""V99 Phase195-FI: read-only atomic boundary witness for official paper archives.

Fail closed on time-skew between verified universe, data-sync horizon, and
all eight economic tracks. Checks structural consistency only: it cannot
attest exchange source-time, authorize paper publication, or promote a model.
No writes, source-data recovery, history patching, or economic tuning.
"""
from __future__ import annotations

import argparse
import json
import math
import zipfile
from datetime import datetime, timedelta, timezone

TRACKS = (
    'v13', 'core_comparison_v1', 'opportunity_v1', 'combined_v1',
    'v14', 'v15', 'v16', 'v99',
)


def strict_json(raw):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError('duplicate_json_key:' + k)
            out[k] = v
        return out

    def bad_constant(value):
        raise ValueError('nonfinite_json_constant:' + value)

    value = json.loads(raw, object_pairs_hook=unique, parse_constant=bad_constant)
    def check(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError('nonfinite_json_number')
        if isinstance(item, dict):
            for x in item.values(): check(x)
        if isinstance(item, list):
            for x in item: check(x)
    check(value)
    if not isinstance(value, dict):
        raise ValueError('json_object_required')
    return value


def utc(value):
    if not isinstance(value, str) or not value:
        raise ValueError('missing_explicit_utc')
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
        raise ValueError('explicit_utc_required')
    return stamp.astimezone(timezone.utc)


def hour(value):
    stamp = utc(value)
    if stamp.minute or stamp.second or stamp.microsecond:
        raise ValueError('not_whole_hour')
    return stamp


def inspect(universe, sync, ledgers, snapshots=None):
    """Return a closed verdict; valid structure NEVER implies source authenticity."""
    if not isinstance(universe, dict) or not isinstance(sync, dict):
        raise ValueError('universe_sync_required')
    if universe.get('mode') != 'PUBLIC_DATA_ONLY' or sync.get('mode') != 'PUBLIC_DATA_ONLY':
        raise ValueError('unexpected_data_mode')
    if sync.get('private_api_used') is not False:
        raise ValueError('private_data_or_missing_flag')
    if not isinstance(ledgers, dict) or set(ledgers) != set(TRACKS):
        raise ValueError('eight_exact_tracks_required')
    if snapshots is not None and set(snapshots) != set(TRACKS):
        raise ValueError('eight_exact_snapshots_required')

    warnings = []
    boundaries = {}
    for name, value in (
        ('universe_verified', universe.get('verified_boundary')),
        ('sync_target', sync.get('target_latest_closed_hour')),
        ('sync_expected', sync.get('expected_latest_closed_hour')),
    ):
        try:
            boundaries[name] = hour(value)
        except (ValueError, TypeError, OverflowError) as exc:
            warnings.append(f'{name}:invalid:{exc}')
    for name in ('sync_generated', 'universe_updated'):
        raw = sync.get('generated_at_utc') if name == 'sync_generated' else universe.get('updated_at_utc')
        try:
            boundaries[name] = utc(raw)
        except (ValueError, TypeError, OverflowError) as exc:
            warnings.append(f'{name}:invalid:{exc}')

    target = boundaries.get('sync_target')
    if target is not None:
        for key in ('sync_expected', 'universe_verified'):
            if key in boundaries and boundaries[key] != target:
                warnings.append(f'{key}:not_equal_sync_target')
        for key in ('sync_generated', 'universe_updated'):
            if key in boundaries and boundaries[key] < target + timedelta(hours=1):
                warnings.append(f'{key}:before_hour_close')

    track_summary = {}
    for name in TRACKS:
        ledger = ledgers[name]
        if not isinstance(ledger, dict):
            warnings.append(name+':ledger_not_object')
            continue
        if ledger.get('mode') != 'PAPER_ONLY' or ledger.get('real_orders_enabled') is not False:
            warnings.append(name+':paper_only_required')
        try:
            end = hour(ledger.get('latest_data_timestamp'))
        except (ValueError, TypeError, OverflowError) as exc:
            warnings.append(name+':latest_invalid:'+str(exc))
            continue
        if target is not None and end != target:
            warnings.append(name+':ledger_latest_not_sync_target')
        rows = ledger.get('equity_curve')
        if not isinstance(rows, list) or not rows:
            warnings.append(name+':curve_missing')
            continue
        previous = None
        for index, row in enumerate(rows):
            try:
                ts = hour(row['timestamp'])
            except (KeyError, TypeError, ValueError, OverflowError) as exc:
                warnings.append(name+':row_timestamp_invalid:'+str(index)+':'+str(exc))
                break
            if previous is not None and ts-previous != timedelta(hours=1):
                warnings.append(name+':curve_gap_or_reorder_at:'+str(index))
                break
            previous = ts
        try:
            final = hour(rows[-1]['timestamp'])
            if final != end:
                warnings.append(name+':curve_end_not_latest')
            track_summary[name] = {'latest':end.isoformat(), 'hours':len(rows),
                                   'curve_last':final.isoformat()}
        except (KeyError, TypeError, ValueError, OverflowError):
            warnings.append(name+':curve_last_invalid')
        if snapshots is not None:
            snap = snapshots[name]
            if snap.get('mode') != 'PAPER_ONLY' or snap.get('real_orders_enabled') is not False:
                warnings.append(name+':snapshot_not_paper_only')
            try:
                snap_end = hour(snap.get('latest_data_timestamp'))
                if snap_end != end:
                    warnings.append(name+':snapshot_latest_not_ledger')
            except (ValueError, TypeError, OverflowError) as exc:
                warnings.append(name+':snapshot_latest_invalid:'+str(exc))

    symbols = universe.get('symbols')
    if not isinstance(symbols, dict) or not symbols:
        warnings.append('universe_symbols_missing')

    return {
        'phase': '195-FI', 'scope': 'DATA_ONLY_ATOMIC_BOUNDARY',
        'status': 'OBSERVED_BOUNDARY_CONSISTENT_NOT_AUTHENTICATED' if not warnings else 'DATA_ONLY_HOLD',
        'boundary_issues': sorted(set(warnings)),
        'boundaries': {k: v.isoformat() for k, v in sorted(boundaries.items())},
        'tracks': track_summary,
        'source_time_authenticated': False,
        'append_only_prefix_certified': False,
        'publication_authorized': False,
        'promotion_authorized': False,
        'holdout_accessed': False,
        'economic_trials': 0,
    }


def inspect_zip(path):
    needed = ['state/paper_v15_universe.json', 'reports/paper_data_sync_v15.json']
    for track in TRACKS:
        needed.extend([f'reports/paper_{track}_ledger.json', f'reports/paper_{track}_snapshot.json'])
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate_zip_paths')
        def read(name):
            if name not in names:
                raise ValueError('missing_archive_member:'+name)
            info = archive.getinfo(name)
            if info.file_size > 32_000_000:
                raise ValueError('oversized_archive_member:'+name)
            return strict_json(archive.read(name))
        universe = read(needed[0])
        sync = read(needed[1])
        ledgers = {track:read(f'reports/paper_{track}_ledger.json') for track in TRACKS}
        snapshots = {track:read(f'reports/paper_{track}_snapshot.json') for track in TRACKS}
    return inspect(universe,sync,ledgers,snapshots)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', required=True)
    args = parser.parse_args()
    verdict = inspect_zip(args.artifact)
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not verdict['boundary_issues'] else 2)
