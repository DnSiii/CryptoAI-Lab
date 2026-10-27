"""Independent Decimal fixture decision oracle; not historical performance proof.

Crucially, an unchanged wallet alone DOES NOT prove a valid CASH decision.
No imports of the primary selector, cost adapter, or wallet arithmetic.
Prereg: research/V99_R106_I1_INDEPENDENT_CASH_DECISION_ORACLE_PREREG_20261026.md
"""
from datetime import datetime, timezone
from decimal import Decimal

DAY = 86_400_000
RATES = {"severe": Decimal("0.0012"),
         "supersevere": Decimal("0.0024")}
START = 1639008000000
END = 1696118400000


def _d(value):
    v = Decimal(str(value))
    assert v.is_finite(), "REFERENCE_NONFINITE_VALUE"
    return v


def _pairs(signal, quotes):
    """Rebuild source validity and fixed pair ranking without primary imports."""
    t = signal["decision_ms"]
    assert type(t) is int and START < t < END
    dt = datetime.fromtimestamp(t / 1000, timezone.utc)
    assert (dt.weekday(), dt.hour, dt.minute, dt.second, dt.microsecond) == (0, 0, 0, 0, 0)
    assert signal["asset"] in ("BTC", "ETH")
    assert signal["fold"] in (1, 2, 3, 4, 5)
    assert t + 21 * DAY < END
    seen = set()
    for q in quotes:
        assert q.asset == signal["asset"] and q.symbol not in seen, "REFERENCE_BAD_QUOTE_ID"
        seen.add(q.symbol)
        parts = q.symbol.split("-")
        assert len(parts) == 4 and parts[0] == q.asset and parts[3] == "P", "REFERENCE_BAD_CONTRACT"
        expiry = datetime.strptime(parts[1].upper(), "%d%b%y").replace(hour=8, tzinfo=timezone.utc)
        assert int(expiry.timestamp() * 1000) == q.expiry_ms
        assert _d(parts[2]) == _d(q.strike_usd) and _d(q.strike_usd) > 0
        assert (START <= q.venue_ms <= q.arrival_ms < t < END
                and q.expiry_ms < END and t < q.expiry_ms
                and t - q.venue_ms <= 300_000
                and t - q.arrival_ms <= 300_000), "REFERENCE_STALE_OR_FUTURE"
        assert (_d(q.index_usd) > 0
                and 0 < _d(q.bid_coin) < _d(q.ask_coin)
                and _d(q.bid_native_lots) > 0 and _d(q.ask_native_lots) > 0), "REFERENCE_BAD_BOOK"
    out = []
    for short in quotes:
        spot = _d(short.index_usd)
        if not (28 * DAY <= short.expiry_ms-t <= 35 * DAY
                and abs(_d(short.strike_usd)/spot-Decimal("0.90")) <= Decimal("0.02")):
            continue
        for long in quotes:
            if (short.symbol == long.symbol
                    or short.expiry_ms != long.expiry_ms
                    or _d(short.strike_usd) <= _d(long.strike_usd)
                    or _d(short.index_usd) != _d(long.index_usd)
                    or abs(_d(long.strike_usd)/spot-Decimal("0.80")) > Decimal("0.02")
                    or abs(short.arrival_ms-long.arrival_ms) > 1000
                    or abs(short.venue_ms-long.venue_ms) > 1000
                    or _d(short.bid_native_lots) < 1
                    or _d(long.ask_native_lots) < 1
                    or _d(short.bid_coin) <= _d(long.ask_coin)):
                continue
            key = (abs(short.expiry_ms-t-30*DAY),
                   abs(_d(short.strike_usd)/spot-Decimal("0.90")),
                   abs(_d(long.strike_usd)/spot-Decimal("0.80")),
                   short.symbol, long.symbol)
            out.append((key, short, long))
    return sorted(out, key=lambda x: x[0])


