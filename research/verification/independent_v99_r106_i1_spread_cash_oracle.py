"""Independent Decimal accounting oracle for modeled I1 vertical-put plumbing.

Synthetic deterministic fixtures ONLY. NO original option tape, ROI, paper or orders.
"""
from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from research.tools.v99_r106_i1_defined_risk_options_ledger import (
    PutQuote, open_vertical, liquidation_nav, inverse_coin_expiry_diagnostic,
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
        # Independent hostile fixtures: reject contract metadata that
        # disagrees with native symbol and exchange-origin stale quotes.
        for bad in (
            replace(short, strike_usd=21000),
            replace(short, expiry_ms=expiry+86400000),
            replace(short, asset="ETH"),
            replace(short, symbol="BTC-1JUL22-19000-P"),
            replace(short, symbol="BTC-INVALID-20000-P"),
            replace(short, venue_ms=decision-600_000, arrival_ms=decision-1_000),
        ):
            try:
                open_vertical(bad, long, decision, 100000, scenario)
            except ValueError:
                checks += 1
            else:
                raise AssertionError("UNBOUND_NATIVE_OPTION_ID_OR_STALE_VENUE_ACCEPTED")
        for bad, other, is_short in (
            (replace(ms, symbol="BTC-1JUL22-19000-P"), ml, True),
            (replace(ml, symbol="BTC-1JUL22-20000-P"), ms, False),
            (replace(ms, venue_ms=mark-600_000, arrival_ms=mark-1_000), ml, True),
        ):
            try:
                liquidation_nav(p, bad, other, mark) if is_short else liquidation_nav(p, other, bad, mark)
            except ValueError:
                checks += 1
            else:
                raise AssertionError("EXIT_OPTION_ID_OR_STALE_VENUE_ACCEPTED")
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

    # Reconstruct inverse coin settlement independently of the USD cash model.
    # The previous modeled USD collateral is NOT a native margin guarantee.
    for delivery in (22000, 18000, 500):
        diag = inverse_coin_expiry_diagnostic(p, delivery)
        intrinsic = qty*(max(d(20000)-d(delivery), d(0))
                         -max(d(19000)-d(delivery), d(0)))
        expected_coin = (d(100000)+expected_credit)/d(20000)-intrinsic/d(delivery)
        assert abs(d(diag["intrinsic_obligation_coin"])-intrinsic/d(delivery)) < d("1e-9")
        assert abs(d(diag["remaining_coin_without_liquidation"])-expected_coin) < d("1e-9")
        assert abs(d(diag["coin_account_usd_without_liquidation"])-expected_coin*d(delivery)) < d("1e-7")
        assert diag["hypothetical_coin_insolvency"] == (expected_coin < 0)
        assert diag["modeled_only"] and not diag["promotion_authorized"]
        if delivery == 500:
            assert diag["hypothetical_coin_insolvency"]
            assert diag["prior_usd_equivalent_model_nav"] > 0
        checks += 6
    for invalid in (0, -1, float("nan")):
        try:
            inverse_coin_expiry_diagnostic(p, invalid)
        except ValueError:
            checks += 1
        else:
            raise AssertionError("BAD_DELIVERY_INDEX_ACCEPTED")
    print({"status":"INDEPENDENT_DECIMAL_MODELED_SPREAD_LEDGER_INVARIANTS_PASS",
           "checks":checks, "original_historical_options_used":False,
           "economic_train_run":False, "native_fee_authenticated":False,
           "native_margin_authenticated":False, "orders":False,
           "promotion":False})



def run_inverse_coin_quote_replay_oracle():
    """Separate Decimal reconstruction from original opening quotes; fixtures only."""
    from research.tools.v99_r106_i1_defined_risk_options_ledger import (
        replay_inverse_coin_expiry_from_quotes,
    )
    from dataclasses import replace
    from datetime import datetime, timezone
    t = int(datetime(2022, 6, 1, tzinfo=timezone.utc).timestamp() * 1000)
    e = int(datetime(2022, 7, 1, 8, tzinfo=timezone.utc).timestamp() * 1000)
    fields = dict(asset="BTC", expiry_ms=e, bid_qty=6.0, ask_qty=6.0,
                  venue_ms=t-60000, arrival_ms=t-30000, spot_usd=20000.0)
    short = PutQuote(symbol="BTC-1JUL22-20000-P", strike_usd=20000.0,
                     bid_coin=0.055, ask_coin=0.060, **fields)
    long = PutQuote(symbol="BTC-1JUL22-19000-P", strike_usd=19000.0,
                    bid_coin=0.025, ask_coin=0.030, **fields)
    cases = 0
    for scenario, per_leg in (("severe", Decimal("0.0024")),
                               ("supersevere", Decimal("0.0048"))):
        position = open_vertical(short, long, t, 100000.0, scenario)
        contracts = min(Decimal("6"), Decimal("100000")*Decimal("0.05")/Decimal("1000"))
        premium_coin = contracts*(Decimal("0.055")-Decimal("0.030"))
        friction_coin = Decimal("2")*contracts*per_leg
        for delivery in (22000, 18000, 500):
            for fee in (None, 0.001):
                actual = replay_inverse_coin_expiry_from_quotes(
                    position, short, long, float(delivery), fee)
                due_usd = contracts*(
                    max(Decimal("20000")-Decimal(delivery), Decimal(0))
                    -max(Decimal("19000")-Decimal(delivery), Decimal(0))
                )
                due_coin = due_usd/Decimal(delivery)
                final_coin = (Decimal("100000")/Decimal("20000")
                              +premium_coin-friction_coin-due_coin
                              -(Decimal("0.001") if fee is not None else Decimal(0)))
                assert abs(Decimal(str(actual["net_opening_credit_coin"]))
                           -(premium_coin-friction_coin)) < Decimal("1e-12")
                assert abs(Decimal(str(actual["intrinsic_settlement_coin"]))
                           -due_coin) < Decimal("1e-12")
                assert abs(Decimal(str(actual["coin_balance_without_margin_liquidation"]))
                           -final_coin) < Decimal("1e-12")
                assert abs(Decimal(str(actual["usd_equivalent_at_delivery_without_margin_liquidation"]))
                           -final_coin*Decimal(delivery)) < Decimal("1e-8")
                assert actual["hypothetical_insolvency"] == (final_coin < 0)
                assert actual["delivery_fee_missing"] == (fee is None)
                assert not actual["native_margin_certified"]
                assert not actual["promotion_authorized"] and not actual["orders_enabled"]
                cases += 1
        # The same instrument but a different premium MUST NOT replay as the open.
        hostile = (
            (replace(short, bid_coin=0.056), long, 18000, None),
            (replace(short, venue_ms=t-600000), long, 18000, None),
            (replace(short, bid_qty=0.01), long, 18000, None),
            (short, replace(long, symbol="BTC-1JUL22-18000-P"), 18000, None),
            (short, long, 0, None),
            (short, long, 18000, -0.001),
        )
        for a, b, spot, fee in hostile:
            try:
                replay_inverse_coin_expiry_from_quotes(position, a, b, spot, fee)
            except ValueError:
                cases += 1
            else:
                raise AssertionError("INVALID_COIN_LEDGER_INPUT_ACCEPTED")
    print({"status": "INDEPENDENT_INVERSE_COIN_QUOTE_REPLAY_PASS",
           "scenarios": 2, "delivery_states": 3, "fee_states": 2,
           "cases_including_adversarial": cases, "synthetic_fixtures_only": True,
           "historical_economic_train_run": False, "promotion": False, "orders": False})

if __name__=="__main__":
    run()
    run_inverse_coin_quote_replay_oracle()
