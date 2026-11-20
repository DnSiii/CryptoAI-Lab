"""Training-only forensic audit of rejected C26 exposure drift; never promotes."""
import argparse
import json
import math
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
SCENARIOS = ("1x", "2x", "4x")
CAP_TOTAL = .90
CAP_ASSET = .40
EPS = 1e-9

def inspect(summary_path):
    summary_path = Path(summary_path)
    summary = json.loads(summary_path.read_text())
    if summary.get("source") != "AUTHENTICATED_CLEAN4" or summary.get("holdout_accessed") is not False:
        raise ValueError("SOURCE_OR_HOLDOUT_CONTRACT")
    if set(summary["results"]) != set(SCENARIOS):
        raise ValueError("SCENARIO_CONTRACT")
    output = {}
    for scenario in SCENARIOS:
        ledger_path = summary_path.with_name(summary_path.stem + "_" + scenario + "_ledger.jsonl")
        counts = {"pre":0, "post":0, "pre_total":0, "post_total":0,
                  "pre_asset":0, "post_asset":0, "off_calendar_trades":0}
        max_total = {"pre":0., "post":0.}
        max_asset = {"pre":0., "post":0.}
        first = {"pre":None, "post":None}
        rows = 0
        with ledger_path.open() as fh:
            for line in fh:
                if not line.strip():
                    continue
                e = json.loads(line)
                rows += 1
                if e["index"] != rows:
                    raise ValueError("ROW_SEQUENCE")
                for side, field in (("pre","weights_before_fill"),("post","weights_after_fill")):
                    weights = e[field]
                    if set(weights) != set(ASSETS) or not all(math.isfinite(float(v)) for v in weights.values()):
                        raise ValueError("INVALID_WEIGHTS")
                    total = sum(abs(v) for v in weights.values())
                    asset = max(abs(v) for v in weights.values())
                    max_total[side] = max(max_total[side], total)
                    max_asset[side] = max(max_asset[side], asset)
                    excess_total = total > CAP_TOTAL + EPS
                    excess_asset = asset > CAP_ASSET + EPS
                    counts[side+"_total"] += int(excess_total)
                    counts[side+"_asset"] += int(excess_asset)
                    if excess_total or excess_asset:
                        counts[side] += 1
                        if first[side] is None:
                            first[side] = dict(index=rows,total=total,asset=asset)
                if e["turnover"] > EPS and not (rows >= 4321 and (rows-4321)%168 == 0):
                    counts["off_calendar_trades"] += 1
        if rows != 27047 or summary["results"][scenario]["hours"] != 27048:
            raise ValueError("INCOMPLETE_HISTORY")
        output[scenario] = dict(rows=rows, violations=counts, first=first,
                                max_total=max_total, max_asset=max_asset,
                                decision="REJECTED_DIAGNOSTIC_ONLY")
    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if "v98_independent" not in args.summary.resolve().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    print(json.dumps(inspect(args.summary), indent=2, sort_keys=True, allow_nan=False))

if __name__ == "__main__":
    main()
