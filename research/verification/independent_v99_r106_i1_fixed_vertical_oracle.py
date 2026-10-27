"""Independent Decimal verification of fixture I1 fixed put-vertical selection.

Does not import the primary selector, wallet arithmetic, or cost functions.
A match is ONLY a synthetic accounting check, not original fill/ROI evidence.
"""
from datetime import datetime, timezone
from decimal import Decimal

DAY = 86_400_000
RATES = {"severe": Decimal("0.0012"),
         "supersevere": Decimal("0.0024")}


def audit_fixture(signal, quotes, decision, before, after):
    assert decision["fixture"] is True
    assert decision["economic_train_executed"] is False
    assert decision["promotion_authorized"] is False
    assert before.asset == after.asset == signal["asset"]
    assert before.scenario == after.scenario
    t = signal["decision_ms"]
    assert datetime.fromtimestamp(t/1000, timezone.utc).weekday() == 0
    assert signal["signal"] in ("POSITIVE_EX_ANTE_PREMIUM",
                                "NO_PREMIUM", "NO_30D_HISTORY")
    if decision["decision"].startswith("CASH_"):
        assert before == after
        return {"independent_fixture": "CASH_MATCH",
                "historical_economic_train": False, "promotion_authorized": False}
    assert decision["decision"] == "MODELED_FIXTURE_OPEN_ONLY"
    assert signal["signal"] == "POSITIVE_EX_ANTE_PREMIUM"
    candidates = []
    for a in quotes:
        for b in quotes:
            if a.symbol == b.symbol:
                continue
            spot = Decimal(str(a.index_usd))
            if not (a.asset == b.asset == signal["asset"]
                    and a.expiry_ms == b.expiry_ms
                    and Decimal(str(a.strike_usd)) > Decimal(str(b.strike_usd))
                    and Decimal(str(a.index_usd)) == Decimal(str(b.index_usd))
                    and 28*DAY <= a.expiry_ms-t <= 35*DAY
                    and abs(a.arrival_ms-b.arrival_ms) <= 1000
                    and abs(a.venue_ms-b.venue_ms) <= 1000
                    and a.bid_native_lots >= 1 and b.ask_native_lots >= 1
                    and Decimal(str(a.bid_coin)) > Decimal(str(b.ask_coin))
                    and abs(Decimal(str(a.strike_usd))/spot-Decimal("0.9"))
                        <= Decimal("0.02")
                    and abs(Decimal(str(b.strike_usd))/spot-Decimal("0.8"))
                        <= Decimal("0.02")):
                continue
            candidates.append((
                (abs(a.expiry_ms-t-30*DAY),
                 abs(Decimal(str(a.strike_usd))/spot-Decimal("0.9")),
                 abs(Decimal(str(b.strike_usd))/spot-Decimal("0.8")),
                 a.symbol, b.symbol), a, b))
    assert candidates, "NO_INDEPENDENT_ELIGIBLE_PAIR"
    _, short, long = min(candidates, key=lambda c: c[0])
    assert decision["short"] == short.symbol and decision["long"] == long.symbol
    fee = Decimal("2") * RATES[before.scenario]
    slip = Decimal("2") * RATES[before.scenario]
    assert Decimal(decision["modeled_fees_coin"]) == fee
    assert Decimal(decision["modeled_slippage_coin"]) == slip
    expected = (Decimal(str(before.cash_coin))
                + Decimal(str(short.bid_coin)) - Decimal(str(long.ask_coin))
                - fee - slip)
    assert Decimal(str(after.cash_coin)) == expected, "INDEPENDENT_CASH_MISMATCH"
    assert len(after.positions) == len(before.positions)+1
    assert after.positions[-1].short_symbol == short.symbol
    assert after.positions[-1].long_symbol == long.symbol
    assert after.positions[-1].qty == 1
    assert Decimal(str(after.reserved_coin)) == (
        Decimal(str(before.reserved_coin))
        + Decimal(str(after.positions[-1].initial_margin_coin)))
    return {"independent_fixture": "SELECTOR_AND_COIN_CASH_MATCH",
            "historical_economic_train": False, "promotion_authorized": False}
