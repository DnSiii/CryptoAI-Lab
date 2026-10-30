from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
POLICY=PROJECT/'reports'/'v98_independent_next_forward_holdout_policy.md'
START='2026-09-16'; END='2026-10-15'

def test_forward_holdout_policy_is_preregistered():
    text=POLICY.read_text()
    assert START in text and END in text
    assert 'NO ACCESS' in text
    assert 'one-shot final confirmation only' in text

def test_research_scripts_do_not_reference_reserved_forward_window():
    violations=[]
    for p in (PROJECT/'scripts').glob('v98_independent_*.py'):
        text=p.read_text(errors='ignore')
        if START in text or END in text:
            violations.append(str(p.relative_to(PROJECT)))
    assert violations==[], f'reserved forward holdout referenced by research scripts: {violations}'
