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
        short_ask_coin=".09", long_bid_coin=".04", index_usd="46000",
        long_ask_coin=".05", entry_fees_coin=".001",
        entry_slippage_coin=".001", margin_coin="4", maintenance_coin="2",
        expiry_ms=EXPIRY))
    # Re-mark all existing exposure at the next Monday before adding risk.
    w = mark_to_exit(w, "p1", quote("50000",".08",".09",OPEN2),
                     quote("45000",".04",".05",OPEN2),
                     OPEN2, ".001", ".001")
    trace["events"].append(dict(kind="mark", name="p1", at_ms=OPEN2,
        short_ask_coin=".09", long_bid_coin=".04", exit_fees_coin=".001",
        exit_slippage_coin=".001", index_usd="46000"))
    s2, l2 = quote("48000", ".09", ".10", OPEN2), quote("43000", ".04", ".05", OPEN2)
    w = open_vertical(w, "p2", s2, l2, OPEN2, "1", ".001", ".001", "4", "2")
    trace["events"].append(dict(kind="open", at_ms=OPEN2, name="p2",
        qty="1", high="48000", low="43000", short_bid_coin=".09",
        short_ask_coin=".10", long_bid_coin=".04", index_usd="46000",
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

    def test_forged_negative_liability_cannot_inflate_native_nav(self):
        w = start_wallet("BTC", "severe", "4")
        s, l = quote("50000", ".08", ".09", OPEN1), quote("45000", ".04", ".05", OPEN1)
        w = open_vertical(w, "p1", s, l, OPEN1, "1", ".001", ".001", "2", "1")
        forged = replace(w, marks=(("p1", D("-999"), OPEN1, D("46000")),))
        with self.assertRaisesRegex(ValueError, "INVALID_COIN_MARK_PROVENANCE"):
            account_nav(forged, OPEN1)

    def test_forged_mark_index_and_clock_fail_closed(self):
        w = start_wallet("BTC", "severe", "100")
        s, l = quote("50000", ".08", ".09", OPEN1), quote("45000", ".04", ".05", OPEN1)
        w = open_vertical(w, "p1", s, l, OPEN1, "1", ".001", ".001", "4", "2")
        for index, clock in (("0", OPEN1), ("-1", OPEN1), ("46000", True),
                             ("46000", OPEN1 + 1)):
            forged = replace(w, marks=(("p1", D(".05"), clock, D(index)),))
            with self.assertRaisesRegex(ValueError, "INVALID_COIN_MARK_PROVENANCE"):
                forged.check()

    def test_forged_open_position_terms_fail_closed(self):
        w = start_wallet("BTC", "severe", "100")
        s, l = quote("50000", ".08", ".09", OPEN1), quote("45000", ".04", ".05", OPEN1)
        w = open_vertical(w, "p1", s, l, OPEN1, "1", ".001", ".001", "4", "2")
        for field, value in (("qty", D("0")), ("high", D("43000")),
                             ("maintenance_margin_coin", D("5")),
                             ("expiry_ms", True)):
            forged = replace(w, positions=(replace(w.positions[0], **{field: value}),))
            with self.assertRaisesRegex(ValueError, "INVALID_OPEN_COIN_POSITION"):
                forged.check()

    def test_independent_oracle_rejects_negative_mark_fee_or_bad_index(self):
        for field, value in (("exit_fees_coin", "-1"),
                             ("exit_slippage_coin", "-1"),
                             ("index_usd", "0")):
            trace, observed, _ = exercise()
            next(e for e in trace["events"] if e["kind"] == "mark")[field] = value
            with self.assertRaisesRegex(AssertionError, "INVALID_REFERENCE_MARK_PROVENANCE"):
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

    def test_rejects_overlapping_open_without_fresh_mark(self):
        w = start_wallet("BTC", "severe", "100")
        s, l = quote("50000",".08",".09",OPEN1), quote("45000",".04",".05",OPEN1)
        w = open_vertical(w,"p1",s,l,OPEN1,"1",".001",".001","4","2")
        s2, l2 = quote("48000",".09",".10",OPEN2), quote("43000",".04",".05",OPEN2)
        with self.assertRaisesRegex(ValueError,"PRETRADE_ALL_POSITION_MARKS_REQUIRED"):
            open_vertical(w,"p2",s2,l2,OPEN2,"1",".001",".001","4","2")

    def test_rejects_maintenance_breach_without_liquidation_terms(self):
        w = start_wallet("BTC", "severe", "100")
        s, l = quote("50000",".08",".09",OPEN1), quote("45000",".04",".05",OPEN1)
        w = open_vertical(w,"p",s,l,OPEN1,"1",".001",".001","4","2")
        w = mark_to_exit(w,"p",quote("50000",".08",".09",MARK),
                         quote("45000",".04",".05",MARK),
                         MARK,"101","0")
        with self.assertRaisesRegex(ValueError, "MAINTENANCE_BREACH"):
            account_nav(w,MARK)

    def test_postentry_maintenance_veto_even_when_cash_covers_reserve(self):
        # 4 coin cash + .028 net credit covers 4 coin reserve, but
        # the same original book implies >=.05 coin close liability.
        w = start_wallet("BTC", "severe", "4")
        s, l = quote("50000", ".08", ".09", OPEN1), quote("45000", ".04", ".05", OPEN1)
        with self.assertRaisesRegex(ValueError, "POSTENTRY_MAINTENANCE_LOWER_BOUND_BREACH"):
            open_vertical(w, "bad", s, l, OPEN1, "1", ".001", ".001", "4", "4")

    def test_oracle_independently_rejects_postentry_maintenance_breach(self):
        trace, observed, _ = exercise()
        trace["initial_coin"] = "4"
        trace["events"][0]["maintenance_coin"] = "4"
        with self.assertRaisesRegex(AssertionError, "POSTENTRY_REFERENCE_MAINTENANCE_BREACH"):
            audit(trace, observed)

    def test_overlapping_entry_requires_exact_existing_mark_index(self):
        w = start_wallet("BTC", "severe", "100")
        s, l = quote("50000", ".08", ".09", OPEN1), quote("45000", ".04", ".05", OPEN1)
        w = open_vertical(w, "p1", s, l, OPEN1, "1", ".001", ".001", "4", "2")
        w = mark_to_exit(w, "p1", quote("50000", ".08", ".09", OPEN2),
                         quote("45000", ".04", ".05", OPEN2), OPEN2, ".001", ".001")
        s2 = quote("48000", ".09", ".10", OPEN2, index="47000")
        l2 = quote("43000", ".04", ".05", OPEN2, index="47000")
        with self.assertRaisesRegex(ValueError, "POSTENTRY_UNBOUND_UNDERLYING_INDEX"):
            open_vertical(w, "p2", s2, l2, OPEN2, "1", ".001", ".001", "4", "2")

    def test_oracle_independently_rejects_overlapping_index_mismatch(self):
        trace, observed, _ = exercise()
        # Existing p1 mark at OPEN2 is source-bound to 46000;
        # a new p2 opening cannot silently net a 47000 underlying.
        opens = [e for e in trace["events"] if e["kind"] == "open"]
        self.assertEqual(len(opens), 2)
        opens[1]["index_usd"] = "47000"
        with self.assertRaisesRegex(AssertionError, "POSTENTRY_REFERENCE_UNBOUND_INDEX"):
            audit(trace, observed)

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


    def test_cross_expiry_settlement_requires_fresh_survivor_mark_and_index(self):
        expiry2 = ms("2022-02-11T08:00:00+00:00")
        def later(strike, bid, ask, at, index="46000"):
            return Quote("BTC", f"BTC-11FEB22-{strike}-P", expiry2, D(strike),
                         D(bid), D(ask), D("10"), D("10"),
                         at-3000, at-2000, D(index))
        w = start_wallet("BTC", "severe", "100")
        w = open_vertical(w, "p1", quote("50000",".08",".09",OPEN1),
                          quote("45000",".04",".05",OPEN1), OPEN1,
                          "1",".001",".001","4","2")
        w = mark_to_exit(w, "p1", quote("50000",".08",".09",OPEN2),
                         quote("45000",".04",".05",OPEN2), OPEN2,
                         ".001",".001")
        w = open_vertical(w, "p2", later("48000",".09",".10",OPEN2),
                          later("43000",".04",".05",OPEN2), OPEN2,
                          "1",".001",".001","4","2")
        with self.assertRaisesRegex(ValueError, "SETTLEMENT_SURVIVOR_ASOF_MARK_REQUIRED"):
            settle(w, "p1", EXPIRY, "46000", ".0001")
        wrong = mark_to_exit(w, "p2", later("48000",".09",".10",EXPIRY,"47000"),
                             later("43000",".04",".05",EXPIRY,"47000"),
                             EXPIRY, ".001", ".001")
        with self.assertRaisesRegex(ValueError, "SETTLEMENT_SURVIVOR_ASOF_MARK_REQUIRED"):
            settle(wrong, "p1", EXPIRY, "46000", ".0001")
        bad = mark_to_exit(w, "p2", later("48000",".09",".10",EXPIRY),
                           later("43000",".04",".05",EXPIRY), EXPIRY,
                           "110", "0")
        with self.assertRaisesRegex(ValueError, "POSTSETTLEMENT_SURVIVOR_MAINTENANCE_VETO"):
            settle(bad, "p1", EXPIRY, "46000", ".0001")
        good = mark_to_exit(w, "p2", later("48000",".09",".10",EXPIRY),
                            later("43000",".04",".05",EXPIRY), EXPIRY,
                            ".001", ".001")
        out = settle(good, "p1", EXPIRY, "46000", ".0001")
        self.assertEqual([p.name for p in out.positions], ["p2"])
        self.assertGreater(D(account_nav(out, EXPIRY)["nav_coin"]), D("2"))
        final = settle(out, "p2", expiry2, "46000", ".0001")
        self.assertEqual(final.settled, ("p1", "p2"))

    def test_independent_cross_expiry_settlement_oracle_falsification(self):
        trace, observed, _ = exercise()
        expiry2 = ms("2022-02-11T08:00:00+00:00")
        p2open = next(e for e in trace["events"]
                      if e["kind"] == "open" and e["name"] == "p2")
        p2open["expiry_ms"] = expiry2
        p2settle = next(e for e in trace["events"]
                        if e["kind"] == "settle" and e["name"] == "p2")
        p2settle["at_ms"] = expiry2
        fresh = dict(kind="mark", name="p2", at_ms=EXPIRY,
                     short_ask_coin=".10", long_bid_coin=".04",
                     exit_fees_coin=".001", exit_slippage_coin=".001",
                     index_usd="46000")
        with self.assertRaisesRegex(AssertionError, "REFERENCE_SETTLEMENT_SURVIVOR_ASOF_MARK_REQUIRED"):
            audit(trace, observed)
        trace["events"].insert(-2, fresh)
        self.assertEqual(audit(trace, observed)["independent_coin_account_replay"], "MATCH")
        fresh["index_usd"] = "47000"
        with self.assertRaisesRegex(AssertionError, "REFERENCE_SETTLEMENT_SURVIVOR_ASOF_MARK_REQUIRED"):
            audit(trace, observed)
        fresh["index_usd"] = "46000"
        fresh["exit_fees_coin"] = "110"
        with self.assertRaisesRegex(AssertionError, "REFERENCE_POSTSETTLEMENT_MAINTENANCE_BREACH"):
            audit(trace, observed)


if __name__ == "__main__":
    unittest.main()
