"""Independent Decimal accounting oracle for modeled I1 vertical-put plumbing.

Synthetic deterministic fixtures ONLY. NO original option tape, ROI, paper or orders.
"""
from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from research.tools.v99_r106_i1_defined_risk_options_ledger import (
    PutQuote, open_vertical, liquidation_nav,
)


def d(x):
    return Decimal(str(x))


def run():
    decision = int(datetime(2022, 6, 1, tzinfo=timezone.utc).timestamp()*1000)
    expiry = int(datetime(2022, 7, 1, 8, tzinfo=timezone.utc).timestamp()*1000)
    base = dict(asset="BTC", expiry_ms=expiry, bid_qty=6, ask_qty=6,
                venue_ms=decision-60_000, arrival_ms=decision-30_000,
                spot_usd=20_000.0)
    short = PutQuote(symbol="BTC-1JUL22-20000-P", strike_usd=20000,
                     bid_coin=0.055, ask_coin=0.060, **base)
    long = PutQuote(symbol="BTC-1JUL22-19000-P", strike_usd=19000,
                    bid_coin=0.025, ask_coin=0.030, **base)
    checks = 0
    for scenario, friction in (("severe", d("0.0024")), ("supersevere", d("0.0048"))):
        p = open_vertical(short, long, decision, 100000, scenario)
        qty = min(d(6), d(100000)*d("0.05")/d(1000))
        entry_cost = d(2)*qty*d(20000)*friction
        expected_credit = qty*(d("0.055")-d("0.030"))*d(20000)-entry_cost
        expected_cash = d(100000)+expected_credit
        assert d(p.qty)==qty
        assert abs(d(p.entry_cost_usd)-entry_cost)<d("1e-7")
        assert abs(d(p.premium_credit_usd)-expected_credit)<d("1e-7")
        assert abs(d(p.cash_after_open_usd)-expected_cash)<d("1e-7")
        assert abs(d(p.collateral_reserved_usd)-qty*d(1000))<d("1e-7")
        checks += 5
        for spot in (22000, 19500, 18000):
            result = p.expiry_nav(spot)
            payoff = qty*(max(d(20000)-d(spot), d(0))
                          -max(d(19000)-d(spot), d(0)))
            assert abs(d(result["settlement_payoff_usd"])-payoff)<d("1e-7")
            assert abs(d(result["nav_usd"])-(expected_cash-payoff))<d("1e-7")
            assert payoff<=qty*d(1000)
            checks += 3
        mark = decision+24*3600*1000
        ms = replace(short, venue_ms=mark-60_000, arrival_ms=mark-30_000,
                     spot_usd=19000, bid_coin=.08, ask_coin=.09)
        ml = replace(long, venue_ms=mark-60_000, arrival_ms=mark-30_000,
                     spot_usd=19000, bid_coin=.045, ask_coin=.055)
        v = liquidation_nav(p, ms, ml, mark)
        debit = qty*(d(".09")-d(".045"))*d(19000)
        cost = d(2)*qty*d(19000)*friction
        assert abs(d(v["nav_usd"])-(expected_cash-debit-cost))<d("1e-7")
        assert not v["orders_enabled"] and v["modeled_only"]
        checks += 2
        for bad in (
            replace(short, arrival_ms=decision+1),
            replace(short, venue_ms=decision+1),
            replace(short, ask_coin=short.bid_coin),
        ):
            try:
                open_vertical(bad, long, decision, 100000, scenario)
            except ValueError:
                checks += 1
            else:
                raise AssertionError("CAUSAL_OR_CROSSED_QUOTE_ACCEPTED")
        try:
            open_vertical(replace(short, bid_coin=0.001), long, decision, 100000, scenario)
        except ValueError as exc:
            assert "NEGATIVE_AFTER_COST_CREDIT" in str(exc)
            checks += 1
        else:
            raise AssertionError("NEGATIVE_CREDIT_ACCEPTED")
        try:
            liquidation_nav(p, replace(ms, ask_qty=0.01), ml, mark)
        except ValueError:
            checks += 1
        else:
            raise AssertionError("NO_DEPTH_MARK_ACCEPTED")
    print({"status":"INDEPENDENT_DECIMAL_MODELED_SPREAD_LEDGER_INVARIANTS_PASS",
           "checks":checks, "original_historical_options_used":False,
           "economic_train_run":False, "native_fee_authenticated":False,
           "native_margin_authenticated":False, "orders":False,
           "promotion":False})


if __name__=="__main__":
    run()
