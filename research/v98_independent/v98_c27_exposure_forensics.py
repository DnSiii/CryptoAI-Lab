"""C27 exposure forensics: distinguish delayed gap drift from actionable post-fill breaches.

Research-only; uses authenticated training ledger, never a holdout or promotion.
"""
import argparse
import json
import math
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
SCENARIOS = ("1x", "2x", "4x")
TOL = 1e-9

def analyze(summary_path):
    summary_path = Path(summary_path)
    summary = json.loads(summary_path.read_text())
    if summary.get("source") != "AUTHENTICATED_CLEAN4" or summary.get("holdout_accessed") is not False:
        raise ValueError("C27_WRONG_SOURCE_OR_HOLDOUT")
    asset_buffer = float(summary["buffer_asset"])
    gross_buffer = float(summary["buffer_gross"])
    if not (0 < asset_buffer < .40 and 0 < gross_buffer < .90):
        raise ValueError("C27_INVALID_PRECOMMITTED_BUFFERS")
    result = {"status": "TRAINING_EXPOSURE_FORENSICS_NOT_VALIDATION", "scenarios": {}}
    for scenario in SCENARIOS:
        path = summary_path.with_name(summary_path.stem + "_" + scenario + "_ledger.jsonl")
        count = 0
        before_buffer = before_hard = after_buffer = after_hard = 0
        max_before_asset = max_after_asset = max_before_gross = max_after_gross = 0.
        delayed_buffer_events = 0
        prev_queue = {a: 0. for a in ASSETS}
        for raw in path.open():
            row = json.loads(raw)
            count += 1
            if row["index"] != count:
                raise ValueError("C27_NONCHRONOLOGICAL_LEDGER")
            before, after = row["weights_before_fill"], row["weights_after_fill"]
            for book in (before, after):
                if set(book) != set(ASSETS) or any(not math.isfinite(float(v)) or float(v) < -TOL for v in book.values()):
                    raise ValueError("C27_INVALID_EXPOSURE")
            b_asset, a_asset = max(before.values()), max(after.values())
            b_gross, a_gross = sum(before.values()), sum(after.values())
            max_before_asset, max_after_asset = max(max_before_asset, b_asset), max(max_after_asset, a_asset)
            max_before_gross, max_after_gross = max(max_before_gross, b_gross), max(max_after_gross, a_gross)
            b_buf = b_asset > asset_buffer + TOL or b_gross > gross_buffer + TOL
            a_buf = a_asset > asset_buffer + TOL or a_gross > gross_buffer + TOL
            b_hard = b_asset > .40 + TOL or b_gross > .90 + TOL
            a_hard = a_asset > .40 + TOL or a_gross > .90 + TOL
            before_buffer += b_buf
            after_buffer += a_buf
            before_hard += b_hard
            after_hard += a_hard
            if b_buf and not a_buf:
                delayed_buffer_events += 1
            if bool(row["hard_cap_breach_after_fill"]) != a_hard:
                raise ValueError("C27_HARD_CAP_FLAG_MISMATCH")
            if a_buf:
                raise ValueError(f"C27_BUFFER_NOT_ENFORCED_AFTER_FILL_{scenario}_{count}")
            if a_hard:
                raise ValueError(f"C27_HARD_CAP_AFTER_FILL_{scenario}_{count}")
            if row["order_type"] == "safety" and not any(v > TOL for v in prev_queue.values()):
                raise ValueError("C27_UNQUEUED_SAFETY_ORDER")
            prev_queue = row["queued_next_open_sell_fractions"]
            if set(prev_queue) != set(ASSETS) or any(not 0 <= float(v) <= 1 for v in prev_queue.values()):
                raise ValueError("C27_INVALID_QUEUE")
        if count != 27047:
            raise ValueError("C27_INCOMPLETE_LEDGER")
        result["scenarios"][scenario] = {
            "checked_hours": count, "pre_fill_buffer_excursions": before_buffer,
            "pre_fill_hard_cap_excursions": before_hard,
            "post_fill_buffer_excursions": after_buffer,
            "post_fill_hard_cap_excursions": after_hard,
            "buffer_excursions_corrected_at_open": delayed_buffer_events,
            "max_pre_fill_asset": max_before_asset, "max_post_fill_asset": max_after_asset,
            "max_pre_fill_gross": max_before_gross, "max_post_fill_gross": max_after_gross,
        }
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if "v98_independent" not in args.summary.resolve().parts or "v98_independent" not in args.output.resolve().parts:
        raise ValueError("C27_NAMESPACE_REQUIRED")
    args.output.write_text(json.dumps(analyze(args.summary), indent=2, sort_keys=True) + "\n")
    print(args.output.read_text())

if __name__ == "__main__":
    main()
