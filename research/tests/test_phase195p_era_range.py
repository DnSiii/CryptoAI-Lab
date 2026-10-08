"""Phase195-P synthetic e2store index and bounded HTTP range controls."""
import copy
import hashlib
import io
import json
import pathlib
import struct
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from v99_phase195p_era_range import (
    SLOT, ERA, FILE_SIZE, TAIL_SIZE, VERSION, SNAPPY_FRAME,
    locate, range_read, run,
)

def synthetic():
    tail = bytearray(TAIL_SIZE)
    b = len(tail) - 32
    tail[0:2] = b"i2"
    struct.pack_into("<I", tail, 2, 16 + 8192 * 8)
    struct.pack_into("<Q", tail, 8, (ERA - 1) * 8192)
    struct.pack_into("<Q", tail, b - 8, 8192)
    tail[b:b+2] = b"i2"
    struct.pack_into("<I", tail, b+2, 24)
    struct.pack_into("<Q", tail, b+8, ERA * 8192)
    struct.pack_into("<Q", tail, b+24, 1)
    pos = FILE_SIZE - TAIL_SIZE - 1000
    struct.pack_into("<q", tail, 16 + (SLOT - (ERA - 1) * 8192) * 8, -1000)
    compressed = SNAPPY_FRAME + bytes(range(20))
    header = bytes.fromhex("0100") + struct.pack("<I", len(compressed)) + bytes(2)
    values = {
        (0, 7): VERSION,
        (FILE_SIZE - TAIL_SIZE, FILE_SIZE - 1): bytes(tail),
        (pos, pos + 7): header,
        (pos + 8, pos + 7 + len(compressed)): compressed,
    }
    def reader(a, z):
        return values[(a, z)]
    return tail, values, reader, pos

class FakeResponse:
    def __init__(self, status, header, data):
        self.status = status
        self.headers = {"Content-Range": header}
        self.data = io.BytesIO(data)
    def getcode(self):
        return self.status
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, n=-1):
        return self.data.read(n)

class Controls(unittest.TestCase):
    def test_full_synthetic_record(self):
        _, _, reader, pos = synthetic()
        r = run(reader)
        self.assertEqual(r["decision"], "PROVISIONAL_ERA_RECORD_AVAILABLE_UNANCHORED")
        self.assertEqual(r["absolute_offset"], pos)
        self.assertEqual(r["record_bytes"], 30)
        self.assertFalse(r["independent_consensus_anchor"])
        self.assertFalse(r["promotion_authorized"])
        self.assertEqual(r["economic_trials"], 0)

    def test_deterministic(self):
        _, _, reader, _ = synthetic()
        self.assertEqual(run(reader), run(reader))

    def test_fixed_slot_index(self):
        tail, _, _, _ = synthetic()
        self.assertEqual(locate(tail)["index"], SLOT - (ERA - 1) * 8192)

    def test_missing_slot_rejected(self):
        tail, _, _, _ = synthetic()
        struct.pack_into("<q", tail, 16 + (SLOT - (ERA - 1) * 8192) * 8, 0)
        with self.assertRaisesRegex(ValueError, "fixed_slot_absent"):
            locate(tail)

    def test_state_boundary_rejected(self):
        tail, _, _, _ = synthetic()
        struct.pack_into("<Q", tail, len(tail) - 32 + 8, 0)
        with self.assertRaisesRegex(ValueError, "era_state_index_boundary"):
            locate(tail)

    def test_block_count_rejected(self):
        tail, _, _, _ = synthetic()
        struct.pack_into("<Q", tail, len(tail) - 32 - 8, 8191)
        with self.assertRaisesRegex(ValueError, "era_block_index_boundary"):
            locate(tail)

    def test_invalid_offset_rejected(self):
        tail, _, _, _ = synthetic()
        struct.pack_into("<q", tail, 16 + (SLOT - (ERA - 1) * 8192) * 8, 100)
        with self.assertRaisesRegex(ValueError, "era_index_offset_out_of_bounds"):
            locate(tail)

    def test_bad_version_rejected(self):
        _, values, _, _ = synthetic()
        values[(0, 7)] = bytes(8)
        self.assertEqual(run(lambda a,z:values[(a,z)])["reason"], "e2store_version_magic")

    def test_bad_snappy_rejected(self):
        _, values, _, pos = synthetic()
        k = next(k for k in values if k[0] == pos + 8)
        values[k] = bytes(len(values[k]))
        self.assertEqual(run(lambda a,z:values[(a,z)])["reason"], "snappy_frame_magic")

    def test_good_bounded_http_range(self):
        opener = lambda req, timeout: FakeResponse(206, "bytes 0-7/" + str(FILE_SIZE), VERSION)
        self.assertEqual(range_read(0,7,opener), VERSION)

    def test_full_body_http200_rejected_without_read(self):
        opener = lambda req, timeout: FakeResponse(200, "", b"")
        with self.assertRaisesRegex(ValueError, "range_http_200"):
            range_read(0,7,opener)

    def test_content_range_mismatch_rejected(self):
        opener = lambda req, timeout: FakeResponse(206, "bytes 1-8/" + str(FILE_SIZE), VERSION)
        with self.assertRaisesRegex(ValueError, "content_range_mismatch"):
            range_read(0,7,opener)

    def test_short_read_rejected(self):
        opener = lambda req, timeout: FakeResponse(206, "bytes 0-7/" + str(FILE_SIZE), VERSION[:4])
        with self.assertRaisesRegex(ValueError, "range_length_mismatch"):
            range_read(0,7,opener)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(json.dumps({"phase":"195-P","synthetic_controls":result.testsRun,"status":"PASS"}))
