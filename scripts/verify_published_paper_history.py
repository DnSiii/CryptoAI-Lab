"""Fail closed if a replay changes previously published official evidence."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def verify(old: dict, new: dict) -> None:
    for field in ("mode", "candidate", "base_capital_brl", "paper_start_after_timestamp", "opening_snapshot"):
        if old.get(field) != new.get(field):
            raise RuntimeError(f"Published paper boundary changed: {field}")
    for field in ("equity_curve", "decisions"):
        previous = old.get(field, [])
        if new.get(field, [])[:len(previous)] != previous:
            raise RuntimeError(f"Published {field} was rewritten; recovery publication blocked")
    if new["latest_data_timestamp"] < old["latest_data_timestamp"]:
        raise RuntimeError("Published paper timestamp regressed")


def main() -> None:
    baseline = PROJECT / "reports" / "published_baseline"
    for path in sorted(baseline.glob("*_ledger.json")):
        verify(json.loads(path.read_text()), json.loads((PROJECT / "reports" / path.name).read_text()))
        print(f"Published history preserved: {path.name}")
    if not list(baseline.glob("*_ledger.json")):
        raise RuntimeError("Published paper baseline missing")


if __name__ == "__main__":
    main()
