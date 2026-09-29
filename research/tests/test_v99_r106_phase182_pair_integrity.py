import csv,tempfile
from pathlib import Path
from research.tools.v99_r106_phase182_pair_integrity import gate

FIELDS=['timestamp','open','high','low','close','volume']
def make(times):
    p=Path(tempfile.mkstemp(suffix='.csv')[1])
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader()
        for t in times:w.writerow({'timestamp':t,'open':10,'high':11,'low':9,'close':10.5,'volume':1})
    return p

def test_exact_pair_passes():
    x=['2023-01-01T00:00:00Z','2023-01-01T01:00:00Z']
    assert gate(make(x),make(x))['status']=='PASS'

def test_mismatch_fails_closed():
    a=make(['2023-01-01T00:00:00Z','2023-01-01T01:00:00Z'])
    b=make(['2023-01-01T00:00:00Z'])
    assert any('timestamp mismatch' in x for x in gate(a,b)['errors'])

def test_holdout_fails_closed():
    x=make(['2024-01-18T00:00:00Z'])
    assert gate(x,x)['status']=='FAIL'

def test_duplicates_fail_closed():
    x=make(['2023-01-01T00:00:00Z','2023-01-01T00:00:00Z'])
    assert gate(x,x)['status']=='FAIL'

def test_nonchronological_fails_closed():
    x=make(['2023-01-01T01:00:00Z','2023-01-01T00:00:00Z'])
    assert gate(x,x)['status']=='FAIL'
