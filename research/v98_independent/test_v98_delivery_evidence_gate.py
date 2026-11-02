"""V98 Independent synthetic negative controls: no historical PnL or real custody."""
from __future__ import annotations
import csv,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
MOD=Path(__file__).with_name("v98_delivery_evidence_gate.py")
spec=importlib.util.spec_from_file_location("v98_delivery_evidence_gate",MOD)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        original=gate.EXPECTED_COUNT;gate.EXPECTED_COUNT=8
        self.addCleanup(lambda:setattr(gate,"EXPECTED_COUNT",original))
        self.ts=[gate.START,gate.START+8*3600000]
        self.expected=self.root/"native_expected.csv"
        with self.expected.open("w",newline="") as f:
            w=csv.writer(f);w.writerow(gate.FIELDS)
            for a in gate.ASSETS:
                for t in self.ts:w.writerow([a,t,"0.00010000"])
        self.expected_sha=digest(self.expected);self.pages=[]
        old_pin=gate.PINNED_EXPECTED_FUNDING_SHA256
        gate.PINNED_EXPECTED_FUNDING_SHA256=self.expected_sha
        self.addCleanup(lambda:setattr(gate,"PINNED_EXPECTED_FUNDING_SHA256",old_pin))
        for a in gate.ASSETS:
            p=self.root/(a+".json")
            p.write_text(json.dumps([{"symbol":a,"fundingTime":t,
                "fundingRate":"0.00010000","markPrice":"123.45"} for t in self.ts]))
            self.pages.append({"source_type":"official_binance_usdm_fundingRate",
                "url":f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={a}&limit=1000&startTime={self.ts[0]}&endTime={self.ts[-1]+60000}",
                "retrieved_at_utc":"2026-11-02T00:00:00Z",
                "http_status":200,
                "response_headers":{"Date":"Mon, 02 Nov 2026 00:00:05 GMT"},
                "file":p.name,"sha256":digest(p)})
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.proofs={}
        for name in ("account_fee_schedule","historical_bid_ask_depth","collateral_liquidation_policy"):
            p=self.root/(name+".txt");p.write_text("SYNTHETIC ONLY; NOT ACCOUNT EVIDENCE\n")
            self.proofs[name]={"file":p.name,"sha256":digest(p),"issuer":"SYNTHETIC",
                               "applicable_account_tier":"SYNTHETIC"}
        self.cost={"fee_periods":[{"start_ms":gate.START,"end_ms":gate.END,
            "spot_taker_bps":10,"perp_taker_bps":5,
            "spot_spread_bps":1,"perp_spread_bps":1,
            "spot_impact_bps":2,"perp_impact_bps":2}],**self.proofs}
        self.write_json("account_costs_manifest.json",self.cost)

    def write_json(self,name,obj):(self.root/name).write_text(json.dumps(obj))
    def evaluate(self):return gate.evaluate(self.root,self.expected,self.expected_sha)

    def test_synthetic_valid_custody_never_approves_trading(self):
        r=self.evaluate()
        self.assertEqual(r["decision"],"PASS_BYTE_AND_CALENDAR_PREFLIGHT_REQUIRES_INDEPENDENT_AUTHENTICATION")
        self.assertEqual(r["native"]["event_count"],8)
        self.assertFalse(r["native"]["exchange_origin_independently_authenticated"])
        self.assertFalse(r["paper_or_live_authorized"])

    def test_unpinned_expected_source_fails(self):
        gate.PINNED_EXPECTED_FUNDING_SHA256="0"*64
        self.assertIn("UNPINNED_EXPECTED_SOURCE",self.evaluate()["blocker"])

    def test_missing_native_pages_fails_closed(self):
        (self.root/"native_pages_manifest.json").unlink()
        self.assertEqual(self.evaluate()["decision"],"HOLD_MISSING_EXTERNAL_EVIDENCE")

    def test_missing_account_evidence_fails_closed(self):
        (self.root/"account_costs_manifest.json").unlink()
        self.assertIn("account",self.evaluate()["blocker"])

    def test_tampered_page_fails_sha(self):
        (self.root/"BTCUSDT.json").write_text("[]")
        self.assertIn("NATIVE_PAGE_SHA",self.evaluate()["blocker"])

    def test_tampered_rate_fails_even_with_recomputed_page_sha(self):
        p=self.root/"BTCUSDT.json";x=json.loads(p.read_text())
        x[0]["fundingRate"]="0.00030000";p.write_text(json.dumps(x))
        self.pages[0]["sha256"]=digest(p)
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("NATIVE_RATE_CONFLICT",self.evaluate()["blocker"])

    def test_missing_one_event_fails_coverage(self):
        p=self.root/"BTCUSDT.json";x=json.loads(p.read_text())
        p.write_text(json.dumps(x[:1]));self.pages[0]["sha256"]=digest(p)
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("NATIVE_INCOMPLETE_COVERAGE",self.evaluate()["blocker"])

    def test_out_of_period_event_fails_firewall(self):
        p=self.root/"BTCUSDT.json";x=json.loads(p.read_text())
        x[1]["fundingTime"]=gate.END;p.write_text(json.dumps(x))
        self.pages[0]["sha256"]=digest(p)
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("OUTSIDE_EXPOSED_TRAINING",self.evaluate()["blocker"])

    def test_official_millisecond_offset_is_reconciled_to_native_slot(self):
        p=self.root/"BTCUSDT.json";x=json.loads(p.read_text())
        x[0]["fundingTime"]+=29;p.write_text(json.dumps(x))
        self.pages[0]["sha256"]=digest(p)
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertTrue(self.evaluate()["native"]["native_marks_reconciled"])

    def test_event_offset_over_sixty_seconds_fails(self):
        p=self.root/"BTCUSDT.json";x=json.loads(p.read_text())
        x[0]["fundingTime"]+=60001;p.write_text(json.dumps(x))
        self.pages[0]["sha256"]=digest(p)
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("NATIVE_SETTLEMENT_OFFSET_GT_60S",self.evaluate()["blocker"])

    def test_non_200_status_fails(self):
        self.pages[0]["http_status"]=451
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("NATIVE_HTTP_NOT_200",self.evaluate()["blocker"])

    def test_missing_original_http_date_fails(self):
        self.pages[0]["response_headers"]={}
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("NATIVE_HTTP_DATE_HEADER",self.evaluate()["blocker"])

    def test_request_window_cannot_claim_unrequested_event(self):
        self.pages[0]["url"]=self.pages[0]["url"].replace(
            str(self.ts[-1]+60000),str(self.ts[0]))
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("NATIVE_ROW_OUTSIDE_REQUEST",self.evaluate()["blocker"])

    def test_future_request_window_fails_before_reading_rows(self):
        self.pages[0]["url"]=self.pages[0]["url"].replace(
            str(self.ts[-1]+60000),str(gate.END))
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("NATIVE_QUERY_OUTSIDE_TRAINING",self.evaluate()["blocker"])

    def test_fractional_timestamp_cannot_truncate_to_slot(self):
        p=self.root/"BTCUSDT.json";rows=json.loads(p.read_text())
        rows[0]["fundingTime"]=float(self.ts[0])+0.25
        p.write_text(json.dumps(rows));self.pages[0]["sha256"]=digest(p)
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("NATIVE_TIMESTAMP_TYPE",self.evaluate()["blocker"])

    def test_duplicate_exchange_json_key_fails(self):
        p=self.root/"BTCUSDT.json"
        rows=json.loads(p.read_text())
        body=json.dumps(rows)
        body=body.replace('"markPrice": "123.45"', '"markPrice": "1", "markPrice": "123.45"',1)
        p.write_text(body);self.pages[0]["sha256"]=digest(p)
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("NATIVE_PAGE_JSON",self.evaluate()["blocker"])

    def test_duplicate_manifest_metadata_key_fails(self):
        p=self.root/"native_pages_manifest.json"
        raw=p.read_text().replace('"pages":', '"pages": [], "pages":',1)
        p.write_text(raw)
        self.assertIn("DUPLICATE_JSON_KEY",self.evaluate()["blocker"])

    def test_fee_period_gap_fails(self):
        self.cost["fee_periods"][0]["start_ms"]+=1
        self.write_json("account_costs_manifest.json",self.cost)
        self.assertIn("ACCOUNT_FEE_PERIOD_GAP_OR_OVERLAP",self.evaluate()["blocker"])

    def test_fractional_fee_period_cannot_be_truncated(self):
        self.cost["fee_periods"][0]["start_ms"]=float(gate.START)+0.25
        self.write_json("account_costs_manifest.json",self.cost)
        self.assertIn("ACCOUNT_FEE_PERIOD_TIMESTAMP_TYPE",self.evaluate()["blocker"])

    def test_boolean_cost_cannot_be_treated_as_one_basis_point(self):
        self.cost["fee_periods"][0]["perp_taker_bps"]=True
        self.write_json("account_costs_manifest.json",self.cost)
        self.assertIn("perp_taker_bps_INVALID",self.evaluate()["blocker"])

    def test_non_object_fee_period_fails_closed(self):
        self.cost["fee_periods"]=[None]
        self.write_json("account_costs_manifest.json",self.cost)
        self.assertIn("ACCOUNT_FEE_PERIOD_SHAPE",self.evaluate()["blocker"])

    def test_symlinked_account_proof_rejected(self):
        p=self.root/"historical_bid_ask_depth.txt"
        original=p.read_bytes();p.unlink()
        target=self.root/"outside_proof.txt";target.write_bytes(original)
        p.symlink_to(target)
        self.assertIn("HISTORICAL_BID_ASK_DEPTH_SHA",self.evaluate()["blocker"])

    def test_missing_depth_evidence_fails(self):
        (self.root/"historical_bid_ask_depth.txt").unlink()
        self.assertIn("HISTORICAL_BID_ASK_DEPTH_SHA",self.evaluate()["blocker"])

    def test_untrusted_host_fails(self):
        self.pages[0]["url"]=self.pages[0]["url"].replace("fapi.binance.com","fake-binance.example")
        self.write_json("native_pages_manifest.json",{"pages":self.pages})
        self.assertIn("NATIVE_ORIGIN_URL",self.evaluate()["blocker"])

if __name__=="__main__":unittest.main()
