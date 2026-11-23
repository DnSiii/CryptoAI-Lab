"""Independent fail-closed reconciliation of C27 training checkpoint artifacts.

Training only. Does not attest future performance or authorize paper.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")

def audit(summary_path):
    summary_path = Path(summary_path).resolve()
    if "v98_independent" not in summary_path.parts:
        raise ValueError("C27_CHECKPOINT_NAMESPACE")
    summary = json.loads(summary_path.read_text())
    if summary.get("holdout_accessed") is not False or summary.get("source") != "AUTHENTICATED_CLEAN4":
        raise ValueError("C27_CHECKPOINT_UNAUTHENTICATED_SUMMARY")
    receipts = summary.get("training_checkpoint_receipts", {})
    if set(receipts) != {"1x", "2x", "4x"}:
        raise ValueError("C27_CHECKPOINT_RECEIPTS_MISSING")
    result = {}
    for scale in ("1x", "2x", "4x"):
        ledger_path = summary_path.with_name(summary_path.stem + "_" + scale + "_ledger.jsonl")
        checkpoint_path = summary_path.with_name(summary_path.stem + "_" + scale + "_checkpoint.json")
        digest = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
        if receipts[scale].get("checkpoint_sha256") != digest:
            raise ValueError("C27_CHECKPOINT_DIGEST_MISMATCH_" + scale)
        checkpoint = json.loads(checkpoint_path.read_text())
        if checkpoint.get("absolute_index") != 27048 or receipts[scale].get("absolute_index") != 27048:
            raise ValueError("C27_CHECKPOINT_CLOCK_" + scale)
        rows = 0
        peak = 10000.0
        last = None
        with ledger_path.open() as f:
            for line in f:
                row = json.loads(line)
                rows += 1
                if type(row.get("index")) is not int or row["index"] != rows:
                    raise ValueError("C27_CHECKPOINT_LEDGER_ORDER_" + scale)
                for field in ("equity", "pre_fill_equity"):
                    v = row.get(field)
                    if type(v) not in (float, int) or not math.isfinite(v) or v <= 0:
                        raise ValueError("C27_CHECKPOINT_LEDGER_FINITE_" + scale)
                    peak = max(peak, v)
                last = row
        if rows != 27047:
            raise ValueError("C27_CHECKPOINT_LEDGER_LENGTH_" + scale)
        if not math.isclose(checkpoint["equity"], last["equity"], rel_tol=1e-12):
            raise ValueError("C27_CHECKPOINT_EQUITY_" + scale)
        if not math.isclose(checkpoint["peak"], peak, rel_tol=1e-12):
            raise ValueError("C27_CHECKPOINT_PEAK_" + scale)
        if checkpoint.get("decision_equity") != checkpoint["equity"] or checkpoint.get("decision_peak") != checkpoint["peak"]:
            raise ValueError("C27_CHECKPOINT_DECISION_CLOCK_" + scale)
        for field, ledger_field in (("weights", "weights_after_fill"), ("queued", "queued_next_open_sell_fractions")):
            if set(checkpoint.get(field, {})) != set(ASSETS) or set(last.get(ledger_field, {})) != set(ASSETS):
                raise ValueError("C27_CHECKPOINT_ASSETS_" + scale)
            for asset in ASSETS:
                if not math.isclose(checkpoint[field][asset], last[ledger_field][asset], abs_tol=1e-12):
                    raise ValueError("C27_CHECKPOINT_BOOK_" + scale + "_" + asset)
        for asset in ASSETS:
            history = checkpoint.get("histories", {}).get(asset, [])
            if len(history) != 27048 or not math.isclose(history[-1], history[-1], rel_tol=0):
                raise ValueError("C27_CHECKPOINT_HISTORY_" + scale + "_" + asset)
            if type(checkpoint.get("previous_open", {}).get(asset)) not in (float, int):
                raise ValueError("C27_CHECKPOINT_PREVIOUS_OPEN_" + scale + "_" + asset)
            if not all(math.isfinite(v) and v > 0 for v in (history[-1], checkpoint["previous_open"][asset])):
                raise ValueError("C27_CHECKPOINT_MARK_" + scale + "_" + asset)
        result[scale] = {"rows": rows, "sha256": digest, "equity_at_last_open": checkpoint["equity"],
                         "peak": peak, "status": "LEDGER_CHECKPOINT_RECONCILED_TRAINING_ONLY"}
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if "v98_independent" not in args.output.resolve().parts:
        raise ValueError("C27_CHECKPOINT_OUTPUT_NAMESPACE")
    result = audit(args.summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("C27_CHECKPOINT_LEDGER_RECONCILED_TRAINING_ONLY", json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
