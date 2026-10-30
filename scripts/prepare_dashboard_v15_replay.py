from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT / "config"
STATE = PROJECT / "state"
REPORTS = PROJECT / "reports"
CANONICAL = PROJECT / "data" / "canonical"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    candidate = load(CONFIG / "candidate_v15_adaptive_capture.json")
    universe = load(STATE / "paper_v15_universe.json")
    sync_path = REPORTS / "paper_data_sync_v15.json"
    sync = load(sync_path)

    ready: dict[str, str] = {}
    for symbol, item in universe.get("symbols", {}).items():
        price = CANONICAL / f"{symbol}_1h.csv"
        funding = CANONICAL / f"{symbol}_funding.csv"
        if price.exists() and price.stat().st_size > 0 and funding.exists():
            start_month = item.get("start_month")
            if start_month:
                ready[str(symbol)] = str(start_month)
    if not ready:
        raise RuntimeError("No published V15 symbols are available in the canonical cache")

    market_symbol = str(candidate["direction_allocator"]["market_symbol"])
    market_path = CANONICAL / f"{market_symbol}_1h.csv"
    if not market_path.exists():
        raise RuntimeError(f"V15 market symbol is absent from cache: {market_symbol}")
    timestamps = pd.read_csv(market_path, usecols=["timestamp"])
    if timestamps.empty:
        raise RuntimeError(f"V15 market cache is empty: {market_symbol}")
    cache_latest = pd.to_datetime(timestamps["timestamp"], utc=True, format="mixed").max()
    published_latest = pd.Timestamp(sync["expected_latest_closed_hour"])
    if published_latest.tzinfo is None:
        published_latest = published_latest.tz_localize("UTC")
    replay_latest = min(published_latest, cache_latest)

    runtime = {
        "cutoff_month": replay_latest.strftime("%Y-%m"),
        "interval": "1h",
        "market": "Binance USD-M perpetual futures",
        "source": "published V15 paper universe + canonical cache",
        "universe_rule": "published discovery state only; dashboard performs no rediscovery",
        "symbols": ready,
    }
    (CONFIG / "research_v15_runtime.json").write_text(
        json.dumps(runtime, indent=2) + "\n", encoding="utf-8"
    )

    sync["dashboard_published_expected_latest_closed_hour"] = published_latest.isoformat()
    sync["dashboard_replay_cache_latest_hour"] = cache_latest.isoformat()
    sync["expected_latest_closed_hour"] = replay_latest.isoformat()
    sync["dashboard_replay_clipped_to_cache"] = bool(replay_latest < published_latest)
    sync_path.write_text(json.dumps(sync, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ready_symbols": len(ready),
                "published_latest": published_latest.isoformat(),
                "cache_latest": cache_latest.isoformat(),
                "replay_latest": replay_latest.isoformat(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
