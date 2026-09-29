import csv, importlib.util, tempfile
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("gate",HERE/"v99_r106_phase180_block_header_gate.py")
gate=importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)

def write(rows):
    f=tempfile.NamedTemporaryFile("w",newline="",delete=False,suffix=".csv")
    w=csv.DictWriter(f,fieldnames=["height","hash","previousblockhash","time","bits"]); w.writeheader(); w.writerows(rows); f.close(); return Path(f.name)

def chain(n=14,start=100):
    rows=[]; prev="gen"
    for i in range(n):
        h=start+i; hh=f"h{h}"; rows.append({"height":h,"hash":hh,"previousblockhash":prev,"time":1600000000+i*600,"bits":"170fffff"}); prev=hh
    return rows

def test_valid_chain_passes(): assert gate.audit(write(chain()))["status"]=="PASS"
def test_parent_mismatch_fails():
    r=chain(); r[4]["previousblockhash"]="wrong"; assert gate.audit(write(r))["status"]=="FAIL"
def test_height_gap_fails():
    r=chain(); r.pop(5); assert gate.audit(write(r))["status"]=="FAIL"
def test_off_boundary_bits_change_fails():
    r=chain(); r[5]["bits"]="180fffff"; assert gate.audit(write(r))["status"]=="FAIL"
def test_firewall_fails():
    r=chain(); r[-1]["time"]=int(gate.FIREWALL); assert gate.audit(write(r))["status"]=="FAIL"
def test_mtp_violation_fails():
    r=chain(); r[12]["time"]=r[5]["time"]; assert gate.audit(write(r))["status"]=="FAIL"
def test_conflicting_height_fails():
    r=chain(); x=dict(r[5]); x["hash"]="evil"; r.append(x); assert gate.audit(write(r))["status"]=="FAIL"
