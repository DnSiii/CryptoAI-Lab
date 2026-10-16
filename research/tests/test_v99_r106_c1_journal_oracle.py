"""Independent C1 journal oracle mutation tests, no historical PnL."""
import csv,datetime,math,tempfile,unittest
from pathlib import Path
from research.tools import v99_r106_c1_core as c
from research.tools import v99_r106_c1_accounting as acc
from research.tools import v99_r106_c1_journal_oracle as oracle
def fake(n=2150):
    start=datetime.datetime(2021,10,1,tzinfo=datetime.timezone.utc)
    b=[];e=[]
    for k in range(n):
        t=start+datetime.timedelta(hours=k)
        v=100*math.exp(k*.0001);u=50*math.exp(-k*.00009)
        b.append((t,v,v*1.005,v*.995,v,1000.))
        e.append((t,u,u*1.005,u*.995,u,900.))
    return b,e
class OracleTests(unittest.TestCase):
    def test_synthetic_original_journal_matches_independent_replay(self):
        b,e=fake()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"j.csv"
            produced=acc.simulate(b,e,c.SEVERE,p)
            witness=oracle.verify(b,e,p,c.SEVERE)
            self.assertEqual(witness["rows"],produced["hours"])
            self.assertAlmostEqual(witness["independent_net_roi"],produced["roi"])
    def test_altered_fee_is_rejected(self):
        b,e=fake()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"j.csv"
            acc.simulate(b,e,c.SEVERE,p)
            with p.open(newline="") as f:records=list(csv.DictReader(f))
            records[10]["fee"]=str(float(records[10]["fee"])+0.01)
            with p.open("w",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=list(oracle.FIELDS))
                writer.writeheader();writer.writerows(records)
            with self.assertRaisesRegex(ValueError,"journal_accounting_discrepancy:fee"):
                oracle.verify(b,e,p,c.SEVERE)
    def test_altered_equity_is_rejected(self):
        b,e=fake()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"j.csv";acc.simulate(b,e,c.SEVERE,p)
            with p.open(newline="") as f:records=list(csv.DictReader(f))
            records[10]["equity"]="12"
            with p.open("w",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=list(oracle.FIELDS))
                writer.writeheader();writer.writerows(records)
            with self.assertRaisesRegex(ValueError,"journal_accounting_discrepancy:equity"):
                oracle.verify(b,e,p,c.SEVERE)
    def test_missing_time_or_extra_hour_refused(self):
        b,e=fake()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"j.csv";acc.simulate(b,e,c.SEVERE,p)
            s=p.read_text().splitlines()
            p.write_text("\n".join(s[:-1])+"\n")
            with self.assertRaisesRegex(ValueError,"journal_hourly_coverage_mismatch"):
                oracle.verify(b,e,p,c.SEVERE)
    def test_wrong_cost_scenario_denied(self):
        b,e=fake()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"j.csv";acc.simulate(b,e,c.SEVERE,p)
            with self.assertRaisesRegex(ValueError,"unfrozen_cost"):
                oracle.verify(b,e,p,0)
if __name__=="__main__":unittest.main()
