"""Fail-closed structural gate for C27 prospective carry-in; NOT an economic replay.

The custodian must supply a separately authenticated snapshot. A syntactically
valid snapshot alone never establishes provenance or permits PnL publication.
"""
import hashlib
import json
import math
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
BASELINE = "6c609dacde9f197ba58ed23546bd14fda968a035"

def validate_carry(root, snapshot_path, expected_start_utc, expected_sha256):
    root = Path(root).resolve()
    path = Path(snapshot_path).resolve()
    if "v98_independent" not in root.parts or root not in path.parents or not path.is_file():
        raise ValueError("CARRY_NAMESPACE")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("CARRY_DIGEST")
    state = json.loads(raw)
    required = {"candidate_commit", "clock_utc", "equity_usd", "peak_equity_usd",
                "positions", "pending_orders", "decision_clock_utc",
                "warmup_receipt_sha256", "source_receipt_sha256"}
    if set(state) != required or state["candidate_commit"] != BASELINE:
        raise ValueError("CARRY_SCHEMA")
    if state["clock_utc"] != expected_start_utc or state["decision_clock_utc"] != expected_start_utc:
        raise ValueError("CARRY_CLOCK")
    if not all(isinstance(state[k], str) and len(state[k]) == 64
               and all(c in "0123456789abcdef" for c in state[k])
               for k in ("warmup_receipt_sha256", "source_receipt_sha256")):
        raise ValueError("CARRY_RECEIPTS")
    equity, peak = state["equity_usd"], state["peak_equity_usd"]
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
           for x in (equity, peak)) or not 0 < equity <= peak:
        raise ValueError("CARRY_EQUITY")
    if set(state["positions"]) != set(ASSETS):
        raise ValueError("CARRY_ASSETS")
    for asset in ASSETS:
        pos = state["positions"][asset]
        if set(pos) != {"quantity", "entry_price", "margin_usd"}:
            raise ValueError("CARRY_POSITION_SCHEMA")
        q, p, m = (pos[k] for k in ("quantity", "entry_price", "margin_usd"))
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
               for x in (q, p, m)) or p <= 0 or m < 0 or (q == 0 and m != 0):
            raise ValueError("CARRY_POSITION")
    if not isinstance(state["pending_orders"], list) or state["pending_orders"]:
        raise ValueError("CARRY_PENDING_ORDERS_UNSUPPORTED")
    return {"status": "STRUCTURE_ONLY_NOT_AUTHENTICATED_NOT_PNL",
            "snapshot_sha256": expected_sha256,
            "economic_replay_allowed": False,
            "missing": ["independent_snapshot_attestation", "warmup_replay",
                        "frozen_variable_horizon_executor", "native_execution_cost_reconciliation"]}
