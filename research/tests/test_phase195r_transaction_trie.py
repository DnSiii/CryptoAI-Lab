"""Phase195-R synthetic transaction-list offset and MPT controls."""
import json,pathlib,struct,sys,unittest,rlp
from trie import HexaryTrie
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from test_phase195q_bellatrix import sample
from v99_phase195r_transaction_trie import transactions
BASE=100+84+384
def make(txs=None):
 if txs is None:txs=[bytes([2,i])+bytes([i])*4 for i in range(102)]
 s=sample();start=4*len(txs)
 offsets=[];cursor=start
 for tx in txs:
  offsets.append(cursor);cursor+=len(tx)
 body=b"".join(struct.pack("<I",x) for x in offsets)+b"".join(txs)
 s.extend(body)
 return s,txs

class Controls(unittest.TestCase):
 def test_valid_trie(self):
  s,txs=make();r=transactions(s)
  t=HexaryTrie(db={})
  for i,x in enumerate(txs):t[rlp.encode(i)]=x
  self.assertEqual(r["computed_transactions_root"],"0x"+t.root_hash.hex())
  self.assertEqual(r["transaction_count"],102)
 def test_reproducible(self):
  s,_=make();self.assertEqual(transactions(s),transactions(s))
 def test_count_mismatch(self):
  s,_=make([bytes([2,i]) for i in range(101)])
  with self.assertRaisesRegex(ValueError,"transaction_count_mismatch"):transactions(s)
 def test_offset_out_of_bounds(self):
  s,_=make();struct.pack_into("<I",s,BASE+508,999999)
  with self.assertRaisesRegex(ValueError,"transaction_list_offset"):transactions(s)
 def test_duplicate_rejected(self):
  s,_=make([b"same"]*102)
  with self.assertRaisesRegex(ValueError,"duplicate_transactions"):transactions(s)
 def test_empty_transaction_rejected(self):
  txs=[bytes([2,i]) for i in range(102)];txs[5]=b""
  s,_=make(txs)
  with self.assertRaisesRegex(ValueError,"transaction_size"):transactions(s)
 def test_wrong_beacon_slot_rejected(self):
  s,_=make();struct.pack_into("<Q",s,100,6173990)
  with self.assertRaisesRegex(ValueError,"slot_mismatch"):transactions(s)

if __name__=="__main__":
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 if not result.wasSuccessful():raise SystemExit(1)
 print(json.dumps({"phase":"195-R","controls":result.testsRun,"status":"PASS"}))
