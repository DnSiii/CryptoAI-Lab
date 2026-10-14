"""Quarantined separate R106 forward epoch: 16 fail-closed structural cases."""
from __future__ import annotations
import copy
import hashlib
import json
import unittest
from datetime import datetime,timezone

from research.tools.v99_r106_epoch2_quarantine import verify,TRACKS

OLD_END="2026-10-10T05:00:00+00:00"
SOURCE="2026-10-14T19:15:00+00:00"
START="2026-10-14T21:00:00+00:00"
NEXT="2026-10-14T22:00:00+00:00"

def data():
    old={"mode":"PAPER_ONLY","real_orders_enabled":False,
         "paper_start_after_timestamp":"2026-09-16T13:00:00+00:00",
         "latest_data_timestamp":OLD_END,"variants":{k:{} for k in TRACKS}}
    old_bytes=json.dumps(old,sort_keys=True).encode()
    ms=int(datetime.fromisoformat(SOURCE).timestamp()*1000)
    exchange={"serverTime":ms,"symbols":[
        {"symbol":sym,"quoteAsset":"USDT","contractType":"PERPETUAL","status":"TRADING"}
        for sym in ("BTCUSDT","ETHUSDT")
    ]}
    raw=json.dumps(exchange,sort_keys=True).encode()
    rows=[{"timestamp":START,"capital_brl":"10000.00",
            "gross_result_brl":"0.00","fees_brl":"0.00",
            "funding_result_brl":"0.00","transfer_result_brl":"0.00",
            "net_result_brl":"0.00"},
          {"timestamp":NEXT,"capital_brl":"10018.50",
           "gross_result_brl":"20.00","fees_brl":"1.00",
           "funding_result_brl":"-0.50","transfer_result_brl":"0.00",
           "net_result_brl":"18.50"}]
    candidate={
        "version":"v99-r106-forward-epoch-v2","mode":"PAPER_ONLY",
        "real_orders_enabled":False,
        "old_immutable_paper_sha256":hashlib.sha256(old_bytes).hexdigest(),
        "new_forward_start_utc":START,
        "first_source_received_utc":SOURCE,
        "first_source_url":"https://fapi.binance.com/fapi/v1/exchangeInfo",
        "first_source_payload_sha256":hashlib.sha256(raw).hexdigest(),
        "variants":{k:{"real_orders_enabled":False,
            "initial_capital_brl":"10000.00",
            "hourly_equity_and_pnl":copy.deepcopy(rows),
            "operations_capped":False,"operation_journal_complete":True,
            "operations":[{"timestamp":NEXT,"symbol":"BTCUSDT","action":"opened"}]}
            for k in TRACKS},
    }
    return old_bytes,candidate,raw

def test(change=None):
    args=list(data())
    if change:change(args[1])
    return verify(*args)

