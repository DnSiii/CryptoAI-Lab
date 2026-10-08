import copy,importlib.util,pathlib,sys,unittest
p=pathlib.Path(__file__).resolve().parents[1]/"tools"/"v99_phase195j_receipt_payload_parity.py"
sys.path.insert(0,str(p.parent))
spec=importlib.util.spec_from_file_location("j",p)
j=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=j
spec.loader.exec_module(j)
g=j.g
txs=["0x"+(i+1).to_bytes(32,"big").hex() for i in range(102)]
h={"number":hex(g.HEIGHT),"timestamp":hex(g.TRAIN_START+1),"hash":"0x"+"ab"*32,
   "receiptsRoot":"0x"+"bc"*32,"transactionsRoot":"0x"+"cd"*32,
   "gasUsed":hex(102),"logsBloom":"0x"+"00"*256,"transactions":txs}
recs=[{"transactionIndex":hex(i),"transactionHash":tx,"blockHash":h["hash"],
       "blockNumber":hex(g.HEIGHT),"cumulativeGasUsed":hex(i+1),
       "status":"0x1","type":"0x2","logsBloom":h["logsBloom"],"logs":[]}
      for i,tx in enumerate(txs)]
def reply(x):return {"status":"HTTP_200_RPC_RESULT","result":copy.deepcopy(x)}
def fake(endpoint,method,params):
    if method=="eth_chainId":return reply("0x1")
    if method=="eth_getBlockByNumber":return reply(h)
    if method=="eth_getBlockReceipts":return reply(recs)
    if method=="eth_getTransactionReceipt":return reply(recs[txs.index(params[0])])
    raise AssertionError(method)
class Tests(unittest.TestCase):
    def test_complete_102_receipts(self):
        x=j.run(fake)
        self.assertTrue(x["cross_operator_payload_parity"])
        self.assertTrue(x["same_operator_transport_parity"])
        self.assertEqual(x["drpc_bulk"]["receipt_count"],102)
        self.assertFalse(x["promotion_authorized"])
    def test_missing_individual_receipt(self):
        def f(endpoint,method,params):
            if method=="eth_getTransactionReceipt" and "publicnode" in endpoint and params[0]==txs[51]:
                return reply(None)
            return fake(endpoint,method,params)
        x=j.run(f)
        self.assertFalse(x["cross_operator_payload_parity"])
        self.assertTrue(x["same_operator_transport_parity"])
    def test_incomplete_bulk(self):
        def f(endpoint,method,params):
            if method=="eth_getBlockReceipts":return reply(recs[:-1])
            return fake(endpoint,method,params)
        self.assertEqual(j.run(f)["decision"],"HOLD_RECEIPT_TRANSPORT_OR_STRUCTURE")
    def test_wrong_chain(self):
        def f(endpoint,method,params):
            if method=="eth_chainId" and "publicnode" in endpoint:return reply("0x2")
            return fake(endpoint,method,params)
        self.assertEqual(j.run(f)["decision"],"HOLD_WRONG_CHAIN")
    def test_noncanonical_quantity(self):
        x=copy.deepcopy(recs);x[0]["cumulativeGasUsed"]="0x01"
        with self.assertRaises(ValueError):j.normalized(h,x)
if __name__=="__main__":unittest.main(verbosity=2)
