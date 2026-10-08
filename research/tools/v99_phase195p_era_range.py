"""Phase195-P: fixed Era754 HTTP-range e2store structural retrieval.
DATA_ONLY. Not an authenticated consensus/SSZ proof.
"""
import hashlib
import json
import re
import struct
import urllib.error
import urllib.request

SLOT = 6173989
ERA = 754
SLOTS_PER_ERA = 8192
FILE_SIZE = 760093020
FILENAME = "mainnet-00754-b82788ae.era"
URL = "https://mainnet.era.nimbus.team/" + FILENAME
TAIL_SIZE = 32 + 8 + 8 + 8192 * 8 + 8
VERSION = bytes.fromhex("6532000000000000")
SNAPPY_FRAME = bytes.fromhex("ff060000734e61507059")

def range_read(start, end, opener=urllib.request.urlopen):
    """Require exact 206 and Content-Range; never stream full archive."""
    if not (0 <= start <= end < FILE_SIZE):
        raise ValueError("invalid_requested_range")
    req = urllib.request.Request(URL, headers={
        "Range": "bytes=" + str(start) + "-" + str(end),
        "User-Agent": "CryptoAI-Lab-Phase195P/1",
        "Accept-Encoding": "identity",
    })
    with opener(req, timeout=40) as response:
        status = getattr(response, "status", response.getcode())
        if status != 206:
            raise ValueError("range_http_" + str(status))
        header = response.headers.get("Content-Range", "")
        match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", header)
        if not match or tuple(map(int, match.groups())) != (start, end, FILE_SIZE):
            raise ValueError("content_range_mismatch")
        data = response.read(end - start + 2)
    if len(data) != end - start + 1:
        raise ValueError("range_length_mismatch")
    return data

def entry_header(data, expected_type):
    if len(data) < 8 or data[:2] != expected_type or data[6:8] != bytes(2):
        raise ValueError("e2store_entry_header_invalid")
    return struct.unpack("<I", data[2:6])[0]

def locate(tail):
    if len(tail) != TAIL_SIZE:
        raise ValueError("era_tail_length")
    state = tail[-32:]
    if entry_header(state, b"i2") != 24:
        raise ValueError("era_state_index_header")
    state_start = struct.unpack_from("<Q", state, 8)[0]
    state_count = struct.unpack_from("<Q", state, 24)[0]
    if state_start != ERA * SLOTS_PER_ERA or state_count != 1:
        raise ValueError("era_state_index_boundary")
    blocks = tail[:-32]
    if entry_header(blocks, b"i2") != 16 + SLOTS_PER_ERA * 8:
        raise ValueError("era_block_index_header")
    start_slot = struct.unpack_from("<Q", blocks, 8)[0]
    count = struct.unpack_from("<Q", blocks, len(blocks) - 8)[0]
    if start_slot != (ERA - 1) * SLOTS_PER_ERA or count != SLOTS_PER_ERA:
        raise ValueError("era_block_index_boundary")
    index = SLOT - start_slot
    relative = struct.unpack_from("<q", blocks, 16 + index * 8)[0]
    if relative == 0:
        raise ValueError("fixed_slot_absent")
    index_start = FILE_SIZE - TAIL_SIZE
    offset = index_start + relative
    if not (8 <= offset < index_start):
        raise ValueError("era_index_offset_out_of_bounds")
    return {"start_slot": start_slot, "state_start_slot": state_start,
            "index": index, "relative_offset": relative, "absolute_offset": offset}

def run(reader=range_read):
    out = {"phase": "195-P", "scope": "DATA_ONLY", "slot": SLOT,
           "era": ERA, "filename": FILENAME, "economic_trials": 0,
           "holdout_accessed": False, "promotion_authorized": False,
           "independent_consensus_anchor": False, "full_train_coverage_proven": False}
    try:
        if reader(0, 7) != VERSION:
            raise ValueError("e2store_version_magic")
        tail = reader(FILE_SIZE - TAIL_SIZE, FILE_SIZE - 1)
        out["tail_sha256"] = hashlib.sha256(tail).hexdigest()
        loc = locate(tail)
        out.update(loc)
        pos = loc["absolute_offset"]
        head = reader(pos, pos + 7)
        n = entry_header(head, bytes.fromhex("0100"))
        if not (10 <= n <= 2_000_000) or pos + 8 + n >= FILE_SIZE - TAIL_SIZE:
            raise ValueError("compressed_block_size_invalid")
        compressed = reader(pos + 8, pos + 7 + n)
        if compressed[:10] != SNAPPY_FRAME:
            raise ValueError("snappy_frame_magic")
        out.update(record_bytes=n, record_sha256=hashlib.sha256(compressed).hexdigest(),
                   decision="PROVISIONAL_ERA_RECORD_AVAILABLE_UNANCHORED")
    except urllib.error.HTTPError as exc:
        out.update(decision="HOLD_ERA_TRANSPORT", reason="http_" + str(exc.code))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        out.update(decision="HOLD_ERA_TRANSPORT", reason=type(exc).__name__)
    except (ValueError, TypeError, KeyError) as exc:
        out.update(decision="HOLD_ERA_STRUCTURE_OR_RANGE", reason=str(exc)[:100])
    return out

if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, separators=(",", ":")))
