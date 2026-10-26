"""Research-only I1 native coin replay: independent journal, safety negatives."""
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from research.tools.v99_r106_i1_native_coin_account_replay import (
    Quote, D, account_nav, mark_to_exit, open_vertical, settle, start_wallet,
)
from research.verification.independent_v99_r106_i1_native_coin_account_oracle import audit

UTC = timezone.utc


def ms(iso):
    return int(datetime.fromisoformat(iso).timestamp()*1000)


OPEN1 = ms("2022-01-03T00:00:00+00:00")
OPEN2 = ms("2022-01-10T00:00:00+00:00")
MARK = ms("2022-01-10T00:01:00+00:00")
EXPIRY = ms("2022-02-04T08:00:00+00:00")


def quote(strike, bid, ask, at, index="46000", asset="BTC"):
    expiry = "04FEB22"
    return Quote(asset, f"{asset}-{expiry}-{strike}-P", EXPIRY, D(strike),
                 D(bid), D(ask), D("10"), D("10"),
                 at-3000, at-2000, D(index))


def exercise(scenario="severe"):
    w = start_wallet("BTC", scenario, "100")
    trace = {"asset":"BTC", "scenario":scenario, "initial_coin":"100", "events":[]}
    s1, l1 = quote("50000", ".08", ".09", OPEN1), quote("45000", ".04", ".05", OPEN1)
    w = open_vertical(w, "p1", s1, l1, OPEN1, "1", ".001", ".001", "4", "2")
    trace["events"].append(dict(kind="open", at_ms=OPEN1, name="p1",
        qty="1", high="50000", low="45000", short_bid_coin=".08",
        long_ask_coin=".05", entry_fees_coin=".001",
        entry_slippage_coin=".001", margin_coin="4", maintenance_coin="2",
        expiry_ms=EXPIRY))
    s2, l2 = quote("48000", ".09", ".10", OPEN2), quote("43000", ".04", ".05", OPEN2)
    w = open_vertical(w, "p2", s2, l2, OPEN2, "1", ".001", ".001", "4", "2")
    trace["events"].append(dict(kind="open", at_ms=OPEN2, name="p2",
        qty="1", high="48000", low="43000", short_bid_coin=".09",
        long_ask_coin=".05", entry_fees_coin=".001",
        entry_slippage_coin=".001", margin_coin="4", maintenance_coin="2",
        expiry_ms=EXPIRY))
    marks = [
        ("p1", quote("50000", ".08", ".09", MARK),
               quote("45000", ".04", ".05", MARK), ".09", ".04"),
        ("p2", quote("48000", ".09", ".10", MARK),
               quote("43000", ".04", ".05", MARK), ".10", ".04"),
    ]
    for name, short, long, ask, bid in marks:
        w = mark_to_exit(w, name, short, long, MARK, ".001", ".001")
        trace["events"].append(dict(kind="mark", name=name, at_ms=MARK,
            short_ask_coin=ask, long_bid_coin=bid, exit_fees_coin=".001",
            exit_slippage_coin=".001", index_usd="46000"))
    nav = account_nav(w, MARK)
    trace["events"].append(dict(kind="nav", at_ms=MARK))
    for name in ("p1", "p2"):
        w = settle(w, name, EXPIRY, "46000", ".0001")
        trace["events"].append(dict(kind="settle", name=name, at_ms=EXPIRY,
            delivery_index_usd="46000", delivery_fee_coin=".0001"))
    observed = {"cash_coin":str(w.cash_coin), "reserved_coin":str(w.reserved_coin),
                "open_position_ids":[p.name for p in w.positions],
                "settled_ids":list(w.settled), "snapshots":[nav],
                "historical_economic_train":False, "promotion_authorized":False}
    return trace, observed, w


