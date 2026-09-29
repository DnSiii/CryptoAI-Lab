import csv,hashlib,importlib.util,json
from pathlib import Path
P=Path(__file__).with_name('v99_r106_phase180_block_stress_features.py'); s=importlib.util.spec_from_file_location('feat',P); feat=importlib.util.module_from_spec(s); s.loader.exec_module(feat)

def write(tmp,n=150,delta=600,start=100000):
    p=tmp/'h.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['height','hash','time']); w.writeheader(); t=start
        for i in range(n): w.writerow({'height':i,'hash':f'{i:064x}','time':t}); t+=delta
    return p

def gate(tmp,src,status='PASS',digest=None):
    p=tmp/'gate.json'; p.write_text(json.dumps({'status':status,'source_sha256':digest or feat.sha256(src),'firewall_utc':'2024-01-18T00:00:00Z','consensus_scope':'bitcoin-mainnet'})); return p

def read(p): return list(csv.DictReader(p.open()))
def build(tmp,src,name='o.csv'): return (lambda o:(feat.build(src,o,gate(tmp,src)),o)[1])(tmp/name)

def test_target_cadence_zero_stress(tmp_path):
    src=write(tmp_path); r=read(build(tmp_path,src))[-1]
    for w in feat.WINDOWS:
        assert float(r[f'mean_stress_{w}'])==0; assert float(r[f'median_stress_{w}'])==0; assert float(r[f'frac_gt_1200_{w}'])==0; assert float(r[f'frac_gt_3600_{w}'])==0

def test_warmup_is_missing_not_imputed(tmp_path):
    src=write(tmp_path,n=10); r=read(build(tmp_path,src)); assert r[6]['mean_stress_6']==''; assert r[7]['mean_stress_6']!=''; assert all(x['mean_stress_36']=='' for x in r)

def test_nonpositive_delta_is_visible_only_next_block(tmp_path):
    src=write(tmp_path,n=9); rows=read(src); rows[6]['time']=rows[5]['time']
    with src.open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=['height','hash','time']); w.writeheader(); w.writerows(rows)
    r=read(build(tmp_path,src)); assert float(r[6]['mean_stress_6'])==0; assert float(r[7]['mean_stress_6'])<0

def test_current_block_timestamp_cannot_change_own_features(tmp_path):
    src=write(tmp_path); a=read(build(tmp_path,src,'a.csv')); rows=read(src); k=100; rows[k]['time']=str(int(rows[k]['time'])+99999)
    with src.open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=['height','hash','time']); w.writeheader(); w.writerows(rows)
    b=read(build(tmp_path,src,'b.csv'))
    feature_cols=[c for c in a[k] if c not in ('height','hash','time')]
    assert all(a[k][c]==b[k][c] for c in feature_cols)
    assert any(a[k+1][c]!=b[k+1][c] for c in feature_cols)

def test_no_future_dependency(tmp_path):
    src=write(tmp_path); a=read(build(tmp_path,src,'a.csv')); rows=read(src); rows[-1]['time']=str(int(rows[-1]['time'])+99999)
    with src.open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=['height','hash','time']); w.writeheader(); w.writerows(rows)
    b=read(build(tmp_path,src,'b.csv')); assert all(a[-1][c]==b[-1][c] for c in a[-1] if c not in ('time',))

def test_manifest_declares_structural_lag(tmp_path):
    src=write(tmp_path); out=tmp_path/'o.csv'; meta=feat.build(src,out,gate(tmp_path,src)); assert meta['causal_lag_blocks']==1

def test_byte_reproducible(tmp_path):
    src=write(tmp_path); a=build(tmp_path,src,'a.csv'); b=build(tmp_path,src,'b.csv'); assert hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()

def test_gate_sha_mismatch_fails(tmp_path):
    src=write(tmp_path); g=gate(tmp_path,src,digest='0'*64)
    try: feat.build(src,tmp_path/'o.csv',g)
    except ValueError as e: assert 'sha256 mismatch' in str(e)
    else: raise AssertionError('mismatched provenance accepted')

def test_failed_gate_fails(tmp_path):
    src=write(tmp_path); g=gate(tmp_path,src,status='FAIL')
    try: feat.build(src,tmp_path/'o.csv',g)
    except ValueError as e: assert 'did not PASS' in str(e)
    else: raise AssertionError('failed gate accepted')

def test_holdout_firewall_fails(tmp_path):
    src=write(tmp_path,n=2,start=feat.FIREWALL-600); g=gate(tmp_path,src)
    try: feat.build(src,tmp_path/'o.csv',g)
    except ValueError as e: assert 'firewall' in str(e)
    else: raise AssertionError('holdout accepted')
