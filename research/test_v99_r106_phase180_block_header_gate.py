import csv, importlib.util, tempfile
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("gate",HERE/"v99_r106_phase180_block_header_gate.py")
gate=importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)

def write(rows):
    f=tempfile.NamedTemporaryFile("w",newline="",delete=False,suffix=".csv")
    w=csv.DictWriter(f,fieldnames=["height","hash","previousblockhash","time","bits"]); w.writeheader(); w.writerows(rows); f.close(); return Path(f.name)

def hh(h): return f"{h+1:064x}"
def chain(n=14,start=100,bits="1d00ffff"):
    rows=[]; prev="0"*64
    for i in range(n):
        h=start+i; cur=hh(h); rows.append({"height":h,"hash":cur,"previousblockhash":prev,"time":1600000000+i*600,"bits":bits}); prev=cur
    return rows

def fails(rows,needle):
    out=gate.audit(write(rows)); assert out["status"]=="FAIL"; assert any(needle in x for x in out["failures"])

def test_valid_chain_passes(): assert gate.audit(write(chain()))["status"]=="PASS"
def test_parent_mismatch_fails():
    r=chain(); r[4]["previousblockhash"]="f"*64; fails(r,"parent_mismatch")
def test_height_gap_fails():
    r=chain(); r.pop(5); fails(r,"height_gap")
def test_off_boundary_bits_change_fails():
    r=chain(); r[5]["bits"]="1c00ffff"; fails(r,"bits_change_off_boundary")
def test_firewall_fails():
    r=chain(); r[-1]["time"]=int(gate.FIREWALL); fails(r,"firewall")
def test_mtp_violation_fails():
    r=chain(); r[12]["time"]=r[5]["time"]; fails(r,"mtp_violation")
def test_conflicting_height_fails():
    r=chain(); x=dict(r[5]); x["hash"]=f"{999:064x}"; r.append(x); fails(r,"conflicting_height")
def test_invalid_pow_fails():
    r=chain(); r[3]["hash"]="f"*64; r[4]["previousblockhash"]="f"*64; fails(r,"pow_invalid")
def test_invalid_hash_encoding_fails():
    r=chain(); r[3]["hash"]="not-a-hash"; r[4]["previousblockhash"]="not-a-hash"; fails(r,"invalid_hash_encoding")
def test_retarget_missing_preroll_fails():
    r=chain(n=2016,start=1); fails(r,"retarget_missing_preroll:2016")
def test_valid_retarget_passes():
    r=chain(n=2017,start=0); assert gate.audit(write(r))["status"]=="PASS"
def test_wrong_retarget_fails():
    r=chain(n=2017,start=0); r[-1]["bits"]="1c00ffff"; fails(r,"retarget_mismatch:2016")
