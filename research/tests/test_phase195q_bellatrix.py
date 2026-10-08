"""Bellatrix SSZ adversarial tests for fixed TRAIN slot."""
import copy,json,pathlib,struct,sys,unittest,snappy
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from v99_phase195q_bellatrix import parse,SLOT,HEIGHT,TIMESTAMP,EXPECTED_HASH,EXPECTED_ROOT

def sample():
 payload=bytearray(508)
 payload[84:116]=bytes.fromhex(EXPECTED_ROOT[2:])
 payload[472:504]=bytes.fromhex(EXPECTED_HASH[2:])
 struct.pack_into("<Q",payload,404,HEIGHT)
 struct.pack_into("<Q",payload,428,TIMESTAMP)
 struct.pack_into("<I",payload,436,508)
 struct.pack_into("<I",payload,504,508)
 body=bytearray(384)
 for i in (200,204,208,212,216,380):struct.pack_into("<I",body,i,384)
 msg=bytearray(84)
 struct.pack_into("<Q",msg,0,SLOT)
 struct.pack_into("<I",msg,80,84)
 return bytearray(struct.pack("<I",100)+bytes(96)+msg+body+payload)

class Controls(unittest.TestCase):
 def test_valid_bellatrix(self):
  self.assertEqual(parse(sample())["fork"],"bellatrix")
 def test_determinism(self):
  self.assertEqual(parse(sample()),parse(sample()))
 def test_wrong_slot(self):
  x=sample();struct.pack_into("<Q",x,100,SLOT+1)
  with self.assertRaisesRegex(ValueError,"slot_mismatch"):parse(x)
 def test_wrong_height(self):
  x=sample();struct.pack_into("<Q",x,100+84+384+404,HEIGHT+1)
  with self.assertRaisesRegex(ValueError,"height_mismatch"):parse(x)
 def test_wrong_timestamp(self):
  x=sample();struct.pack_into("<Q",x,100+84+384+428,TIMESTAMP+12)
  with self.assertRaisesRegex(ValueError,"timestamp_mismatch"):parse(x)
 def test_wrong_hash(self):
  x=sample();x[100+84+384+472]^=1
  with self.assertRaisesRegex(ValueError,"hash_mismatch"):parse(x)
 def test_wrong_root(self):
  x=sample();x[100+84+384+84]^=1
  with self.assertRaisesRegex(ValueError,"root_mismatch"):parse(x)
 def test_signed_offset(self):
  x=sample();struct.pack_into("<I",x,0,104)
  with self.assertRaisesRegex(ValueError,"signed_offset"):parse(x)
 def test_body_offset(self):
  x=sample();struct.pack_into("<I",x,100+80,88)
  with self.assertRaisesRegex(ValueError,"body_offset"):parse(x)
 def test_payload_offsets(self):
  x=sample();struct.pack_into("<I",x,100+84+384+436,507)
  with self.assertRaisesRegex(ValueError,"payload_offsets"):parse(x)
 def test_snappy_frame_roundtrip(self):
  raw=bytes(sample())
  compressor=snappy.StreamCompressor()
  compressed=compressor.add_chunk(raw)
  self.assertEqual(snappy.StreamDecompressor().decompress(compressed),raw)

if __name__=="__main__":
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 if not result.wasSuccessful():raise SystemExit(1)
 print(json.dumps({"phase":"195-Q","controls":result.testsRun,"status":"PASS"}))
