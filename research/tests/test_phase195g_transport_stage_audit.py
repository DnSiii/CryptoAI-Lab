"""Synthetic Phase195-G transport tests; no network, holdout or PnL."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
import urllib.error

path=Path(__file__).resolve().parents[1]/'tools'/'v99_phase195g_transport_stage_audit.py'
spec=importlib.util.spec_from_file_location('phase195g',path)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

class Response:
    def __init__(self,data): self.f=io.BytesIO(data)
    def __enter__(self): return self
    def __exit__(self,*a): self.f.close()
    def read(self,n): return self.f.read(n)

def fake(result=None,error=None,override=None):
    obj={'jsonrpc':'2.0','id':m.RPC_ID}
    if error is None: obj['result']=result
    else: obj['error']={'code':error,'message':'untrusted'}
    if override: obj.update(override)
    return lambda request,timeout: Response(json.dumps(obj).encode())

class Tests(unittest.TestCase):
    def test_chain_id(self):
        self.assertEqual(m.summarize('eth_chainId',m.rpc('https://invalid','eth_chainId',[],fake('0x1')))['status'],'CHAIN_ID_ONE')
    def test_http_status(self):
        def blocked(*a,**kw): raise urllib.error.HTTPError('url',403,'blocked',{},None)
        self.assertEqual(m.rpc('https://invalid','eth_chainId',[],blocked),{'status':'HTTP_ERROR','http_code':403})
    def test_rpc_method_error(self):
        self.assertEqual(m.rpc('https://invalid','eth_getBlockReceipts',[],fake(error=-32601))['rpc_code'],-32601)
    def test_wrong_id(self):
        self.assertEqual(m.rpc('https://invalid','eth_chainId',[],fake('0x1',override={'id':1}))['status'],'INVALID_RPC_ENVELOPE')
    def test_bool_id(self):
        self.assertEqual(m.rpc('https://invalid','eth_chainId',[],fake('0x1',override={'id':True}))['status'],'INVALID_RPC_ENVELOPE')
    def test_duplicate_key(self):
        opener=lambda req,timeout: Response(b'{"jsonrpc":"2.0","id":1957,"result":1,"result":2}')
        self.assertEqual(m.rpc('https://invalid','eth_chainId',[],opener)['status'],'INVALID_JSON')
    def test_response_bound(self):
        opener=lambda req,timeout: Response(b' '*(m.MAX_BYTES+1))
        self.assertEqual(m.rpc('https://invalid','eth_chainId',[],opener)['status'],'BOUNDED_RESPONSE_TOO_LARGE')
    def test_wrong_chain_short_circuit(self):
        calls=[]
        def f(e,method,params):
            calls.append(method)
            return {'status':'HTTP_200_RPC_RESULT','result':'0x38'}
        out=m.audit_operator('fake','https://invalid',f)
        self.assertEqual(calls,['eth_chainId'])
        self.assertIn('skipped',out)
    def test_fixed_train_firewall(self):
        block={'number':hex(m.HEIGHT),'timestamp':hex(m.TRAIN_END),'hash':'0x'+'aa'*32}
        self.assertEqual(m.summarize('eth_getBlockByNumber',{'status':'HTTP_200_RPC_RESULT','result':block})['status'],'OUT_OF_TRAIN_HEADER')
    def test_invalid_quantities(self):
        for v in ('0x01','0xA','0x+1','0x_1',' 0x1',1,True):
            with self.subTest(v=v),self.assertRaises(ValueError): m.qty(v)
    def test_all_methods_no_raw_bodies(self):
        def f(e,method,params):
            if method=='eth_chainId': return {'status':'HTTP_200_RPC_RESULT','result':'0x1'}
            if method=='eth_getBlockByNumber':
                return {'status':'HTTP_200_RPC_RESULT','result':{'number':hex(m.HEIGHT),'timestamp':hex(m.TRAIN_START+1),'hash':'0x'+'aa'*32}}
            return {'status':'HTTP_200_RPC_RESULT','result':[]}
        out=m.audit_operator('fake','https://invalid',f)
        self.assertEqual(len(out['stages']),6)
        self.assertNotIn('"result"',json.dumps(out))
        self.assertEqual(out['stages']['fixed_train_header']['train_timestamp'],True)

if __name__=='__main__': unittest.main(verbosity=2)
