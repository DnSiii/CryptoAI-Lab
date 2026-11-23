"""Cross-executor C27 training continuation: fixed split, no holdout or promotion."""
import argparse
import json
import math
from pathlib import Path
from .phase243_native_funding_cashflow import ASSETS, HOUR_MS
from .v98_phase243_training_reader import load, START_MS
from .v98_c27_authenticated_runner import replay
from .v98_c27_variable_horizon_kernel import continue_replay

SPLIT = 12000  # fixed 2024 training boundary, never selected by performance

def audit(prices, manifest, funding_path):
    data = load(prices, manifest, funding_path)
    if data["hours"] != 27048:
        raise ValueError("C27_CROSS_EXECUTOR_INCOMPLETE")
    funding = {a: {} for a in ASSETS}
    for a in ASSETS:
        for stamp, rate in data["funding"][a].items():
            offset = stamp - START_MS
            if offset % HOUR_MS or not 0 <= offset < 27048 * HOUR_MS:
                raise ValueError("C27_CROSS_EXECUTOR_FUNDING_CLOCK")
            funding[a][offset // HOUR_MS] = rate
    bars = data["bars"]
    verdict = {}
    for scale in (1., 2., 4.):
        summary, full = replay(bars, funding, scale)
        prefix = full[:SPLIT - 1]
        last = prefix[-1]
        state = dict(
            equity=last["equity"],
            peak=max([10000.] + [max(x["equity"], x["pre_fill_equity"]) for x in prefix]),
            weights=dict(last["weights_after_fill"]),
            queued=dict(last["queued_next_open_sell_fractions"]),
            histories={a: [bars[a][j][3] for j in range(SPLIT)] for a in ASSETS},
            previous_open={a: bars[a][SPLIT - 1][0] for a in ASSETS},
            decision_equity=last["equity"],
            decision_peak=max([10000.] + [max(x["equity"], x["pre_fill_equity"]) for x in prefix]),
            absolute_index=SPLIT)
        # The test must cross a serialization boundary, not reuse mutable objects.
        state = json.loads(json.dumps(state, sort_keys=True, allow_nan=False))
        suffix_bars = {a: bars[a][SPLIT:] for a in ASSETS}
        suffix_funding = {a: {i-SPLIT: v for i,v in funding[a].items() if i >= SPLIT} for a in ASSETS}
        continued = continue_replay(suffix_bars, suffix_funding, scale, state)
        expected = full[SPLIT-1:]
        actual = continued["ledger"]
        if len(actual) != len(expected):
            raise ValueError("C27_CROSS_EXECUTOR_LENGTH")
        fields = ("index", "equity", "turnover", "cost_return", "gross_return",
                  "funding_return", "order_type", "weights_after_fill",
                  "queued_next_open_sell_fractions")
        for index, (a, b) in enumerate(zip(actual, expected)):
            for key in fields:
                if a[key] != b[key]:
                    raise ValueError(f"C27_CROSS_EXECUTOR_DIVERGENCE scale={scale} index={SPLIT+index} field={key}")
        if not math.isclose(continued["final_equity"], summary["final_equity"], rel_tol=1e-12):
            raise ValueError("C27_CROSS_EXECUTOR_TERMINAL")
        # A second fixed 2024/2025 training boundary tests carry_out from the
        # continuation kernel itself, rather than reconstructing it from the
        # original historical ledger. The state crosses a JSON boundary again.
        second_split = 18000
        first_n = second_split - SPLIT
        first_bars = {a: bars[a][SPLIT:second_split] for a in ASSETS}
        first_funding = {a: {i-SPLIT: v for i, v in funding[a].items()
                             if SPLIT <= i < second_split} for a in ASSETS}
        first = continue_replay(first_bars, first_funding, scale, state)
        carried = json.loads(json.dumps(first["carry_out"], sort_keys=True, allow_nan=False))
        if carried["absolute_index"] != second_split:
            raise ValueError("C27_CROSS_EXECUTOR_SECOND_CLOCK")
        second_bars = {a: bars[a][second_split:] for a in ASSETS}
        second_funding = {a: {i-second_split: v for i, v in funding[a].items()
                              if i >= second_split} for a in ASSETS}
        second = continue_replay(second_bars, second_funding, scale, carried)
        stitched = first["ledger"] + second["ledger"]
        if len(stitched) != len(expected):
            raise ValueError("C27_CROSS_EXECUTOR_STITCH_LENGTH")
        for index, (a, b) in enumerate(zip(stitched, expected)):
            for key in fields:
                if a[key] != b[key]:
                    raise ValueError(f"C27_CROSS_EXECUTOR_STITCH_DIVERGENCE scale={scale} index={SPLIT+index} field={key}")
        if not math.isclose(second["final_equity"], summary["final_equity"], rel_tol=1e-12):
            raise ValueError("C27_CROSS_EXECUTOR_STITCH_TERMINAL")
        verdict[f"{int(scale)}x"] = dict(compared_hours=len(actual),
            stitched_hours=len(stitched), status="CROSS_EXECUTOR_EQUAL_TRAINING_ONLY")
    return verdict

def main():
    parser = argparse.ArgumentParser()
    for name in ("prices", "manifest", "funding", "output"):
        parser.add_argument("--"+name, required=True, type=Path)
    args = parser.parse_args()
    if "v98_independent" not in args.output.resolve().parts:
        raise ValueError("C27_CROSS_EXECUTOR_NAMESPACE")
    result = audit(args.prices, args.manifest, args.funding)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print("C27_CROSS_EXECUTOR_TRAINING_ONLY", json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
