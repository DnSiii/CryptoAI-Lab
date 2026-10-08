"""Phase195-H synthetic tests: no live RPC, prices, PnL or holdout."""
import copy
import importlib.util
import pathlib
import sys
import unittest

tools_dir=pathlib.Path(__file__).resolve().parents[1]/'tools'
sys.path.insert(0,str(tools_dir))
path=tools_dir/'v99_phase195h_crosssource_receipt_structure.py'
spec=importlib.util.spec_from_file_location('phase195h',path)
h=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=h
spec.loader.exec_module(h)
g=h.g
TX='0x'+'12'*32;BH='0x'+'34'*32;ROOT='0x'+'56'*32
base={'number':hex(g.HEIGHT),'timestamp':hex(g.TRAIN_START+12),'hash':BH,
      'parentHash':'0x'+'78'*32,'receiptsRoot':ROOT,'transactionsRoot':'0x'+'ab'*32,
      'transactions':[TX],'gasUsed':'0x5208','logsBloom':'0x'+'00'*256}
rec={'transactionIndex':'0x0','transactionHash':TX,'blockHash':BH,'blockNumber':hex(g.HEIGHT),
     'cumulativeGasUsed':'0x5208','status':'0x1','logs':[]}
logs={topic:[] for topic in g.TOPICS.values()}

class Tests(unittest.TestCase):
    def test_synthetic_valid(self):
        r=h.validate(base,copy.deepcopy(base),[rec],logs)
        self.assertEqual(r['receipt_count'],1)
        self.assertFalse(r['receipts_root_recomputed'])
        self.assertFalse(r['promotion_authorized'])
    def test_header_disagreement(self):
        b=copy.deepcopy(base);b['receiptsRoot']='0x'+'ff'*32
        with self.assertRaisesRegex(ValueError,'cross_source_header_disagreement'):
            h.validate(base,b,[rec],logs)
    def test_missing_receipt(self):
        with self.assertRaisesRegex(ValueError,'receipt_cardinality'):
            h.validate(base,base,[],logs)
    def test_wrong_receipt_tx(self):
        bad=copy.deepcopy(rec);bad['transactionHash']='0x'+'cc'*32
        with self.assertRaisesRegex(ValueError,'receipt_order'):
            h.validate(base,base,[bad],logs)
    def test_wrong_gas(self):
        bad=copy.deepcopy(rec);bad['cumulativeGasUsed']='0x5209'
        with self.assertRaisesRegex(ValueError,'block_gas_used_mismatch'):
            h.validate(base,base,[bad],logs)
    def test_missing_logs_query(self):
        with self.assertRaisesRegex(ValueError,'missing_eth_getLogs'):
            h.validate(base,base,[rec],{})
    def test_out_of_train(self):
        bad=copy.deepcopy(base);bad['timestamp']=hex(g.TRAIN_END)
        with self.assertRaisesRegex(ValueError,'train_firewall'):
            h.validate(bad,bad,[rec],logs)
    def test_duplicate_tx(self):
        bad=copy.deepcopy(base);bad['transactions']=[TX,TX]
        with self.assertRaisesRegex(ValueError,'duplicate_tx'):
            h.validate(bad,bad,[rec,rec],logs)

if __name__=='__main__': unittest.main(verbosity=2)
