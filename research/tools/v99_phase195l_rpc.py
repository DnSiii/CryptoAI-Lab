import json,urllib.request
RPC={'drpc':'https://eth.drpc.org','publicnode':'https://ethereum-rpc.publicnode.com'}
def rpc(url,method,params):
 req=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':195,'method':method,'params':params}).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=25) as f: result=json.load(f)
 if 'error' in result:raise ValueError('rpc_error')
 return result['result']
