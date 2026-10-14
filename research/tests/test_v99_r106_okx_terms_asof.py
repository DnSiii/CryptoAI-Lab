"""OKX native contract/funding as-of gate: no economic results, synthetic data."""
from __future__ import annotations
import hashlib
import json
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import patch

from research.tools import v99_r106_okx_terms_asof as n
from research.tools import v99_r106_okx_prospective_receipt as o

T=datetime(2026,10,14,20,25,0,tzinfo=timezone.utc)
def at(seconds):
    return o.iso(T+timedelta(seconds=seconds))
def resp(path,values,start=1,end=2):
    raw=json.dumps({"code":"0","data":values}).encode()
    return {"url":o.HOST+path,"requested_utc":at(start),
            "received_utc":at(end),"raw":raw,
            "sha256":hashlib.sha256(raw).hexdigest(),
            "byte_count":len(raw)}
def valid_meta(inst):
    return {"instId":inst,"ctType":"linear","state":"live","settleCcy":"USDT",
            "ctVal":"0.01","ctValCcy":"BTC","lotSz":"1","minSz":"1","tickSz":"0.1"}
def valid_fund(inst):
    time=int((T+timedelta(hours=3)).timestamp()*1000)
    return {"instId":inst,"fundingRate":"0.0001",
            "fundingTime":str(time),"nextFundingTime":str(time+4*3600000)}
def server(time):
    return [{"ts":str(int((T+timedelta(seconds=time)).timestamp()*1000))}]

class TestOKXNativeTerms(unittest.TestCase):
    def test_exact_allowlisted_paths(self):
        self.assertIn("BTC-USDT-SWAP",n.path_meta(o.INSTS[0]))
        with self.assertRaises(ValueError):n.path_meta("FAKE-USDT-SWAP")
        with self.assertRaises(ValueError):n.path_fund("FAKE-USDT-SWAP")
        with self.assertRaises(ValueError):n.fetch("/api/v5/trade/order")

    def test_live_usdt_swap_contract_valid(self):
        x=n.verify_contract(resp(n.path_meta(o.INSTS[0]),[valid_meta(o.INSTS[0])]),o.INSTS[0])
        self.assertEqual(x["ctVal"],"0.01")
        self.assertEqual(x["settleCcy"],"USDT")

    def test_nonlive_instrument_rejected(self):
        x=valid_meta(o.INSTS[0]);x["state"]="suspend"
        with self.assertRaisesRegex(ValueError,"live linear"):
            n.verify_contract(resp(n.path_meta(o.INSTS[0]),[x]),o.INSTS[0])

    def test_inverse_instrument_rejected(self):
        x=valid_meta(o.INSTS[0]);x["ctType"]="inverse"
        with self.assertRaisesRegex(ValueError,"live linear"):
            n.verify_contract(resp(n.path_meta(o.INSTS[0]),[x]),o.INSTS[0])

    def test_negative_or_zero_contract_values(self):
        x=valid_meta(o.INSTS[0]);x["ctVal"]="0"
        with self.assertRaisesRegex(ValueError,"nonpositive"):
            n.verify_contract(resp(n.path_meta(o.INSTS[0]),[x]),o.INSTS[0])

    def test_native_contract_bad_precision_rejected(self):
        x=valid_meta(o.INSTS[0]);x["tickSz"]="NaN"
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            n.verify_contract(resp(n.path_meta(o.INSTS[0]),[x]),o.INSTS[0])

    def test_forecast_funding_is_not_cashflow(self):
        x=n.verify_current_funding(resp(n.path_fund(o.INSTS[0]),[valid_fund(o.INSTS[0])]),o.INSTS[0])
        self.assertEqual(x["observed_rate_not_settled"],"0.0001")
        self.assertFalse(x["settled_cashflow_authenticated"])

    def test_bad_funding_inst(self):
        x=valid_fund(o.INSTS[0]);x["instId"]="SOMEOTHER"
        with self.assertRaisesRegex(ValueError,"mismatch"):
            n.verify_current_funding(resp(n.path_fund(o.INSTS[0]),[x]),o.INSTS[0])

    def test_future_notice_too_far_rejected(self):
        x=valid_fund(o.INSTS[0])
        x["fundingTime"]=str(int((T+timedelta(days=7)).timestamp()*1000))
        with self.assertRaisesRegex(ValueError,"48-hour"):
            n.verify_current_funding(resp(n.path_fund(o.INSTS[0]),[x]),o.INSTS[0])

    def test_nonincreasing_funding_schedule_rejected(self):
        x=valid_fund(o.INSTS[0])
        x["nextFundingTime"]=x["fundingTime"]
        with self.assertRaisesRegex(ValueError,"increasing"):
            n.verify_current_funding(resp(n.path_fund(o.INSTS[0]),[x]),o.INSTS[0])

    def test_absurd_funding_rate_rejected(self):
        x=valid_fund(o.INSTS[0]);x["fundingRate"]="2.0"
        with self.assertRaisesRegex(ValueError,"plausible"):
            n.verify_current_funding(resp(n.path_fund(o.INSTS[0]),[x]),o.INSTS[0])

    def test_full_synthetic_terms_acquisition_data_only(self):
        requests=[]
        def fake(path):
            i=len(requests)
            requests.append(path)
            if path==o.TIME:
                return resp(path,server(i+1),i,i+1)
            inst=next(x for x in o.INSTS if x in path)
            return resp(path,[valid_fund(inst) if path.startswith(n.FUND_PATH) else valid_meta(inst)],i,i+1)
        with patch.object(n,"fetch",side_effect=fake):
            manifest,original=n.acquire()
        self.assertEqual(len(requests),12)
        self.assertEqual(len(original),12)
        self.assertEqual(len(manifest["contracts"]),5)
        self.assertEqual(manifest["earliest_safe_decision_utc"],"2026-10-14T22:00:00+00:00")
        self.assertFalse(manifest["fee_schedule_independently_proven"])
        self.assertFalse(manifest["funding_cashflows_settled_and_pit_authenticated"])
        self.assertFalse(manifest["binance_r106_parameters_crossvenue_transfer_authorized"])
        self.assertFalse(manifest["paper_publication_authorized"])
        self.assertFalse(manifest["holdout_accessed"])

    def test_no_real_trading(self):
        text=open(n.__file__,encoding="utf8").read()
        for word in ("new_order(","api_secret","API_KEY","create_order("):
            self.assertNotIn(word,text)

if __name__=="__main__":
    unittest.main()
