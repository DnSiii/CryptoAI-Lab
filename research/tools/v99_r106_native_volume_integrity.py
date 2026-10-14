"""Independent native contract-volume audit of immutable OKX receipts; DATA_ONLY.

Checks units in original raw candles against observed OKX ctVal, without
reusing Binance economics or converting projected funding into cashflow.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from research.tools import v99_r106_asof_pair_gate as pair
from research.tools import v99_r106_receipt_append as source


def decimal(value):
    if isinstance(value, bool) or value is None:
        raise ValueError("invalid native decimal")
    try:
        x = Decimal(str(value))
    except (TypeError, InvalidOperation) as exc:
        raise ValueError("invalid native decimal") from exc
    if not x.is_finite():
        raise ValueError("nonfinite native decimal")
    return x


def audit_rows(rows, multiplier, observed_utc, last_closed_utc):
    ct = decimal(multiplier)
    if ct <= 0 or not isinstance(rows, list) or not 4 <= len(rows) <= 6:
        raise ValueError("invalid native contract or source length")
    observed = source.utc(observed_utc)
    closed = source.utc(last_closed_utc)
    stamps = []
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) < 9 or row[8] != ("0" if index == 0 else "1"):
            raise ValueError("confirmed candle ordering violated")
        stamp = int(row[0])
        if stamp % 3600000:
            raise ValueError("unaligned native candle")
        ts = datetime.fromtimestamp(stamp / 1000, timezone.utc)
        if ts > observed or (index > 0 and ts + timedelta(hours=1) > observed):
            raise ValueError("unavailable future candle")
        stamps.append(ts)
        op, hi, lo, cl, contracts, base, quote = (decimal(row[i]) for i in (1, 2, 3, 4, 5, 6, 7))
        if lo <= 0 or not lo <= min(op, cl) <= max(op, cl) <= hi or min(contracts, base, quote) < 0:
            raise ValueError("invalid native OHLCV")
        if abs(contracts * ct - base) > max(Decimal("0.0000001"), base * Decimal("0.0000001")):
            raise ValueError("native contract-to-base volume mismatch")
        if base > 0 and not base * lo * Decimal("0.999999") <= quote <= base * hi * Decimal("1.000001"):
            raise ValueError("quote turnover outside OHLCV range")
    if any(a - b != timedelta(hours=1) for a, b in zip(stamps, stamps[1:])):
        raise ValueError("missing or reordered native candle")
    if stamps[1] + timedelta(hours=1) != closed:
        raise ValueError("manifest confirmed-close mismatch")
    return len(rows) - 1


def audit(market_dir: Path, terms_dir: Path):
    verified = pair.audit(market_dir, terms_dir)
    market = source.strict((market_dir / "manifest.json").read_bytes())
    total = 0
    details = {}
    for inst, entry in sorted(market["instruments"].items()):
        original = source.strict((market_dir / (inst + ".raw.json")).read_bytes())
        if original.get("code") != "0":
            raise ValueError("native source error")
        ct = verified["assets"][inst]["contract_native_value"]
        n = audit_rows(original.get("data"), ct, entry["received_utc"], entry["latest_confirmed_close_utc"])
        if n != entry["confirmed_candles"] or len(original["data"]) - n != entry["unconfirmed_candles"]:
            raise ValueError("manifest confirmed-candle counts mismatch")
        total += n
        details[inst] = {"confirmed_bars": n, "ctVal": ct}
    return {"status": "OKX_NATIVE_VOLUME_AND_PIT_PASS_DATA_ONLY", "confirmed_rows": total,
            "instruments": details, "earliest_safe_decision_utc": verified["earliest_safe_decision_utc"],
            "native_fee_tiers_attested": False, "funding_settlements_attested": False,
            "paper_publication_authorized": False, "promotion_authorized": False,
            "economic_trials": 0}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--market", type=Path, required=True)
    p.add_argument("--terms", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = audit(a.market, a.terms)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "confirmed_rows": result["confirmed_rows"],
                      "promotion_authorized": False}, sort_keys=True))


if __name__ == "__main__":
    main()
