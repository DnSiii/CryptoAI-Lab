"""Phase195-O: fixed historical Beacon header vs finalized-header liveness.
Read-only, DATA_ONLY, never a trusted consensus proof.
"""
import hashlib
import json
import urllib.error
import urllib.request

SLOT = 6173989
OPERATORS = (
    ("ethstaker", "https://beaconstate.ethstaker.cc"),
    ("chainsafe", "https://beaconstate-mainnet.chainsafe.io"),
)
MAX_BYTES = 1_000_000

def probe(name, base, suffix, historical, opener=urllib.request.urlopen):
    url = base + "/eth/v1/beacon/headers/" + suffix
    result = {"operator": name, "probe": "historical" if historical else "finalized_control",
              "status": "HOLD_TRANSPORT"}
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": "CryptoAI-Lab-Phase195O/1"
    })
    try:
        with opener(req, timeout=30) as response:
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return dict(result, status="HOLD_INVALID_RESPONSE", reason="oversize")
        result["sha256"] = hashlib.sha256(raw).hexdigest()
        obj = json.loads(raw)
        header = obj["data"]["header"]
        reported_slot = int(header["message"]["slot"])
        if reported_slot < 0:
            raise ValueError("negative_slot")
        result["reported_slot"] = reported_slot
        if historical and reported_slot != SLOT:
            return dict(result, status="SAFETY_HALT_SLOT_MISMATCH")
        if historical and obj["data"].get("canonical") is not True:
            return dict(result, status="HOLD_CANONICALITY_NOT_REPORTED")
        result["status"] = ("PROVISIONAL_HISTORICAL_HEADER_UNANCHORED"
                            if historical else "FINALIZED_HEADER_CONTROL_REPORTED")
    except urllib.error.HTTPError as exc:
        result.update(status="HOLD_HTTP", http_status=int(exc.code))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result.update(status="HOLD_TRANSPORT", reason=type(exc).__name__)
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        result.update(status="HOLD_INVALID_RESPONSE", reason=type(exc).__name__)
    return result

def run(opener=urllib.request.urlopen):
    results = []
    for name, base in OPERATORS:
        results.append(probe(name, base, "finalized", False, opener))
        results.append(probe(name, base, str(SLOT), True, opener))
    historical = [x for x in results if x["probe"] == "historical"]
    controls = [x for x in results if x["probe"] == "finalized_control"]
    if any(x["status"] == "SAFETY_HALT_SLOT_MISMATCH" for x in results):
        decision = "SAFETY_HALT_SLOT_MISMATCH"
    elif any(x["status"] == "PROVISIONAL_HISTORICAL_HEADER_UNANCHORED" for x in historical):
        decision = "PROVISIONAL_HEADER_AVAILABILITY_UNANCHORED"
    elif any(x["status"] == "FINALIZED_HEADER_CONTROL_REPORTED" for x in controls):
        decision = "HOLD_HISTORICAL_ARCHIVE_MISSING"
    else:
        decision = "HOLD_PROVIDER_TRANSPORT_OR_SCHEMA"
    return {
        "phase": "195-O", "scope": "DATA_ONLY", "slot": SLOT, "decision": decision,
        "probes": results, "economic_trials": 0, "holdout_accessed": False,
        "promotion_authorized": False, "independent_consensus_anchor": False,
        "full_train_coverage_proven": False, "historical_latency_proven": False,
    }

if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, separators=(",", ":")))
