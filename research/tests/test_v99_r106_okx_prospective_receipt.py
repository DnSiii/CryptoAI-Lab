"""Synthetic OKX prospective raw data gate; never imports a trading runner."""
from __future__ import annotations
import copy
import hashlib
import json
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import patch

from research.tools import v99_r106_okx_prospective_receipt as o

T=datetime(2026,10,14,20,15,tzinfo=timezone.utc)
def iso(sec): return o.iso(T+timedelta(seconds=sec))
def body(payload): return json.dumps({"code":"0","msg":"","data":payload}).encode()
def response(path,payload,request=1,received=2):
    raw=body(payload)
    return {"url":o.HOST+path,"requested_utc":iso(request),
            "received_utc":iso(received),"raw":raw,
            "sha256":hashlib.sha256(raw).hexdigest(),"byte_count":len(raw),"http":{}}
def candle(hour,confirm="1"):
    t=int(datetime(2026,10,14,hour,tzinfo=timezone.utc).timestamp()*1000)
    return [str(t),"100","103","99","102","250","25000","25500",confirm]
def series():
    return [candle(19,"0")]+[candle(i) for i in (18,17,16,15,14)]

class TestOKXReceipts(unittest.TestCase):
    def test_preregistered_instruments_only(self):
        self.assertIn("BTC-USDT-SWAP",o.candle_path("BTC-USDT-SWAP"))
        with self.assertRaises(ValueError):o.candle_path("LUNA-USDT-SWAP")

    def test_utc_timestamp_required(self):
        with self.assertRaises(ValueError):o.as_utc("2026-10-14T20:15:00")
        with self.assertRaises(ValueError):o.as_utc("2026-10-14T17:15:00-03:00")

    def test_eligibility_t_minus_one(self):
        self.assertEqual(o.safe_eligibility(iso(2)),"2026-10-14T22:00:00+00:00")

    def test_complete_and_unfinished_are_separate(self):
        r=o.validate_candles(response(o.candle_path(o.INSTS[0]),series()),o.INSTS[0])
        self.assertEqual(r["confirmed_candles"],5)
        self.assertEqual(r["unconfirmed_candles"],1)
        self.assertEqual(r["latest_confirmed_close_utc"],"2026-10-14T19:00:00+00:00")

    def test_nonconfirm_rejected(self):
        a=series();a[0][-1]="2"
        with self.assertRaisesRegex(ValueError,"confirm"):o.validate_candles(response(o.candle_path(o.INSTS[0]),a),o.INSTS[0])

    def test_duplicate_hour_rejected(self):
        a=series();a[2][0]=a[1][0]
        with self.assertRaisesRegex(ValueError,"duplicate"):o.validate_candles(response(o.candle_path(o.INSTS[0]),a),o.INSTS[0])

    def test_gap_rejected(self):
        a=series();a.pop(2)
        with self.assertRaisesRegex(ValueError,"gapped"):o.validate_candles(response(o.candle_path(o.INSTS[0]),a),o.INSTS[0])

    def test_future_confirmed_candle_rejected(self):
        a=series();a[0][-1]="1"
        # Bar 19:00 confirmed at 20:15 is legitimate. Change to 20:00.
        a[0][0]=str(int(a[0][0])+3600000)
        with self.assertRaisesRegex(ValueError,"confirmed not yet closed"):
            o.validate_candles(response(o.candle_path(o.INSTS[0]),a),o.INSTS[0])

    def test_negative_volume_rejected(self):
        a=series();a[1][5]="-10"
        with self.assertRaisesRegex(ValueError,"semantics"):o.validate_candles(response(o.candle_path(o.INSTS[0]),a),o.INSTS[0])

    def test_high_below_close_rejected(self):
        a=series();a[1][2]="98"
        with self.assertRaisesRegex(ValueError,"semantics"):o.validate_candles(response(o.candle_path(o.INSTS[0]),a),o.INSTS[0])

    def test_nonfinite_price_rejected(self):
        a=series();a[1][1]="NaN"
        with self.assertRaisesRegex(ValueError,"nonfinite"):o.validate_candles(response(o.candle_path(o.INSTS[0]),a),o.INSTS[0])

    def test_stale_source_candle_rejected(self):
        a=[candle(hour) for hour in (12,11,10,9,8)]
        with self.assertRaisesRegex(ValueError,"stale"):o.validate_candles(response(o.candle_path(o.INSTS[0]),a),o.INSTS[0])

    def test_clock_corroboration(self):
        before=response(o.TIME,[{"ts":str(int((T+timedelta(seconds=1)).timestamp()*1000))}],0,1)
        after=response(o.TIME,[{"ts":str(int((T+timedelta(seconds=8)).timestamp()*1000))}],7,8)
        inbetween=[response(o.candle_path(x),series(),i+1,i+2) for i,x in enumerate(o.INSTS)]
        values=o.corroborate(before,after,inbetween)
        self.assertLess(values["before_ms"],values["after_ms"])

    def test_clock_skew_rejected(self):
        r=response(o.TIME,[{"ts":"1"}])
        with self.assertRaisesRegex(ValueError,"not near"):o.get_clock(r)

    def test_server_clock_rewind_rejected(self):
        before=response(o.TIME,[{"ts":str(int((T+timedelta(seconds=12)).timestamp()*1000))}],0,1)
        after=response(o.TIME,[{"ts":str(int(T.timestamp()*1000))}],7,8)
        with self.assertRaisesRegex(ValueError,"regressed"):
            o.corroborate(before,after,[response(o.candle_path(x),series(),i+1,i+2) for i,x in enumerate(o.INSTS)])

    def test_duplicate_json_keys_rejected(self):
        r=response(o.TIME,[])
        r["raw"]=b'{"code":"0","code":"0","data":[]}'
        with self.assertRaisesRegex(ValueError,"duplicate"):o.parse(r)

    def test_error_code_rejected(self):
        r=response(o.TIME,[])
        r["raw"]=b'{"code":"50011","msg":"rate limit","data":[]}'
        with self.assertRaisesRegex(ValueError,"failure"):o.parse(r)

    def test_complete_synthetic_capture_is_only_data(self):
        seen=[]
        before_ms=int((T+timedelta(seconds=1)).timestamp()*1000)
        after_ms=int((T+timedelta(seconds=8)).timestamp()*1000)
        def fake_get(path):
            i=len(seen);seen.append(path)
            if i==0:return response(o.TIME,[{"ts":str(before_ms)}],0,1)
            if i==6:return response(o.TIME,[{"ts":str(after_ms)}],7,8)
            return response(path,series(),i,i+1)
        with patch.object(o,"fetch",side_effect=fake_get):
            manifest,original=o.acquire()
        self.assertEqual(len(seen),7)
        self.assertEqual(len(original),7)
        self.assertEqual(len(manifest["instruments"]),5)
        self.assertEqual(manifest["earliest_candidate_decision_utc"],"2026-10-14T22:00:00+00:00")
        self.assertFalse(manifest["paper_publication_authorized"])
        self.assertFalse(manifest["original_r106_binance_fee_and_funding_model_transfer_authorized"])
        self.assertFalse(manifest["promotion_authorized"])
        self.assertFalse(manifest["holdout_accessed"])
        self.assertEqual(manifest["economic_trials"],0)
        self.assertEqual(manifest["instruments"]["BTC-USDT-SWAP"]["source_raw_sha256"],
                         original["BTC-USDT-SWAP"]["sha256"])

    def test_forbidden_endpoint_rejected(self):
        with self.assertRaises(ValueError):o.fetch("/api/v5/trade/order")

if __name__=="__main__":unittest.main()
