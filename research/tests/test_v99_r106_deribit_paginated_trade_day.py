"""Adversarial, offline controls for original Deribit trade pagination; never trading."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research.tools import v99_r106_deribit_paginated_trade_day as primary
from research.verification import independent_v99_r106_deribit_paginated_trade_day_oracle as oracle


def trade(coin, tid, ts, strike="30000"):
    return dict(trade_id=tid, timestamp=ts, instrument_name=f"{coin}-25FEB22-{strike}-P",
                price=0.012, amount=1.0)


def page(trades, more=False):
    return json.dumps(dict(jsonrpc="2.0", result=dict(trades=trades, has_more=more)),
                      separators=(",", ":")).encode()


def state():
    return dict(ids={}, boundary={}, eligible={})


class TestOriginalPagination(unittest.TestCase):
    def test_valid_first_and_overlap_second_page(self):
        st = state()
        t = primary.DAY_START + 1000
        last, more, new, count = primary.add_page(
            st, page([trade("BTC","a",t),trade("BTC","b",t+1)], True), "BTC", None)
        self.assertEqual((last,more,new,count), (t+1,True,2,2))
        last,more,new,count = primary.add_page(st,
            page([trade("BTC","b",t+1),trade("BTC","c",t+2,"35000")]),
            "BTC", t+1)
        self.assertEqual((new,len(st["ids"]),more), (1,3,False))
        self.assertEqual(st["eligible"]["2022-02-25"], {"30000","35000"})

    def test_reject_missing_inclusive_overlap(self):
        st=state(); t=primary.DAY_START+100
        primary.add_page(st,page([trade("BTC","a",t)],True),"BTC",None)
        with self.assertRaisesRegex(ValueError,"MISSING_INCLUSIVE"):
            primary.add_page(st,page([trade("BTC","b",t+1)]),"BTC",t)

    def test_reject_conflicting_boundary_duplicate(self):
        st=state(); t=primary.DAY_START+100
        primary.add_page(st,page([trade("BTC","a",t)],True),"BTC",None)
        bad=trade("BTC","a",t);bad["price"]=0.99
        with self.assertRaisesRegex(ValueError,"AMBIGUOUS_TIMESTAMP"):
            primary.add_page(st,page([bad,trade("BTC","b",t+1)]),"BTC",t)

    def test_reject_stuck_cursor(self):
        st=state(); t=primary.DAY_START+100
        primary.add_page(st,page([trade("BTC","a",t)],True),"BTC",None)
        with self.assertRaisesRegex(ValueError,"STUCK_CURSOR"):
            primary.add_page(st,page([trade("BTC","a",t)]),"BTC",t)

    def test_reject_cross_day(self):
        with self.assertRaisesRegex(ValueError,"OUTSIDE_FIXED_TRAIN_DAY"):
            primary.parse(page([trade("ETH","a",primary.DAY_END)]),"ETH")

    def test_reject_missing_id(self):
        bad=trade("ETH","a",primary.DAY_START);bad.pop("trade_id")
        with self.assertRaisesRegex(ValueError,"MISSING_OR_DUPLICATE"):
            primary.parse(page([bad]),"ETH")

    def test_reject_missing_has_more(self):
        raw=json.dumps(dict(result=dict(trades=[trade("ETH","a",primary.DAY_START)]))).encode()
        with self.assertRaisesRegex(ValueError,"MISSING_HAS_MORE"):
            primary.parse(raw,"ETH")

    def test_independent_replay_and_forged_status(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);rawdir=root/"raw_ephemeral";rawdir.mkdir()
            rows=[]
            for coin in ("BTC","ETH"):
                raw=page([trade(coin,coin+"1",primary.DAY_START+10,"30000"),
                          trade(coin,coin+"2",primary.DAY_START+11,"35000")])
                name=f"{coin}_000.json";(rawdir/name).write_bytes(raw)
                rows.append(dict(currency=coin,day="2022-01-23",
                    status="COMPLETE_REPORTED_TRADE_PAGINATION",
                    pages=[dict(file=name,sha256=hashlib.sha256(raw).hexdigest(),
                        cursor=None,last_timestamp=primary.DAY_START+11,returned=2,
                        unique_new=2,has_more=False)],page_count=1,unique_trade_prints=2,
                    first_timestamp=primary.DAY_START+10,last_timestamp=primary.DAY_START+11,
                    eligible_28_35d_put_strikes_by_expiry={"2022-02-25":2},
                    eligible_two_distinct_traded_put_strikes=True,error=None))
            report=dict(schema="V99_R106_DERIBIT_ORIGINAL_PAGINATED_TRADE_DAY_SOURCE_ONLY_V1",
                status="TRADE_ACTIVITY_FEASIBLE_QUOTES_STILL_MISSING",rows=rows,
                original_661_day_quote_archive_delivered=False,certified_option_lifecycles=0,
                trade_prints_are_not_executable_quotes=True,
                api_reported_complete_is_not_market_quote_coverage=True,**primary.FORBIDDEN)
            path=root/"original_paginated_trade_day_source_only.json"
            path.write_text(json.dumps(report))
            self.assertEqual(oracle.verify(root)["status"],
                "INDEPENDENT_ORIGINAL_PAGINATED_TRADE_BYTES_REPLAY_PASS")
            report["rows"][0]["pages"][0]["has_more"]=True
            path.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,"ORACLE_FORGED_PAGE_META"):
                oracle.verify(root)


if __name__ == "__main__":
    unittest.main()
