import csv,importlib.util,tempfile
from pathlib import Path
P=Path(__file__).parent/'tools'/'v99_r106_phase180_arrival_gate.py'; spec=importlib.util.spec_from_file_location('g',P); g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
def write(rows):
 f=tempfile.NamedTemporaryFile('w',newline='',delete=False); csv.writer(f).writerows(rows); f.close(); return Path(f.name)
def hx(i): return f'{i:064x}'
def base(): return [[h,hx(h),1000+h] for h in range(1,1010)]
def ev(rows): return g.evaluate(write(rows),0,3000,0)
def test_holdout_firewall():
 try:g.evaluate(write([[1,hx(1),1000]]),0,g.HOLDOUT_START_MS+1,0)
 except ValueError as e: assert 'holdout' in str(e)
 else: assert False
def test_conflicting_hash_fails_closed():
 r=ev(base()+[[10,hx(9999),1011]]); assert r['status']=='FAIL' and r['conflicting_heights']==[10]
def test_gap_fails_even_if_bucket_threshold_relaxed():
 r=ev([x for x in base() if x[0]!=500]); assert r['status']=='FAIL' and r['internal_missing_heights']==1
def test_same_observer_duplicate_is_deterministic_earliest():
 rows=base()+[[10,hx(10),999]]; r1=ev(rows); r2=ev(list(reversed(rows))); assert r1['canonical_train_sha256']==r2['canonical_train_sha256'] and r1['duplicate_pairs']==1
def test_raw_holdout_rows_never_enter_train():
 r=ev(base()+[[2000,hx(2000),g.HOLDOUT_START_MS]]); assert r['raw_rows_at_or_after_holdout']==1 and r['train_height_max']==1009
def test_single_observer_policy_is_explicit():
 r=ev(base()); assert r['source_policy']=='single_observer_only' and r['cross_source_min_forbidden'] and r['header_time_fallback_forbidden']
def test_late_start_fails_temporal_coverage():
 start=10_000_000_000; rows=[[h,hx(h),start+g.EDGE_TOLERANCE_MS+1+h] for h in range(1,1010)]; r=g.evaluate(write(rows),start,start+g.EDGE_TOLERANCE_MS*3,0); assert r['status']=='FAIL' and not r['starts_on_time']
def test_early_end_fails_temporal_coverage():
 start=10_000_000_000; rows=[[h,hx(h),start+h] for h in range(1,1010)]; r=g.evaluate(write(rows),start,start+g.EDGE_TOLERANCE_MS*3,0); assert r['status']=='FAIL' and not r['ends_on_time']