def _independent_risk_reason(before, short, long, reason, initial, maintenance):
    """Only certify simple empty-wallet risk vetoes, never guess overlap NAV."""
    assert not before.positions and not before.marks, "UNVERIFIED_OVERLAPPING_RISK_ORACLE"
    fee = 2 * RATES[before.scenario]
    friction = 2 * fee
    initial, maintenance = _d(initial), _d(maintenance)
    if initial < maintenance or maintenance <= 0:
        expected = "UNVERIFIED_OR_INVALID_NATIVE_MARGIN_COST"
    else:
        net = _d(short.bid_coin) - _d(long.ask_coin) - friction
        cash = _d(before.cash_coin) + net
        if net <= 0:
            expected = "NEGATIVE_NET_PREMIUM"
        elif cash < initial:
            expected = "REUSED_OR_INSUFFICIENT_COIN_COLLATERAL"
        else:
            immediate = max(Decimal(0), _d(short.ask_coin) - _d(long.bid_coin))
            if cash - immediate < maintenance:
                expected = "POSTENTRY_MAINTENANCE_LOWER_BOUND_BREACH"
            elif cash - immediate - friction < maintenance:
                expected = "POSTENTRY_SCENARIO_COST_MAINTENANCE_VETO"
            else:
                expected = None
    assert expected is not None and reason == expected, "REFERENCE_UNJUSTIFIED_RISK_CASH"
    return "INDEPENDENT_RISK_CASH_VETO_MATCH"


def audit_fixture(signal, quotes, decision, before, after, *,
                  initial_margin_coin=None, maintenance_margin_coin=None):
    assert decision["fixture"] is True
    assert decision["economic_train_executed"] is False
    assert decision["promotion_authorized"] is False
    assert before.asset == after.asset == signal["asset"]
    assert before.scenario == after.scenario
    assert before.scenario in RATES
    assert signal["signal"] in ("POSITIVE_EX_ANTE_PREMIUM",
                                "NO_PREMIUM", "NO_30D_HISTORY")
    candidates = _pairs(signal, quotes)
    selected = candidates[0][1:] if candidates else None
    label = decision["decision"]
    if label == "CASH_NO_ELIGIBLE_SOURCE_OR_SIGNAL":
        assert before == after
        assert signal["signal"] != "POSITIVE_EX_ANTE_PREMIUM" or not selected, "REFERENCE_FORGED_CASH_WITH_VALID_PAIR"
        return {"independent_fixture": "CASH_MATCH",
                "historical_economic_train": False, "promotion_authorized": False}
    if label == "CASH_RISK_VETO":
        assert before == after
        assert signal["signal"] == "POSITIVE_EX_ANTE_PREMIUM" and selected, "REFERENCE_FORGED_RISK_CASH"
        assert initial_margin_coin is not None and maintenance_margin_coin is not None, "RISK_TERMS_REQUIRED_FOR_INDEPENDENT_ORACLE"
        verdict = _independent_risk_reason(
            before, *selected, decision.get("reason"),
            initial_margin_coin, maintenance_margin_coin)
        return {"independent_fixture": verdict,
                "historical_economic_train": False, "promotion_authorized": False}
    assert label == "MODELED_FIXTURE_OPEN_ONLY"
    assert signal["signal"] == "POSITIVE_EX_ANTE_PREMIUM" and selected
    assert not before.positions and not before.marks, "UNVERIFIED_OVERLAPPING_OPEN_ORACLE"
    short, long = selected
    assert decision["short"] == short.symbol and decision["long"] == long.symbol
    fee = Decimal("2") * RATES[before.scenario]
    slip = Decimal("2") * RATES[before.scenario]
    assert _d(decision["modeled_fees_coin"]) == fee
    assert _d(decision["modeled_slippage_coin"]) == slip
    expected = (_d(before.cash_coin)
                + _d(short.bid_coin) - _d(long.ask_coin) - fee - slip)
    assert _d(after.cash_coin) == expected, "INDEPENDENT_CASH_MISMATCH"
    assert len(after.positions) == len(before.positions) + 1
    assert after.positions[-1].short_symbol == short.symbol
    assert after.positions[-1].long_symbol == long.symbol
    assert after.positions[-1].qty == 1
    assert _d(after.reserved_coin) == (
        _d(before.reserved_coin) + _d(after.positions[-1].initial_margin_coin))
    if initial_margin_coin is not None:
        assert _d(after.positions[-1].initial_margin_coin) == _d(initial_margin_coin)
    if maintenance_margin_coin is not None:
        assert _d(after.positions[-1].maintenance_margin_coin) == _d(maintenance_margin_coin)
    return {"independent_fixture": "SELECTOR_AND_COIN_CASH_MATCH",
            "historical_economic_train": False, "promotion_authorized": False}