class NativeCoinAccountTests(unittest.TestCase):
    def test_independent_two_overlapping_positions_and_same_expiry(self):
        for scenario in ("severe", "supersevere"):
            trace, observed, w = exercise(scenario)
            self.assertEqual(audit(trace, observed)["independent_coin_account_replay"], "MATCH")
            self.assertEqual(w.reserved_coin, Decimal(0))
            self.assertEqual(w.settled, ("p1","p2"))

    def test_oracle_rejects_fabricated_coin_cash(self):
        trace, observed, _ = exercise()
        observed["cash_coin"] = str(D(observed["cash_coin"])+D("1"))
        with self.assertRaisesRegex(AssertionError, "JOURNAL_MISMATCH"):
            audit(trace, observed)

    def test_oracle_rejects_fabricated_nav(self):
        trace, observed, _ = exercise()
        observed["snapshots"][0]["nav_coin"] = "99999"
        with self.assertRaisesRegex(AssertionError, "NAV_MISMATCH"):
            audit(trace, observed)

    def test_oracle_rejects_hidden_entry_fee(self):
        trace, observed, _ = exercise()
        trace["events"][0]["entry_fees_coin"] = "0"
        with self.assertRaisesRegex(AssertionError, "JOURNAL_MISMATCH"):
            audit(trace, observed)

    def test_rejects_unattested_lot_or_double_spent_coin(self):
        w = start_wallet("BTC", "severe", "5")
        s, l = quote("50000",".08",".09",OPEN1), quote("45000",".04",".05",OPEN1)
        with self.assertRaisesRegex(ValueError, "COLLATERAL"):
            open_vertical(w,"p",s,l,OPEN1,"1",".001",".001","6","3")
        with self.assertRaisesRegex(ValueError, "DEPTH"):
            open_vertical(w,"p",s,l,OPEN1,"11",".001",".001","1",".5")

    def test_rejects_stale_and_future_source(self):
        w = start_wallet("BTC", "severe", "100")
        s, l = quote("50000",".08",".09",OPEN1), quote("45000",".04",".05",OPEN1)
        with self.assertRaisesRegex(ValueError, "NONCAUSAL"):
            open_vertical(w,"p",replace(s,arrival_ms=OPEN1+1),l,
                          OPEN1,"1",".001",".001","4","2")
        with self.assertRaisesRegex(ValueError, "NONCAUSAL"):
            open_vertical(w,"p",replace(s,arrival_ms=OPEN1-400000,
                                       venue_ms=OPEN1-401000),l,
                          OPEN1,"1",".001",".001","4","2")

    def test_rejects_maintenance_breach_without_liquidation_terms(self):
        w = start_wallet("BTC", "severe", "100")
        s, l = quote("50000",".08",".09",OPEN1), quote("45000",".04",".05",OPEN1)
        w = open_vertical(w,"p",s,l,OPEN1,"1",".001",".001","4","2")
        w = mark_to_exit(w,"p",quote("50000",".08",".09",MARK),
                         quote("45000",".04",".05",MARK),
                         MARK,"101","0")
        with self.assertRaisesRegex(ValueError, "MAINTENANCE_BREACH"):
            account_nav(w,MARK)

    def test_rejects_unbound_source_index(self):
        w = start_wallet("BTC", "severe", "100")
        s, l = quote("50000",".08",".09",OPEN1), quote("45000",".04",".05",OPEN1)
        w = open_vertical(w,"p",s,l,OPEN1,"1",".001",".001","4","2")
        with self.assertRaisesRegex(ValueError,"UNSYNCHRONIZED"):
            mark_to_exit(w,"p",quote("50000",".08",".09",MARK),
                         quote("45000",".04",".05",MARK,index="47000"),
                         MARK,".001",".001")

    def test_rejects_cross_asset_coin_netted_as_collateral(self):
        w = start_wallet("BTC","severe","100")
        s = quote("50000",".08",".09",OPEN1,asset="ETH")
        l = quote("45000",".04",".05",OPEN1,asset="ETH")
        with self.assertRaisesRegex(ValueError,"WRONG_COIN"):
            open_vertical(w,"p",s,l,OPEN1,"1",".001",".001","4","2")


if __name__ == "__main__":
    unittest.main()
