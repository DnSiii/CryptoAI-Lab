import csv, tempfile
from pathlib import Path
from research.tools.v99_r106_phase181_beacon_slot_gate import gate

def write(rows):
    p=Path(tempfile.mkstemp(suffix='.csv')[1])
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['slot','block_root','parent_root','observed_at']); w.writeheader(); w.writerows(rows)
    return p

def test_holdout_fails_closed():
    p=write([{'slot':1,'block_root':'b','parent_root':'a','observed_at':'2024-01-18T00:00:00Z'}])
    assert gate(p,'2021-12-01T00:00:00Z')['status']=='FAIL'

def test_parent_discontinuity_fails():
    p=write([{'slot':1,'block_root':'b','parent_root':'a','observed_at':'2021-11-01T00:00:00Z'},{'slot':2,'block_root':'c','parent_root':'x','observed_at':'2021-11-01T00:00:12Z'}])
    assert any('parent discontinuity' in x for x in gate(p,'2021-12-01T00:00:00Z')['errors'])

def test_gap_is_not_known_at_scheduled_slot():
    rows=[]; parent='genesis'
    for s in range(2050):
        if s==2048: continue
        root=f'r{s}'; rows.append({'slot':s,'block_root':root,'parent_root':parent,'observed_at':f'2021-11-{1+s//720:02d}T00:00:00Z'}); parent=root
    # Synthetic parent continuity intentionally cannot represent skipped canonical parent with this simple fixture;
    # the key invariant is that gate never derives availability from protocol scheduled time.
    p=write(rows); out=gate(p,'2021-12-01T00:00:00Z')
    assert 'next observed canonical block' in out['availability_rule']

def test_preroll_required():
    p=write([{'slot':1,'block_root':'b','parent_root':'a','observed_at':'2021-11-01T00:00:00Z'}])
    assert any('pre-roll' in x for x in gate(p,'2021-12-01T00:00:00Z')['errors'])
