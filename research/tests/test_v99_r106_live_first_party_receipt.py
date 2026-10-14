"""Adversarial DATA_ONLY receipt tests; every network response is synthesized."""
import hashlib
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from research.tools import v99_r106_live_first_party_receipt as capture

T=datetime(2026,10,14,19,15,0,tzinfo=timezone.utc)
CORE=capture.CORE

def at(seconds):
    return capture.iso(T+timedelta(seconds=seconds))

def sample_receipt(path, payload, request=0, received=1, headers=None):
    raw=json.dumps(payload,separators=(",",":")).encode()
    return {"url":capture.BASE+path,"requested_utc":at(request),
            "received_utc":at(received),"duration_ms":(received-request)*1000,
            "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
            "response_headers": headers or {"date": None}, "raw":raw}

def row(h):
    start=datetime(2026,10,14,h,0,0,tzinfo=timezone.utc)
    t=int(start.timestamp()*1000)
    return [t,"10","12","9","11","123",t+3599999,"1400",22,"70","900","0"]

def response_map():
    srv1=int((T+timedelta(seconds=1)).timestamp()*1000)
    srv2=int((T+timedelta(seconds=7)).timestamp()*1000)
    return {
        "/fapi/v1/time": [
            sample_receipt("/fapi/v1/time",{"serverTime":srv1},0,1),
            sample_receipt("/fapi/v1/time",{"serverTime":srv2},6,7)
        ],
        "/fapi/v1/exchangeInfo":[sample_receipt(
            "/fapi/v1/exchangeInfo",{"symbols":[{
                "symbol":sym,"contractType":"PERPETUAL",
                "quoteAsset":"USDT","status":"TRADING","onboardDate":1672531200000,
            } for sym in CORE]},1,2)],
        **{"/fapi/v1/klines?symbol="+symbol+"&interval=1h&limit=3":[
            sample_receipt("/fapi/v1/klines?symbol="+symbol+"&interval=1h&limit=3",
                           [row(17),row(18),row(19)],2,3)] for symbol in CORE},
    }


