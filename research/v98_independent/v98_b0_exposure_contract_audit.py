"""Independent V98 B0 exposure audit of the existing next-open ledger.

No parameter tuning, holdout access, or strategy promotion. Distinguishes
pre-fill market drift from post-fill target caps defined in causal overlay.
"""
import argparse
import json
import math
from pathlib import Path

ASSET_CAP = 0.40
GROSS_CAP = 0.75
EPS = 1e-10


def audit(entries):
    if not entries:
        raise ValueError("EMPTY_LEDGER")
    stats = {"rows": 0, "before_asset_cap_breaches": 0,
             "before_gross_cap_breaches": 0, "after_asset_cap_breaches": 0,
             "after_gross_cap_breaches": 0, "max_before_asset": 0.0,
             "max_before_gross": 0.0, "max_after_asset": 0.0,
             "max_after_gross": 0.0}
    for expected_index, row in enumerate(entries, start=1):
        if row["index"] != expected_index:
            raise ValueError("NONCONTIGUOUS_LEDGER")
        for stage, field in (("before", "weights_before_fill"),
                             ("after", "weights_after_fill")):
            weights = row[field]
            if len(weights) != 4 or any(not math.isfinite(float(w)) or float(w) < 0
                                        for w in weights.values()):
                raise ValueError("INVALID_WEIGHTS")
            largest = max(weights.values())
            gross = sum(weights.values())
            stats["max_" + stage + "_asset"] = max(stats["max_" + stage + "_asset"], largest)
            stats["max_" + stage + "_gross"] = max(stats["max_" + stage + "_gross"], gross)
            stats[stage + "_asset_cap_breaches"] += int(largest > ASSET_CAP + EPS)
            stats[stage + "_gross_cap_breaches"] += int(gross > GROSS_CAP + EPS)
        stats["rows"] += 1
    stats["post_fill_gate_pass"] = not (stats["after_asset_cap_breaches"] or
                                         stats["after_gross_cap_breaches"])
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    with args.ledger.open() as handle:
        result = audit(json.loads(line) for line in handle if line.strip())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
