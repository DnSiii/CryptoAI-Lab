"""Authenticated V98 B0 next-open economic replay. Research only; no holdout."""
import argparse
import json
import math
from pathlib import Path
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import HOUR_MS, ASSETS
from .v98_b0_authenticated_replay_bridge import preregistered_sleeves
from .v98_b0_next_open_execution import replay_next_open

def run(prices, manifest, funding):
    data = load(prices, manifest, funding)
    # Funding is timestamp-keyed in the authenticated source, index-keyed in
    # the executor. Never replace missing settlements with fabricated rates.
    indexed = {a: {} for a in ASSETS}
    for a in ASSETS:
        for stamp, rate in data["funding"][a].items():
            offset = stamp - START_MS
            if offset % HOUR_MS or not (0 <= offset < data["hours"] * HOUR_MS):
                raise ValueError("INVALID_FUNDING_TIMESTAMP")
            indexed[a][offset // HOUR_MS] = rate
    results = {}
    ledgers = {}
    for scale in (1., 2., 4.):
        summary, entries = replay_next_open(
            data["bars"], indexed, preregistered_sleeves(), cost_scale=scale)
        if summary["hours"] != data["hours"] or len(entries) != data["hours"] - 1:
            raise ValueError("INCOMPLETE_NEXT_OPEN_REPLAY")
        if not all(math.isfinite(float(v)) for v in
                   (summary["final_equity"], summary["max_drawdown"],
                    summary["total_turnover"], summary["funding_return_sum"])):
            raise ValueError("NONFINITE_ECONOMIC_RESULT")
        scenario = str(int(scale)) + "x"
        results[scenario] = summary
        ledgers[scenario] = entries
    return {"status": "EXPLORATORY_NEXT_OPEN_NOT_INDEPENDENTLY_VALIDATED",
            "holdout_accessed": False, "source": "AUTHENTICATED_CLEAN4",
            "price_manifest_sha256": data["price_manifest_sha256"],
            "funding_manifest_sha256": data["funding_manifest_sha256"],
            "results": results, "ledgers": ledgers}

def main():
    p = argparse.ArgumentParser()
    for name in ("prices", "manifest", "funding", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if "v98_independent" not in a.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result = run(a.prices, a.manifest, a.funding)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    # Persist full position/equity chronology separately from compact summary.
    ledgers = result.pop("ledgers")
    for scenario, entries in ledgers.items():
        ledger_path = a.output.with_name(a.output.stem + "_" + scenario + "_ledger.jsonl")
        with ledger_path.open("w") as out:
            for entry in entries:
                out.write(json.dumps(entry, sort_keys=True, allow_nan=False) + "\n")
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
