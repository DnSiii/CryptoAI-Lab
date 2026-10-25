"""Independent Decimal replay of overlapping cash/reserve transitions; fixtures only."""
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from research.tools.v99_r106_i1_defined_risk_options_ledger import PutQuote, open_vertical
from research.tools.v99_r106_i1_overlapping_cash_portfolio import (
    start_portfolio, open_position, settle_position, source_only_status,
)


def d(x):
    return Decimal(str(x))


def quote_pair(asset, t, e, high, low, spot):
    base = dict(asset=asset, expiry_ms=e, bid_qty=6., ask_qty=6.,
                venue_ms=t-60_000, arrival_ms=t-30_000, spot_usd=spot)
    suffix = datetime.fromtimestamp(e/1000, tz=timezone.utc).strftime("%-d%b%y").upper()
    short = PutQuote(symbol=f"{asset}-{suffix}-{high}-P",
                     strike_usd=high, bid_coin=.055, ask_coin=.060, **base)
    long = PutQuote(symbol=f"{asset}-{suffix}-{low}-P",
                    strike_usd=low, bid_coin=.025, ask_coin=.030, **base)
    return short, long


def must_reject(call, reason):
    try:
        call()
    except ValueError:
        return 1
    raise AssertionError(reason)


def run():
    t1 = int(datetime(2022, 6, 6, tzinfo=timezone.utc).timestamp()*1000)
    t2 = int(datetime(2022, 6, 13, tzinfo=timezone.utc).timestamp()*1000)
    e1 = int(datetime(2022, 7, 8, 8, tzinfo=timezone.utc).timestamp()*1000)
    e2 = int(datetime(2022, 7, 15, 8, tzinfo=timezone.utc).timestamp()*1000)
    btc = quote_pair("BTC", t1, e1, 20000, 19000, 20000)
    eth = quote_pair("ETH", t2, e2, 2000, 1900, 2000)
    checks = 0
    for scenario, cost_per_leg in (("severe", d(".0024")), ("supersevere", d(".0048"))):
        p0 = start_portfolio(100000., scenario)
        a = open_vertical(*btc, t1, p0.cash_usd, scenario)
        p1 = open_position(p0, "BTC-A", a, *btc)
        free = p1.cash_usd-p1.reserved_usd
        b = open_vertical(*eth, t2, free, scenario)
        p2 = open_position(p1, "ETH-B", b, *eth)
        qty_a = min(d(6), d(100000)*d(".05")/d(1000))
        credit_a = qty_a*d(20000)*(d(".055")-d(".030")-2*cost_per_leg)
        qty_b = min(d(6), (d(100000)+credit_a-qty_a*d(1000))*d(".05")/d(100))
        credit_b = qty_b*d(2000)*(d(".055")-d(".030")-2*cost_per_leg)
        reserve = qty_a*d(1000)+qty_b*d(100)
        expected_cash = d(100000)+credit_a+credit_b
        assert abs(d(p2.cash_usd)-expected_cash) < d("1e-7")
        assert abs(d(p2.reserved_usd)-reserve) < d("1e-7")
        assert p2.reserved_usd <= p2.initial_usd*.20
        checks += 3
        p3 = settle_position(p2, "BTC-A", e1, 18000.)
        assert abs(d(p3.cash_usd)-(expected_cash-qty_a*d(1000))) < d("1e-7")
        assert abs(d(p3.reserved_usd)-qty_b*d(100)) < d("1e-7")
        p4 = settle_position(p3, "ETH-B", e2, 1800.)
        final = expected_cash-qty_a*d(1000)-qty_b*d(100)
        assert abs(d(p4.cash_usd)-final) < d("1e-7")
        assert abs(d(p4.reserved_usd)) < d("1e-7")
        assert p4.settled_ids == ("BTC-A", "ETH-B")
        status = source_only_status(p4)
        assert not any(status[k] for k in (
            "unrealized_option_liability_known", "native_coin_margin_authenticated",
            "historical_fee_or_fill_authenticated", "economic_train_executed",
            "validation_opened", "holdout_opened", "promotion_authorized",
            "orders_enabled"))
        checks += 6
        checks += must_reject(lambda: open_position(p2, "BTC-A", a, *btc), "DUPLICATE_ID")
        # Balanced but invented cash and premium cannot enter a portfolio.
        inflated = replace(b, premium_credit_usd=b.premium_credit_usd+100,
                           cash_after_open_usd=b.cash_after_open_usd+100)
        checks += must_reject(lambda: open_position(p1, "ETH-FORGED", inflated, *eth),
                              "FORGED_BALANCED_PREMIUM_AND_CASH")
        checks += must_reject(lambda: open_position(p1, "ETH-QUOTE", b,
                              replace(eth[0], bid_coin=eth[0].bid_coin+0.001), eth[1]),
                              "ORIGINAL_MODEL_QUOTE_PREMIUM_MISMATCH")
        checks += must_reject(lambda: open_position(p1, "ETH-B", replace(b, initial_cash_usd=p1.cash_usd,
                                  cash_after_open_usd=p1.cash_usd+b.premium_credit_usd), *eth),
                                  "COLLATERAL_REUSE")
        checks += must_reject(lambda: settle_position(p2, "BTC-A", e1-1, 18000.), "EARLY_SETTLEMENT")
        checks += must_reject(lambda: settle_position(p3, "BTC-A", e1, 18000.), "DOUBLE_SETTLEMENT")
        checks += must_reject(lambda: settle_position(p2, "ETH-B", e2, 1800.), "OUT_OF_ORDER_SETTLEMENT")
        checks += must_reject(lambda: settle_position(p2, "BTC-A", e1, 0), "INVALID_DELIVERY")
        checks += must_reject(lambda: open_position(replace(p1, reserved_usd=0), "ETH-B", b, *eth), "FORGED_RESERVE")
        checks += must_reject(lambda: open_position(replace(p1, cash_usd=0), "ETH-B", b, *eth), "FORGED_CASH")
        checks += must_reject(lambda: open_position(p1, "ETH-B", replace(b, scenario="supersevere" if scenario=="severe" else "severe"), *eth),
                              "WRONG_SCENARIO")
        checks += must_reject(lambda: open_position(p1, "ETH-B", replace(b, decision_ms=t1-7*86_400_000), *eth),
                              "INVALID_DECISION")
        # Reserve consistency alone does not catch a fabricated positive cash
        # balance after settlement. The journal must replay every credit/debit.
        checks += must_reject(lambda: replace(p4, cash_usd=p4.cash_usd+1000).verify(),
                              "FORGED_FINAL_CASH_WITH_CORRECT_RESERVE")
        checks += must_reject(lambda: replace(p1, cash_usd=p1.cash_usd+1000).verify(),
                              "FORGED_OPEN_CASH_WITH_CORRECT_RESERVE")
        checks += must_reject(lambda: replace(p4, events=p4.events[:-1]).verify(),
                              "MISSING_FINAL_SETTLEMENT_RECEIPT")
        checks += must_reject(lambda: replace(p4, events=p4.events[:-1]+(
                              replace(p4.events[-1], delivery_index_usd=1950.),)).verify(),
                              "MUTATED_SETTLEMENT_PRICE")
        checks += must_reject(lambda: replace(p2, events=tuple(reversed(p2.events))).verify(),
                              "REVERSED_EVENT_SEQUENCE")
        checks += must_reject(lambda: replace(p2, events=p2.events+(p2.events[0],)).verify(),
                              "DUPLICATE_OPEN_EVENT")
        checks += must_reject(lambda: replace(p3, reserved_usd=p3.reserved_usd+10).verify(),
                              "FORGED_POST_SETTLEMENT_RESERVE")
    print({"status": "INDEPENDENT_DECIMAL_SHARED_CASH_RESERVE_ORACLE_PASS",
           "checks": checks, "scenario_count": 2,
           "original_historical_options_used": False, "economic_train": False,
           "native_margin": False, "promotion": False, "orders": False})


if __name__ == "__main__":
    run()