class TestFirstPartyReceipt(unittest.TestCase):
    def test_safe_eligibility_is_next_full_bar(self):
        self.assertEqual(capture.first_safe_decision(at(2)),"2026-10-14T21:00:00+00:00")

    def test_onboard_date_does_not_backdate_observation(self):
        listed=capture.listed_symbols(capture.decode(response_map()["/fapi/v1/exchangeInfo"][0]),at(2))
        self.assertEqual(len(listed),5)
        for item in listed.values():
            self.assertEqual(item["first_directly_observed_in_this_snapshot_utc"],at(2))
            self.assertEqual(item["earliest_eligible_after_receipt_t_minus_1_utc"],
                             "2026-10-14T21:00:00+00:00")
            self.assertNotEqual(item["onboard_date_metadata_ms_NOT_a_discovery_receipt"],
                                int(T.timestamp()*1000))

    def test_no_unfinished_candle_admitted(self):
        rows=capture.fully_closed_klines([row(17),row(18),row(19)],at(3),"BTCUSDT")
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[-1]["open_utc"],"2026-10-14T18:00:00+00:00")

    def test_nonhourly_candle_rejected(self):
        bad=row(18);bad[6]-=1000
        with self.assertRaisesRegex(ValueError,"non-hourly"):
            capture.fully_closed_klines([bad],at(3),"BTCUSDT")

    def test_duplicate_candle_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            capture.fully_closed_klines([row(18),row(18)],at(3),"BTCUSDT")

    def test_unfinished_only_fails(self):
        with self.assertRaisesRegex(ValueError,"no fully closed"):
            capture.fully_closed_klines([row(19)],at(3),"BTCUSDT")

    def test_duplicate_exchange_symbol_rejected(self):
        item={"symbol":"BTCUSDT","contractType":"PERPETUAL","quoteAsset":"USDT",
              "status":"TRADING","onboardDate":123}
        with self.assertRaisesRegex(ValueError,"duplicate"):
            capture.listed_symbols({"symbols":[item,item]},at(2))

    def test_nontrading_listing_not_eligible(self):
        item={"symbol":"BTCUSDT","contractType":"PERPETUAL","quoteAsset":"USDT",
              "status":"BREAK","onboardDate":123}
        with self.assertRaisesRegex(ValueError,"empty as-of universe"):
            capture.listed_symbols({"symbols":[item]},at(2))

    def test_missing_onboard_date_fails(self):
        item={"symbol":"BTCUSDT","contractType":"PERPETUAL","quoteAsset":"USDT",
              "status":"TRADING"}
        with self.assertRaisesRegex(ValueError,"onboardDate"):
            capture.listed_symbols({"symbols":[item]},at(2))

    def test_server_clock_skew_fails(self):
        inputs=response_map()
        bad=sample_receipt("/fapi/v1/time",{"serverTime":10000},6,7)
        with self.assertRaisesRegex(ValueError,"clocks disagree"):
            capture.corroborate_times(inputs["/fapi/v1/time"][0],bad,at(0),at(8))

    def test_reversed_server_time_fails(self):
        inputs=response_map()
        before=sample_receipt("/fapi/v1/time",{"serverTime":int((T+timedelta(seconds=9)).timestamp()*1000)},0,1)
        after=sample_receipt("/fapi/v1/time",{"serverTime":int(T.timestamp()*1000)},6,7)
        with self.assertRaises(ValueError):
            capture.corroborate_times(before,after,at(0),at(8))

    def test_window_too_long_fails_closed(self):
        a,b=response_map()["/fapi/v1/time"]
        with self.assertRaisesRegex(ValueError,"exceeds"):
            capture.corroborate_times(a,b,at(0),at(61))

    def test_bad_timestamp_without_utc_rejected(self):
        with self.assertRaisesRegex(ValueError,"UTC"):
            capture.utc("2026-10-14T19:15:00")

    def test_duplicate_source_json_key_rejected(self):
        item=sample_receipt("/fapi/v1/time",{})
        item["raw"]=b'{"serverTime":1,"serverTime":2}'
        with self.assertRaisesRegex(ValueError,"duplicate"):
            capture.decode(item)

    def test_nonfinite_source_json_rejected(self):
        item=sample_receipt("/fapi/v1/time",{})
        item["raw"]=b'{"serverTime":NaN}'
        with self.assertRaisesRegex(ValueError,"non-finite"):
            capture.decode(item)

    def test_first_party_endpoint_allowlist(self):
        for p in ("/fapi/v1/order","/fapi/v2/account","https://evil.org"):
            with self.subTest(p=p),self.assertRaises(ValueError):
                capture.http_get(p)

    def test_acquire_full_synthetic_snapshot_has_no_trade_or_holdout(self):
        responses=response_map()
        seen=[]
        def fake_get(path):
            seen.append(path)
            return responses[path].pop(0)
        with patch.object(capture,"http_get",side_effect=fake_get),\
             patch.object(capture,"stamp",side_effect=[T,T+timedelta(seconds=8)]):
            manifest, raw=capture.acquire()
        self.assertEqual(len(seen),8)
        self.assertEqual(manifest["universe_total_eligible_at_observation"],5)
        self.assertEqual(set(manifest["fully_closed_klines"]),set(CORE))
        self.assertEqual(manifest["earliest_safe_decision_utc"],"2026-10-14T21:00:00+00:00")
        self.assertEqual(len(raw),8)
        self.assertFalse(manifest["independently_exchange_signed"])
        self.assertFalse(manifest["paper_publication_authorized"])
        self.assertFalse(manifest["promotion_authorized"])
        self.assertFalse(manifest["training_or_holdout_accessed"])
        self.assertEqual(manifest["economic_trials"],0)
        self.assertEqual(manifest["kline_receipts"]["BTCUSDT"]["sha256"],
                         hashlib.sha256(raw["klines_BTCUSDT"]["raw"]).hexdigest())

    def test_no_private_endpoints_anywhere(self):
        script=capture.__file__
        text=open(script,encoding="utf-8").read()
        for token in ("fapi/v1/order","new_order(","API_KEY","api_secret"):
            self.assertNotIn(token,text)


if __name__=="__main__":
    unittest.main()
