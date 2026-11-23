"""Derive an auditable C27 continuation checkpoint from authenticated training artifacts.

No fitting, no future data, no synthetic reset. The caller must independently
verify the source manifests and the full C27 ledger before using this output.
"""
import hashlib
import json
import math
from pathlib import Path
from .phase243_native_funding_cashflow import ASSETS
from .v98_c27_authenticated_runner import ASSET_BUFFER, GROSS_BUFFER

def build_checkpoint(bars, ledger, *, initial_equity=10000.0):
    """Produce the next-open state from a *complete* 27048-hour training replay.

    Ledger must be the exact 27047-row C27 training ledger for one fixed cost
    scenario, already reconciled independently against authenticated sources.
    """
    if set(bars) != set(ASSETS) or any(len(bars[a]) != 27048 for a in ASSETS):
        raise ValueError("C27_CHECKPOINT_INCOMPLETE_SOURCE")
    if len(ledger) != 27047 or any(type(r.get("index")) is not int or r["index"] != i + 1
                                  for i, r in enumerate(ledger)):
        raise ValueError("C27_CHECKPOINT_LEDGER_CLOCK")
    if not math.isfinite(initial_equity) or initial_equity <= 0:
        raise ValueError("C27_CHECKPOINT_INITIAL_EQUITY")
    last = ledger[-1]
    required = ("equity", "weights_after_fill", "queued_next_open_sell_fractions")
    if any(k not in last for k in required):
        raise ValueError("C27_CHECKPOINT_TERMINAL_FIELDS")
    equity = float(last["equity"])
    if not math.isfinite(equity) or equity <= 0:
        raise ValueError("C27_CHECKPOINT_EQUITY")
    if any(not isinstance(r.get("equity"), (int,float)) or
           not math.isfinite(r["equity"]) or r["equity"] <= 0 for r in ledger):
        raise ValueError("C27_CHECKPOINT_LEDGER_EQUITY")
    # Training replay audits the pre-fill opening high-water mark too.
    if any(not isinstance(r.get("pre_fill_equity"), (int,float)) or
           not math.isfinite(r["pre_fill_equity"]) or r["pre_fill_equity"] <= 0 for r in ledger):
        raise ValueError("C27_CHECKPOINT_LEDGER_PRE_FILL")
    peak = max([float(initial_equity)] +
               [max(float(r["equity"]),float(r["pre_fill_equity"])) for r in ledger])
    weights = last["weights_after_fill"]
    queued = last["queued_next_open_sell_fractions"]
    if set(weights) != set(ASSETS) or set(queued) != set(ASSETS):
        raise ValueError("C27_CHECKPOINT_BOOK_ASSETS")
    for a in ASSETS:
        if type(weights[a]) not in (int,float) or not math.isfinite(weights[a]) or not 0 <= weights[a] <= ASSET_BUFFER + 1e-10:
            raise ValueError("C27_CHECKPOINT_WEIGHTS")
        if type(queued[a]) not in (int,float) or not math.isfinite(queued[a]) or not 0 <= queued[a] <= 1:
            raise ValueError("C27_CHECKPOINT_QUEUE")
    if sum(weights.values()) > GROSS_BUFFER + 1e-10:
        raise ValueError("C27_CHECKPOINT_GROSS")
    histories = {}
    previous_open = {}
    for a in ASSETS:
        rows = bars[a]
        if any(len(row) != 5 or not all(type(v) in (int,float) and math.isfinite(v) for v in row)
               or min(row[:4]) <= 0 or row[2] > min(row[0],row[3])
               or row[1] < max(row[0],row[3]) or row[4] < 0 for row in rows):
            raise ValueError("C27_CHECKPOINT_BAD_SOURCE")
        histories[a] = [float(r[3]) for r in rows]
        previous_open[a] = float(rows[-1][0])
    # At the last training open, the decision clock was updated after the fill.
    # The terminal close mark is NOT part of this carry state.
    return dict(equity=equity, peak=peak, weights=dict(weights), queued=dict(queued),
                histories=histories, decision_equity=equity, decision_peak=peak,
                absolute_index=27048, previous_open=previous_open)

def write_checkpoint(bars, ledger, output):
    output = Path(output).resolve()
    if "v98_independent" not in output.parts:
        raise ValueError("C27_CHECKPOINT_NAMESPACE")
    state = build_checkpoint(bars, ledger)
    payload = (json.dumps(state, sort_keys=True, separators=(",",":"), allow_nan=False) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    return {"checkpoint_sha256": hashlib.sha256(payload).hexdigest(),
            "status": "TRAINING_DERIVED_UNATTESTED_UNTIL_SOURCE_AND_LEDGER_AUDIT",
            "absolute_index": state["absolute_index"]}
