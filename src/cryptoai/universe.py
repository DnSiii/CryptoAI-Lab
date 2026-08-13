from __future__ import annotations

import pandas as pd

from .binance_data import discover_archives


def _metadata(chosen) -> list[dict[str, object]]:
    return [
        {
            "symbol": a.symbol,
            "first_month": a.first_month,
            "last_month": a.last_month,
            "monthly_files": a.monthly_files,
            "delisted": a.delisted,
        }
        for a in chosen
    ]


def _force_core(chosen, eligible):
    by_symbol = {a.symbol: a for a in eligible}
    out = list(chosen)
    for required in ("BTCUSDT", "ETHUSDT"):
        if required in by_symbol and required not in {x.symbol for x in out}:
            if out:
                out[-1] = by_symbol[required]
            else:
                out.append(by_symbol[required])
    return sorted({x.symbol: x for x in out}.values(), key=lambda x: x.symbol)


def select_adversarial_universe(max_symbols: int) -> tuple[list[str], list[dict[str, object]]]:
    """Select an old-contract stress universe with deliberate delisted inclusion.

    This is not a production liquidity universe. It is intentionally adversarial and
    exists to expose survivorship-sensitive ideas early.
    """
    archives = discover_archives()
    eligible = [a for a in archives if a.first_month and a.first_month <= "2024-01" and a.monthly_files >= 12]
    delisted = [a for a in eligible if a.delisted]
    live = [a for a in eligible if not a.delisted]
    n_delisted = min(max(4, max_symbols // 4), len(delisted))
    chosen = _force_core(delisted[:n_delisted] + live[: max_symbols - n_delisted], eligible)
    meta = _metadata(chosen)
    return [a.symbol for a in chosen], meta


def select_discovery_universe(max_symbols: int, *, existed_by: str = "2021-01") -> tuple[list[str], list[dict[str, object]]]:
    """Select contracts using only first-listing information available by a historical cutoff.

    The selector deliberately does not filter on current listing status, last archive month,
    or future realized liquidity. Delisted contracts can therefore remain in the sample
    naturally without using their future failure as a selection input.
    """
    archives = discover_archives()
    eligible = [a for a in archives if a.first_month and a.first_month <= existed_by]
    eligible = sorted(eligible, key=lambda a: (a.first_month or "9999-99", a.symbol))
    chosen = _force_core(eligible[:max_symbols], eligible)
    meta = _metadata(chosen)
    return [a.symbol for a in chosen], meta


def complete_funding_archive_end(requested_end: str, universe_meta: list[dict[str, object]]) -> str:
    """Clip replay to the latest complete BTC/ETH monthly funding archive."""
    core_last = {
        str(row["symbol"]): str(row["last_month"])
        for row in universe_meta
        if row.get("symbol") in {"BTCUSDT", "ETHUSDT"} and row.get("last_month")
    }
    if set(core_last) != {"BTCUSDT", "ETHUSDT"}:
        raise RuntimeError(f"Could not determine complete funding archive cutoff for BTC/ETH: {core_last}")
    latest_common_month = min(core_last.values())
    archive_end = pd.Period(latest_common_month, freq="M").end_time.normalize()
    requested = pd.Timestamp(requested_end)
    return str(min(requested, archive_end).date())
