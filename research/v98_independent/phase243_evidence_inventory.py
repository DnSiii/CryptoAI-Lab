#!/usr/bin/env python3
"""V98 Independent Phase243 evidence inventory with a strict V98-only read boundary.

Reads explicit V98 decisions/results, never V99 files or code/test/prereg text.
An absent/ambiguous decision remains unresolved, not implicitly promoted.
This is a DATA_ONLY inventory; no PnL or holdout reads.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'research' / 'v98_independent' / 'phase243_evidence_inventory.json'
PHASE = re.compile(r'phase[_-]?(\d{3})', re.I)
STATUS = re.compile(r'^\s*(?:status|decision)\s*:\s*(.+?)\s*$', re.I | re.M)
TOKENS = {
    'rejected': {'REJECT', 'REJECTED', 'REJECT_FAMILY_NO_RESCUE',
                 'REJECTED_NO_RESCUE', 'REJECT_FINAL_HOLDOUT'},
    'data_failed': {'FAIL_DATA', 'FAIL_DATA_NO_ALPHA'},
    'validation_pass': {'PASS_VALIDATION'},
    'training_pass': {'PASS_TRAINING'},
    'promoted_or_frozen': {'PROMOTED', 'FROZEN_CANDIDATE'},
    'data_only_pass': {'PASS_DATA_ONLY', 'PASS_SOURCE_INTEGRITY_DATA_ONLY_NO_ALPHA'},
}
PRIORITY = ('rejected', 'data_failed', 'validation_pass', 'training_pass',
            'promoted_or_frozen', 'data_only_pass')


def phase_of(path: Path):
    m = PHASE.search(path.name)
    return int(m.group(1)) if m else None


def classify_token(token: str):
    clean = re.sub(r'[^A-Z0-9_]+', '', token.strip().strip('*`').upper().replace(' ', '_'))
    for category, accepted in TOKENS.items():
        if clean in accepted:
            return category
    return 'unknown'


def classify(text: str, *, suffix: str = '.md'):
    """Only explicit top-level JSON decision/status or Markdown status lines count."""
    if suffix == '.json':
        try:
            obj = json.loads(text)
        except (ValueError, TypeError):
            return 'unknown'
        if not isinstance(obj, dict):
            return 'unknown'
        return classify_token(str(obj.get('decision', obj.get('status', ''))))
    matches = STATUS.findall('\n'.join(text.splitlines()[:45]))
    found = {classify_token(v) for v in matches} - {'unknown'}
    if len(found) == 1:
        return next(iter(found))
    return 'unknown'


def allowed_files(root: Path):
    """Explicit namespace allowlist: never traverse ROOT/reports wholesale."""
    reports = root / 'reports'
    research = root / 'research' / 'v98_independent'
    if reports.is_dir():
        for p in reports.glob('v98_independent_phase*'):
            if p.suffix in {'.md', '.json'} and 'prereg' not in p.name.lower():
                yield p
        sub = reports / 'v98_independent'
        if sub.is_dir() and not sub.is_symlink():
            for p in sub.rglob('*'):
                if p.suffix in {'.md', '.json'} and 'prereg' not in p.name.lower():
                    yield p
    if research.is_dir() and not research.is_symlink():
        for p in research.glob('phase*'):
            name = p.name.lower()
            if p.suffix not in {'.md', '.json'} or 'prereg' in name:
                continue
            if not any(k in name for k in ('audit', 'decision', 'postmortem',
                                           'rejection', 'failure', 'results')):
                continue
            yield p


def inventory(root: Path = ROOT):
    root = Path(root).resolve()
    permitted = (root / 'reports', root / 'research' / 'v98_independent')
    rows = {}
    for p in allowed_files(root):
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 2_000_000:
            continue
        # A symlink in a parent directory cannot expand the read boundary.
        rp = p.resolve()
        if not (rp.is_relative_to(permitted[1]) or
                (rp.is_relative_to(permitted[0]) and
                 (p.name.startswith('v98_independent_phase') or
                  rp.is_relative_to(permitted[0] / 'v98_independent')))):
            continue
        ph = phase_of(p)
        if ph is None:
            continue
        decision = classify(p.read_text(encoding='utf-8', errors='replace'), suffix=p.suffix)
        rec = rows.setdefault(ph, {'phase': ph, 'files': [], 'signals': []})
        rec['files'].append(str(p.relative_to(root)))
        if decision != 'unknown':
            rec['signals'].append(decision)
    out = []
    for ph, rec in sorted(rows.items()):
        signals = set(rec['signals'])
        # Conflicting decisions are unresolved; never silently prefer promotion.
        final = next(iter(signals)) if len(signals) == 1 else 'unknown'
        rec['status'] = final
        rec['files'] = sorted(set(rec['files']))
        rec['signals'] = sorted(signals)
        rec['architecture_eligibility'] = (
            'negative_evidence_only' if final in {'rejected', 'data_failed'}
            else 'candidate_for_marginal_review' if final in
            {'validation_pass', 'training_pass', 'promoted_or_frozen'}
            else 'data_capability_only' if final == 'data_only_pass'
            else 'unresolved')
        out.append(rec)
    return {'engine': 'V98 Independent', 'phase': 243,
            'mode': 'EVIDENCE_INVENTORY_NO_PNL', 'external_benchmarks_read': False,
            'v14_used': False, 'v15_used': False, 'v99_used': False,
            'phase_count': len(out), 'phases': out}


def main():
    payload = inventory()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'phase': 243, 'phase_count': payload['phase_count'],
                      'status_counts': {s: sum(r['status'] == s for r in payload['phases'])
                                        for s in sorted({r['status'] for r in payload['phases']})}}, indent=2))


if __name__ == '__main__':
    main()
