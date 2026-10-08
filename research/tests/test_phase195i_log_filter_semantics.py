"""Phase195-I synthetic adversarial tests. No prices, holdout, or PnL."""
import copy
import importlib.util
import pathlib
import sys
import unittest

p=pathlib.Path(__file__).resolve().parents[1]/"tools"/"v99_phase195i_log_filter_semantics.py"
sys.path.insert(0,str(p.parent))
spec=importlib.util.spec_from_file_location("phase195i",p)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)
g=m.g
BH="0x"+"ab"*32
TX="0x"+"cd"*32
def row():
    return dict(blockHash=BH,blockNumber=hex(g.HEIGHT),address=g.USDC,
                topics=[g.TOPICS["mint"]],removed=False,logIndex="0x0",
                transactionIndex="0x0",transactionHash=TX,data="0x")
def answer(rows):return {"status":"HTTP_200_RPC_RESULT","result":rows}
def fake(endpoint,method,params):
    if method=="eth_chainId":return answer("0x1")
    if method=="eth_getBlockByNumber":
        return answer(dict(number=hex(g.HEIGHT),timestamp=hex(g.TRAIN_START+1),hash=BH))
    return answer([])
class Tests(unittest.TestCase):
    def test_valid_empty(self):
        x=m.summarize_logs(answer([]),BH,g.TOPICS["mint"])
        self.assertEqual(x["count"],0)
        self.assertEqual(x["status"],"PROVISIONAL_UNVERIFIED_LOG_TRANSPORT")
    def test_valid_one(self):
        x=m.summarize_logs(answer([row()]),BH,g.TOPICS["mint"])
        self.assertEqual(x["count"],1)
    def test_deterministic_order(self):
        a=row();b=row();b["logIndex"]="0x1";b["data"]="0x00"
        self.assertEqual(m.summarize_logs(answer([a,b]),BH,g.TOPICS["mint"])["digest"],
                         m.summarize_logs(answer([b,a]),BH,g.TOPICS["mint"])["digest"])
    def test_duplicate_index(self):
        self.assertEqual(m.summarize_logs(answer([row(),row()]),BH,g.TOPICS["mint"])["status"],"INVALID_LOG_ROW")
    def test_wrong_block_hash(self):
        a=row();a["blockHash"]="0x"+"ef"*32
        self.assertEqual(m.summarize_logs(answer([a]),BH,g.TOPICS["mint"])["status"],"INVALID_LOG_ROW")
    def test_removed_log(self):
        a=row();a["removed"]=True
        self.assertEqual(m.summarize_logs(answer([a]),BH,g.TOPICS["mint"])["status"],"INVALID_LOG_ROW")
    def test_malformed_hex_data(self):
        a=row();a["data"]="0xz1"
        self.assertEqual(m.summarize_logs(answer([a]),BH,g.TOPICS["mint"])["status"],"INVALID_LOG_ROW")
    def test_malformed_topic(self):
        a=row();a["topics"]=["0x1"]
        self.assertEqual(m.summarize_logs(answer([a]),BH,g.TOPICS["mint"])["status"],"INVALID_LOG_ROW")
    def test_noncanonical_log_index(self):
        a=row();a["logIndex"]="0x00"
        self.assertEqual(m.summarize_logs(answer([a]),BH,g.TOPICS["mint"])["status"],"INVALID_LOG_ROW")
    def test_wrong_tx_index_type(self):
        a=row();a["transactionIndex"]=0
        self.assertEqual(m.summarize_logs(answer([a]),BH,g.TOPICS["mint"])["status"],"INVALID_LOG_ROW")
    def test_http_error_preserved(self):
        self.assertEqual(m.summarize_logs({"status":"HTTP_ERROR","http_code":400},BH,g.TOPICS["mint"]),
                         {"status":"HTTP_ERROR","http_code":400})
    def test_all_modes_are_hold(self):
        r=m.run(fake)
        self.assertEqual(r["decision"],"HOLD_LOG_TRANSPORT_DIAGNOSTIC_ONLY")
        self.assertTrue(r["parity"]["mint"]["same_log_digest_if_available"])
        self.assertFalse(r["promotion_authorized"])
        self.assertFalse(r["receipt_root_proven"])
    def test_http_400_mode_fail_closed(self):
        def f(endpoint,method,params):
            if method=="eth_getLogs" and "blockHash" in params[0]:
                return {"status":"HTTP_ERROR","http_code":400}
            return fake(endpoint,method,params)
        r=m.run(f)
        self.assertFalse(r["parity"]["mint"]["all_four_transports_available"])
        self.assertFalse(r["promotion_authorized"])
    def test_cross_source_digest_disagreement(self):
        def f(endpoint,method,params):
            if method=="eth_getLogs" and "drpc" in endpoint and params[0]["topics"][0]==g.TOPICS["mint"]:
                return answer([row()])
            return fake(endpoint,method,params)
        r=m.run(f)
        self.assertFalse(r["parity"]["mint"]["same_log_digest_if_available"])
        self.assertFalse(r["promotion_authorized"])
    def test_cross_source_header_disagreement(self):
        def f(endpoint,method,params):
            if method=="eth_getBlockByNumber" and "drpc" in endpoint:
                h=fake(endpoint,method,params)
                h["result"]["hash"]="0x"+"ef"*32
                return h
            return fake(endpoint,method,params)
        self.assertEqual(m.run(f)["decision"],"HOLD_HEADER_DISAGREEMENT")
    def test_out_of_train(self):
        def f(endpoint,method,params):
            if method=="eth_getBlockByNumber":
                h=fake(endpoint,method,params)
                h["result"]["timestamp"]=hex(g.TRAIN_END)
                return h
            return fake(endpoint,method,params)
        self.assertEqual(m.run(f)["decision"],"HOLD_TRAIN_FIREWALL")
if __name__=="__main__":unittest.main(verbosity=2)
