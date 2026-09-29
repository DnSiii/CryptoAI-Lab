import csv, importlib.util, tempfile
from pathlib import Path

P=Path(__file__).parent/'tools'/'v99_r106_phase180_arrival_gate.py'
spec=importlib.util.spec_from_file_location('g',P); g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

def write(rows):
    f=tempfile.NamedTemporaryFile('w',newline='',delete=False); csv.writer(f).writerows(rows); f.close(); return Path(f.name)
def hx(i): return f'{i:064x}'

def test_holdout_firewall():
    p=write([[1,hx(1),1000]])
    try: g.evaluate(p,0,g.HOLDOUT_START_MS+1,0)
    except ValueError as e: assert 'holdout' in str(e)
    else: assert False

def test_conflicting_hash_fails_closed():
    rows=[[h,hx(h),1000+h] for h in range(1,1010)]+[[10,hx(9999),1011]]
    r=g.evaluate(write(rows),0,100000,0)
    assert r['status']=='FAIL' and r['conflicting_heights']==[10]

def test_gap_fails_even_if_bucket_threshold_relaxed():
    rows=[[h,hx(h),1000+h] for h in range(1,1010) if h!=500]
    r=g.evaluate(write(rows),0,100000,0)
    assert r['status']=='FAIL' and r['internal_missing_heights']==1

def test_same_observer_duplicate_is_deterministic_earliest():
    rows=[[h,hx(h),1000+h] for h in range(1,1010)]+[[10,hx(10),999]]
    r1=g.evaluate(write(rows),0,100000,0); r2=g.evaluate(write(list(reversed(rows))),0,100000,0)
    assert r1['canonical_train_sha256']==r2['canonical_train_sha256']
    assert r1['duplicate_pairs']==1

def test_raw_holdout_rows_never_enter_train():
    rows=[[h,hx(h),1000+h] for h in range(1,1010)] + [[2000,hx(2000),g.HOLDOUT_START_MS]]
    r=g.evaluate(write(rows),0,100000,0)
    assert r['raw_rows_at_or_after_holdout']==1 and r['train_height_max']==1009

def test_single_observer_policy_is_explicit():
    rows=[[h,hx(h),1000+h] for h in range(1,1010)]
    r=g.evaluate(write(rows),0,100000,0)
    assert r['source_policy']=='single_observer_only'
    assert r['cross_source_min_forbidden'] and r['header_time_fallback_forbidden']
