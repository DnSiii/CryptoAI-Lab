#!/usr/bin/env python3
"""Phase195-N fixed TRAIN beacon operators; no slot-search, no PnL."""
import json
from v99_phase195l_header import H, verify_header
from v99_phase195l_rpc import rpc
from v99_phase195n_beacon_probe import run_probes

EXPECTED_HASH = "0x96cfa0fb5e50b0a3f6cc76f3299cfbf48f17e8b41798d1394474e67ec8a97e9f"
EXPECTED_ROOT = "0xdafc7e17d609503a08b1406eb69c714cb3e7ba51e84580977c449999068ae513"

def run(call=rpc):
    try:
        block = call("https://eth.drpc.org", "eth_getBlockByNumber", [hex(H), False])
        verify_header(block)
        if block["hash"].lower() != EXPECTED_HASH:
            raise ValueError("fixed_train_hash_changed")
        if block["receiptsRoot"].lower() != EXPECTED_ROOT:
            raise ValueError("fixed_train_root_changed")
        return run_probes(block)
    except Exception as exc:
        return {
            "phase": "195-N", "scope": "DATA_ONLY", "height": H,
            "decision": "HOLD_EXECUTION_HEADER",
            "reason": str(exc)[:120] if isinstance(exc, ValueError) else type(exc).__name__,
            "economic_trials": 0, "holdout_accessed": False,
            "promotion_authorized": False, "independent_consensus_anchor": False,
            "historical_latency_proven": False, "full_train_coverage_proven": False,
        }

if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, separators=(",", ":")))