class TestEpoch2(unittest.TestCase):
    def test_pass_is_still_hold_not_publication(self):
        x=test()
        self.assertEqual(x["status"],"STRUCTURE_PASS_QUARANTINE_PENDING_VERIFIED_SOURCE")
        self.assertFalse(x["publication_authorized"])
        self.assertFalse(x["promotion_authorized"])
        self.assertFalse(x["source_first_party_authenticated_independently"])
        self.assertFalse(x["old_published_data_mutated"])
        self.assertEqual(x["economic_trials"],0)
        self.assertEqual(len(x["variants"]),5)

    def test_immutable_old_sha_mismatch(self):
        with self.assertRaisesRegex(ValueError,"legacy paper anchor"):
            test(lambda a:a.update(old_immutable_paper_sha256="0"*64))

    def test_wrong_first_party_receipt_sha(self):
        with self.assertRaisesRegex(ValueError,"raw receipt hash"):
            test(lambda a:a.update(first_source_payload_sha256="0"*64))

    def test_source_not_approved_endpoint(self):
        with self.assertRaisesRegex(ValueError,"first-party endpoint"):
            test(lambda a:a.update(first_source_url="https://untrusted.test/exchangeInfo"))

    def test_causal_first_eligible_bar(self):
        with self.assertRaisesRegex(ValueError,"causal t-1"):
            test(lambda a:a.update(new_forward_start_utc="2026-10-14T20:00:00Z"))

    def test_new_epoch_cannot_restart_inside_legacy(self):
        with self.assertRaisesRegex(ValueError,"new epoch must begin"):
            test(lambda a:a.update(new_forward_start_utc=OLD_END))

    def test_mutated_first_capital_rejected(self):
        with self.assertRaisesRegex(ValueError,"start a NEW"):
            test(lambda a:a["variants"]["f3"]["hourly_equity_and_pnl"][0].update(capital_brl="11641.06"))

    def test_no_inherited_legacy_capital(self):
        with self.assertRaisesRegex(ValueError,"do not inherit"):
            test(lambda a:a["variants"]["f3"].update(initial_capital_brl="11641.06"))

    def test_hourly_accounting_cannot_hide_costs(self):
        with self.assertRaisesRegex(ValueError,"identity broken"):
            test(lambda a:a["variants"]["f1"]["hourly_equity_and_pnl"][1].update(fees_brl="0.00"))

    def test_equity_delta_must_equal_net(self):
        with self.assertRaisesRegex(ValueError,"equity !="):
            test(lambda a:a["variants"]["f1"]["hourly_equity_and_pnl"][1].update(capital_brl="10019.50"))

    def test_negative_fee_rejected(self):
        with self.assertRaisesRegex(ValueError,"fees must"):
            test(lambda a:a["variants"]["f1"]["hourly_equity_and_pnl"][1].update(fees_brl="-1.00"))

    def test_subcent_accounting_rejected(self):
        with self.assertRaisesRegex(ValueError,"sub-cent"):
            test(lambda a:a["variants"]["f7"]["hourly_equity_and_pnl"][1].update(fees_brl="1.001"))

    def test_missing_financial_component_rejected(self):
        def mutate(a):del a["variants"]["f3"]["hourly_equity_and_pnl"][1]["funding_result_brl"]
        with self.assertRaisesRegex(ValueError,"incomplete"):
            test(mutate)

    def test_operation_capping_prohibited(self):
        with self.assertRaisesRegex(ValueError,"journal completeness"):
            test(lambda a:a["variants"]["f3"].update(operations_capped=True))

    def test_duplicate_operations_even_nonadjacent_rejected(self):
        def mutate(a):
            a["variants"]["f3"]["operations"]=[
                {"timestamp":NEXT,"symbol":"BTCUSDT"},
                {"timestamp":NEXT,"symbol":"ETHUSDT"},
                {"timestamp":NEXT,"symbol":"BTCUSDT"}]
        with self.assertRaisesRegex(ValueError,"duplicate"):
            test(mutate)

    def test_no_real_orders(self):
        with self.assertRaisesRegex(ValueError,"simulation only"):
            test(lambda a:a.update(real_orders_enabled=True))

    def test_no_mutation_of_input(self):
        old,new,raw=data()
        before=copy.deepcopy(new)
        verify(old,new,raw)
        self.assertEqual(new,before)

    def test_bad_source_server_time(self):
        old,new,raw=data()
        payload=json.loads(raw)
        payload["serverTime"]=123
        new_raw=json.dumps(payload,sort_keys=True).encode()
        new["first_source_payload_sha256"]=hashlib.sha256(new_raw).hexdigest()
        with self.assertRaisesRegex(ValueError,"server clock"):
            verify(old,new,new_raw)

    def test_duplicate_source_json_key(self):
        old,new,_=data()
        raw=b'{"symbols":[],"symbols":[]}'
        new["first_source_payload_sha256"]=hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError,"malformed first-party"):
            verify(old,new,raw)

if __name__=="__main__":
    unittest.main()
