import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from research.v98_independent.phase243_strict_historical_accounting_run import run, verify_native_prices

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
H=3600000
START=1704067200000

class StrictHistoricalRunTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"v98_independent"
        self.root.mkdir()
        self.funding=self.root/"funding"
        self.funding.mkdir()
        manifest={"mode":"V98_NATIVE_FUNDING_CANONICAL_SOURCE_ONLY","holdout_accessed":False,"assets":{}}
        for a in ASSETS:
            p=self.funding/f"{a}_native_funding.csv"
            p.write_text("funding_time_ms,funding_rate\n"+f"{START+H},0.001\n")
            manifest["assets"][a]={"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
        (self.funding/"funding_manifest.json").write_text(json.dumps(manifest))
        self.positions=self.root/"positions.csv"
        self.output=self.root/"ledger.csv"
    def write(self,decision_offset=-H,missing=False):
        with self.positions.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["asset","hour_open_ms","decision_time_ms","pre_trade_notional_usd","target_notional_usd","close_price","fill_price"])
            w.writeheader()
            for t in (START,START+H):
                for a in ASSETS:
                    if missing and a=="BNBUSDT" and t==START+H: continue
                    w.writerow(dict(asset=a,hour_open_ms=t,decision_time_ms=t+decision_offset,
                                    pre_trade_notional_usd=0,target_notional_usd=0,close_price=100,fill_price=100))
    def execute(self):
        return run(self.positions,self.funding,self.output,initial_equity_usd=10000,
                   taker_fee_bps=5,slippage_bps=2,cost_multiplier=1,max_gross_leverage=2)
    def test_complete_flat_historical_receipt(self):
        self.write()
        r=self.execute()
        self.assertEqual(r["hours"],2)
        self.assertEqual(r["ending_equity_usd"],10000)
        self.assertTrue(self.output.with_suffix(".receipt.json").exists())
    def test_reject_same_hour_decision(self):
        self.write(decision_offset=0)
        with self.assertRaisesRegex(ValueError,"NONCAUSAL_DECISION"):
            self.execute()
    def test_reject_incomplete_grid(self):
        self.write(missing=True)
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_CLEAN4"):
            self.execute()
    def test_full_length_duplicate_rows_cannot_fake_clean4_history(self):
        # 35,040 rows, but only one asset and one hour: never an admissible year.
        with self.positions.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["asset","hour_open_ms","decision_time_ms",
                "pre_trade_notional_usd","target_notional_usd","close_price","fill_price"])
            w.writeheader()
            row=dict(asset="BTCUSDT",hour_open_ms=START,decision_time_ms=START-H,
                     pre_trade_notional_usd=0,target_notional_usd=0,close_price=100,fill_price=100)
            for _ in range(8760*len(ASSETS)):
                w.writerow(row)
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_HISTORICAL_ASSET_GRID"):
            self.execute()
    def test_reject_modified_funding(self):
        self.write()
        with (self.funding/"BTCUSDT_native_funding.csv").open("a") as f: f.write("\n")
        with self.assertRaisesRegex(ValueError,"FUNDING_CANONICAL_HASH_MISMATCH"):
            self.execute()
    def test_native_price_provenance_and_tamper(self):
        self.write()
        prices=self.root/"prices"
        prices.mkdir()
        manifest={"mode":"CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA","holdout_accessed":False,"prices":{}}
        from datetime import datetime, timezone
        for a in ASSETS:
            p=prices/f"{a}_1h.csv"
            with p.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["open_time","open","close"])
                w.writeheader()
                for t in (START,START+H):
                    w.writerow({"open_time":datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),
                                "open":100,"close":100})
            manifest["prices"][a]={"canonical_sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
        m=self.root/"price_manifest.json"
        m.write_text(json.dumps(manifest))
        with self.positions.open(newline="") as f: rows=list(csv.DictReader(f))
        verify_native_prices(rows,prices,m)
        rows[0]["fill_price"]="101"
        with self.assertRaisesRegex(ValueError,"EXECUTION_PRICE_SOURCE_MISMATCH"):
            verify_native_prices(rows,prices,m)
        rows[0]["fill_price"]="100"
        with (prices/"BTCUSDT_1h.csv").open("a") as f:f.write("tamper")
        with self.assertRaisesRegex(ValueError,"PRICE_CANONICAL_HASH_MISMATCH"):
            verify_native_prices(rows,prices,m)
    def test_reject_duplicate_and_gapped_authenticated_bars(self):
        self.write()
        prices=self.root/"prices"
        prices.mkdir()
        manifest={"mode":"CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA","holdout_accessed":False,"prices":{}}
        from datetime import datetime, timezone
        for a in ASSETS:
            p=prices/f"{a}_1h.csv"
            with p.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["open_time","open","close"])
                w.writeheader()
                for t in (START,START+H):
                    w.writerow({"open_time":datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),"open":100,"close":100})
            manifest["prices"][a]={"canonical_sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
        m=self.root/"price_manifest.json"
        with self.positions.open(newline="") as f: rows=list(csv.DictReader(f))
        p=prices/"BTCUSDT_1h.csv"
        original=p.read_text()
        for corrupted, error in (
            (original+original.splitlines()[-1]+"\\n","DUPLICATE_OR_UNALIGNED"),
            (original.replace(datetime.fromtimestamp((START+H)/1000,timezone.utc).isoformat(),
                              datetime.fromtimestamp((START+2*H)/1000,timezone.utc).isoformat()),"NONCONTIGUOUS"),
        ):
            p.write_text(corrupted)
            manifest["prices"]["BTCUSDT"]["canonical_sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()
            m.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,error):
                verify_native_prices(rows,prices,m)
        p.write_text(original)
        manifest["prices"]["BTCUSDT"]["canonical_sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()
        m.write_text(json.dumps(manifest))
        verify_native_prices(rows,prices,m)
if __name__=="__main__": unittest.main()
