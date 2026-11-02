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

    def test_authorized_raw_jsonl_uses_same_pinned_expected_calendar(self):
        import v98_authorized_funding_mark_ingest as importer
        saved=(importer.START,importer.END,importer.EXPECTED)
        importer.START=gate.START
        importer.END=gate.START+2*gate.EIGHT_HOURS_MS
        importer.EXPECTED=8
        self.addCleanup(lambda:(setattr(importer,"START",saved[0]),
                                setattr(importer,"END",saved[1]),
                                setattr(importer,"EXPECTED",saved[2])))
        pages=[]
        for page in self.pages:
            raw=(self.root/page["file"]).read_text()
            pages.append({"url":page["url"],"status":200,
                "response_headers":page["response_headers"],
                "retrieved_at_utc":page["retrieved_at_utc"],
                "response_body":raw,
                "response_body_sha256":hashlib.sha256(raw.encode()).hexdigest()})
        (self.root/"native_pages_manifest.json").unlink()
        (self.root/"authorized_funding_pages.jsonl").write_text(
            "\n".join(json.dumps(x) for x in pages)+"\n")
        out=self.evaluate()
        self.assertEqual(out["decision"],
            "PASS_BYTE_AND_CALENDAR_PREFLIGHT_REQUIRES_INDEPENDENT_AUTHENTICATION")
        self.assertEqual(out["native"]["event_count"],8)
        self.assertFalse(out["native"]["exchange_origin_independently_authenticated"])
        self.assertTrue((self.root/"v98_authorized_native_preflight.csv").is_file())

    def test_dual_source_formats_are_rejected(self):
        (self.root/"authorized_funding_pages.jsonl").write_text("{}\n")
        self.assertIn("NATIVE_AMBIGUOUS_SOURCE_FORMAT",self.evaluate()["blocker"])

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


    def _capture_fixture(self, *, block_primary=False, tamper_rate=False, drop_last=False):
        import v98_delivery_native_mark_collector as collector
        import v98_authorized_funding_mark_ingest as importer
        from urllib.parse import urlsplit, parse_qs
        saved=(collector.EXPECTED_COUNT,importer.START,importer.END,importer.EXPECTED,collector.expected_events,collector.END)
        collector.EXPECTED_COUNT=8
        collector.END=gate.START+2*gate.EIGHT_HOURS_MS
        collector.expected_events=gate.expected_events
        importer.START=gate.START
        importer.END=gate.START+2*gate.EIGHT_HOURS_MS
        importer.EXPECTED=8
        self.addCleanup(lambda:(setattr(collector,"EXPECTED_COUNT",saved[0]),
                                setattr(importer,"START",saved[1]),
                                setattr(importer,"END",saved[2]),
                                setattr(importer,"EXPECTED",saved[3]),
                                setattr(collector,"expected_events",saved[4]),
                                setattr(collector,"END",saved[5])))
        calls=[]
        def fetcher(url,timeout):
            q=parse_qs(urlsplit(url).query)
            calls.append((url,q))
            if block_primary and urlsplit(url).hostname=="fapi.binance.com":
                raise RuntimeError("BINANCE_HTTP_451_HOST_fapi.binance.com")
            asset=q["symbol"][0]
            rows=[{"symbol":asset,"fundingTime":t,"fundingRate":"0.00010000",
                   "markPrice":"123.45"} for t in self.ts]
            if tamper_rate and asset=="BTCUSDT":rows[0]["fundingRate"]="0.001"
            if drop_last and asset=="BTCUSDT":rows.pop()
            body=json.dumps(rows).encode()
            return 200,{"Date":"Mon, 02 Nov 2026 00:00:05 GMT"},body,"2026-11-02T00:00:00Z"
        return collector,fetcher,calls

    def test_collector_captures_all_four_assets_with_pinned_calendar(self):
        collector,fetcher,calls=self._capture_fixture()
        out=collector.collect(self.expected,self.expected_sha,self.root/"capture",fetcher)
        self.assertEqual(out["events"],8)
        self.assertEqual(out["source_receipt"],
                         "STRUCTURAL_MATCH_ONLY_ORIGIN_ATTESTATION_REQUIRED")
        self.assertFalse(out["paper_or_live_authorized"])
        self.assertEqual(len(calls),4)
        self.assertTrue(all(int(q["endTime"][0])==collector.END-1 for _,q in calls))
        self.assertTrue((self.root/"capture"/"authorized_funding_pages.jsonl").exists())

    def test_collector_falls_back_to_second_official_host_on_http_451(self):
        collector,fetcher,calls=self._capture_fixture(block_primary=True)
        out=collector.collect(self.expected,self.expected_sha,self.root/"capture",fetcher)
        self.assertEqual(out["events"],8)
        self.assertEqual(len(calls),8)
        self.assertTrue(all("fapi1.binance.com" in p["url"] for p in
            map(json.loads,(self.root/"capture"/"authorized_funding_pages.jsonl").read_text().splitlines())))

    def test_collector_rejects_rate_conflict_without_partial_evidence(self):
        collector,fetcher,_=self._capture_fixture(tamper_rate=True)
        with self.assertRaisesRegex(ValueError,"NATIVE_FUNDING_RATE_CONFLICT"):
            collector.collect(self.expected,self.expected_sha,self.root/"capture",fetcher)
        self.assertFalse((self.root/"capture"/"authorized_funding_pages.jsonl").exists())

    def test_collector_rejects_missing_event_without_partial_evidence(self):
        collector,fetcher,_=self._capture_fixture(drop_last=True)
        with self.assertRaisesRegex(ValueError,"NATIVE_INCOMPLETE"):
            collector.collect(self.expected,self.expected_sha,self.root/"capture",fetcher)
        self.assertFalse((self.root/"capture"/"authorized_funding_pages.jsonl").exists())

    def test_collector_refuses_overwrite_of_existing_native_evidence(self):
        collector,fetcher,_=self._capture_fixture()
        dest=self.root/"capture";dest.mkdir()
        (dest/"native_pages_manifest.json").write_text("{}")
        with self.assertRaises(FileExistsError):
            collector.collect(self.expected,self.expected_sha,dest,fetcher)
        self.assertFalse((dest/"authorized_funding_pages.jsonl").exists())


    def test_manifest_transport_exposes_source_only_exact_mark_csv(self):
        result=self.evaluate()
        p=self.root/"v98_authorized_native_preflight.csv"
        self.assertEqual(result["decision"],
                         "PASS_BYTE_AND_CALENDAR_PREFLIGHT_REQUIRES_INDEPENDENT_AUTHENTICATION")
        self.assertTrue(p.exists())
        self.assertEqual(digest(p),result["native"]["exact_marks_csv_sha256"])
        with p.open(newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),8)
        self.assertEqual(rows[0]["markPrice"],"123.45")
        self.assertFalse(result["paper_or_live_authorized"])

    def test_failed_cost_evidence_does_not_emit_exact_mark_table(self):
        (self.root/"historical_bid_ask_depth.txt").unlink()
        result=self.evaluate()
        self.assertEqual(result["decision"],"HOLD_MISSING_EXTERNAL_EVIDENCE")
        self.assertFalse((self.root/"v98_authorized_native_preflight.csv").exists())

    def test_conflicting_existing_exact_mark_table_is_rejected(self):
        (self.root/"v98_authorized_native_preflight.csv").write_text("TAMPERED")
        result=self.evaluate()
        self.assertEqual(result["decision"],"HOLD_MISSING_EXTERNAL_EVIDENCE")
        self.assertIn("EXACT_MARK_OUTPUT_CONFLICT",result["blocker"])


    def test_collector_multi_page_cursor_is_lossless_and_never_crosses_cutoff(self):
        import v98_delivery_native_mark_collector as collector
        import v98_authorized_funding_mark_ingest as importer
        from urllib.parse import urlsplit,parse_qs
        saved=(gate.EXPECTED_COUNT,gate.PINNED_EXPECTED_FUNDING_SHA256,
               collector.EXPECTED_COUNT,collector.END,collector.MAX_PAGE,
               collector.expected_events,importer.END,importer.EXPECTED)
        self.addCleanup(lambda:(
            setattr(gate,"EXPECTED_COUNT",saved[0]),
            setattr(gate,"PINNED_EXPECTED_FUNDING_SHA256",saved[1]),
            setattr(collector,"EXPECTED_COUNT",saved[2]),
            setattr(collector,"END",saved[3]),
            setattr(collector,"MAX_PAGE",saved[4]),
            setattr(collector,"expected_events",saved[5]),
            setattr(importer,"END",saved[6]),
            setattr(importer,"EXPECTED",saved[7])))
        ts=[gate.START+i*gate.EIGHT_HOURS_MS for i in range(3)]
        with self.expected.open("w",newline="") as f:
            w=csv.writer(f);w.writerow(gate.FIELDS)
            for a in gate.ASSETS:
                for t in ts:w.writerow((a,t,"0.00010000"))
        sha=digest(self.expected)
        gate.EXPECTED_COUNT=collector.EXPECTED_COUNT=importer.EXPECTED=12
        gate.PINNED_EXPECTED_FUNDING_SHA256=sha
        collector.expected_events=gate.expected_events
        collector.END=importer.END=ts[-1]+gate.EIGHT_HOURS_MS
        collector.MAX_PAGE=2
        calls=[]
        def fetcher(url,timeout):
            q=parse_qs(urlsplit(url).query)
            self.assertEqual(int(q["endTime"][0]),collector.END-1)
            self.assertEqual(int(q["limit"][0]),2)
            asset=q["symbol"][0];cursor=int(q["startTime"][0])
            rows=[{"symbol":asset,"fundingTime":t,"fundingRate":"0.00010000",
                   "markPrice":"123.45"} for t in ts if t>=cursor][:2]
            calls.append((asset,cursor,len(rows)))
            return 200,{"Date":"Mon, 02 Nov 2026 00:00:05 GMT"},json.dumps(rows).encode(),"2026-11-02T00:00:00Z"
        out=collector.collect(self.expected,sha,self.root/"multipage",fetcher)
        self.assertEqual(out["events"],12)
        self.assertEqual(out["pages"],8)
        self.assertEqual(len(calls),8)
        self.assertTrue(all(calls[i][1]<calls[i+1][1] for i in (0,2,4,6)))
        self.assertFalse(out["paper_or_live_authorized"])

if __name__=="__main__":unittest.main()
