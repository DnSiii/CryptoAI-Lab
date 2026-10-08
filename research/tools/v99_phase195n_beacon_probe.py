"""Phase195-N: preregistered two-operator fixed-slot historical Beacon availability.
DATA_ONLY. Provider responses are never authenticated consensus ancestry proofs.
"""
import hashlib
import json
import urllib.error
import urllib.request
from v99_phase195m_beacon_core import compare, slot_from_timestamp

PROVIDERS = (
    ("ethstaker", "https://beaconstate.ethstaker.cc"),
    ("chainsafe", "https://beaconstate-mainnet.chainsafe.io"),
)
MAX_RESPONSE_BYTES = 8_000_000
MISMATCH_REASONS = {
    "slot_mismatch", "execution_height_mismatch",
    "execution_timestamp_mismatch", "execution_hash_mismatch",
    "execution_receipts_root_mismatch",
}

def probe_one(name, base, slot, block, opener=urllib.request.urlopen):
    """Exactly one request to the predeclared operator and predeclared slot."""
    url = base + "/eth/v2/beacon/blocks/" + str(slot)
    result = {"provider": name, "slot": slot, "status": "HOLD_TRANSPORT"}
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "CryptoAI-Lab-Phase195N/1"}
    )
    try:
        with opener(req, timeout=30) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            result.update(status="HOLD_INVALID_RESPONSE", reason="oversize")
            return result
        result["response_sha256"] = hashlib.sha256(raw).hexdigest()
        beacon = json.loads(raw)
        parity = compare(block, beacon)
        if parity["slot"] != slot:
            raise ValueError("slot_mismatch")
        result.update(
            status="PROVISIONAL_PARITY_UNANCHORED",
            reported_finalized=True,
            execution_optimistic=False,
            payload_hash=parity["beacon_payload_block_hash"],
            payload_receipts_root=parity["beacon_payload_receipts_root"],
        )
    except urllib.error.HTTPError as exc:
        result.update(status="HOLD_HTTP", http_status=int(exc.code))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result.update(status="HOLD_TRANSPORT", reason=type(exc).__name__)
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        result.update(
            status="SAFETY_HALT_MISMATCH" if reason in MISMATCH_REASONS else "HOLD_INVALID_RESPONSE",
            reason=reason[:100],
        )
    return result

def run_probes(block, opener=urllib.request.urlopen):
    slot = slot_from_timestamp(int(block["timestamp"], 16))
    results = [probe_one(name, base, slot, block, opener) for name, base in PROVIDERS]
    matches = sum(p["status"] == "PROVISIONAL_PARITY_UNANCHORED" for p in results)
    if any(p["status"] == "SAFETY_HALT_MISMATCH" for p in results):
        decision = "SAFETY_HALT_BEACON_MISMATCH"
    elif matches == len(PROVIDERS):
        decision = "PROVISIONAL_TWO_PROVIDER_PARITY_UNANCHORED"
    elif matches:
        decision = "PROVISIONAL_ONE_PROVIDER_PARITY_UNANCHORED"
    else:
        decision = "HOLD_BEACON_ARCHIVE_UNAVAILABLE"
    return {
        "phase": "195-N", "scope": "DATA_ONLY", "height": 17000000,
        "slot": slot, "operators": results, "decision": decision,
        "economic_trials": 0, "holdout_accessed": False,
        "promotion_authorized": False, "independent_consensus_anchor": False,
        "historical_latency_proven": False, "full_train_coverage_proven": False,
    }
