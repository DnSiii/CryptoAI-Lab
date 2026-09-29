import csv,hashlib,importlib.util
from pathlib import Path

P=Path(__file__).with_name('v99_r106_phase180_block_stress_features.py')
s=importlib.util.spec_from_file_location('feat',P); feat=importlib.util.module_from_spec(s); s.loader.exec_module(feat)

def write(tmp,n=150,delta=600):
    p=tmp/'h.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['height','hash','time']); w.writeheader()
        t=100000
        for i in range(n):
            w.writerow({'height':i,'hash':f'{i:064x}','time':t}); t+=delta
    return p

def read(p): return list(csv.DictReader(p.open()))

def test_target_cadence_zero_stress(tmp_path):
    src=write(tmp_path); out=tmp_path/'o.csv'; feat.build(src,out); r=read(out)[-1]
    for w in feat.WINDOWS:
        assert float(r[f'mean_stress_{w}'])==0
        assert float(r[f'median_stress_{w}'])==0
        assert float(r[f'frac_gt_1200_{w}'])==0
        assert float(r[f'frac_gt_3600_{w}'])==0

def test_warmup_is_missing_not_imputed(tmp_path):
    src=write(tmp_path,n=10); out=tmp_path/'o.csv'; feat.build(src,out); r=read(out)
    assert r[5]['mean_stress_6']==''
    assert r[6]['mean_stress_6']!=''
    assert all(x['mean_stress_36']=='' for x in r)

def test_nonpositive_delta_retained(tmp_path):
    src=write(tmp_path,n=8); rows=read(src); rows[6]['time']=rows[5]['time']
    with src.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['height','hash','time']); w.writeheader(); w.writerows(rows)
    out=tmp_path/'o.csv'; feat.build(src,out); r=read(out)[6]
    assert float(r['mean_stress_6']) < 0

def test_no_future_dependency(tmp_path):
    src=write(tmp_path); o1=tmp_path/'a.csv'; feat.build(src,o1); a=read(o1)
    rows=read(src); rows[-1]['time']=str(int(rows[-1]['time'])+99999)
    with src.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['height','hash','time']); w.writeheader(); w.writerows(rows)
    o2=tmp_path/'b.csv'; feat.build(src,o2); b=read(o2)
    assert a[:-1]==b[:-1]

def test_byte_reproducible(tmp_path):
    src=write(tmp_path); a=tmp_path/'a.csv'; b=tmp_path/'b.csv'; feat.build(src,a); feat.build(src,b)
    assert hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()

def test_gap_fails_closed(tmp_path):
    src=write(tmp_path,n=8); rows=read(src); rows.pop(3)
    with src.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['height','hash','time']); w.writeheader(); w.writerows(rows)
    try: feat.build(src,tmp_path/'o.csv')
    except ValueError as e: assert 'height gap' in str(e)
    else: raise AssertionError('gap accepted')
