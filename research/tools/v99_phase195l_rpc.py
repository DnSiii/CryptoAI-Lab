"""Phase195-L RPC transport with method-level HTTP attribution; no credentials."""
import json,urllib.request,urllib.error
def rpc(url,method,params):
 req=urllib.request.Request(url,data=json.dumps({"jsonrpc":"2.0","id":195,
  "method":method,"params":params}).encode(),headers={"Content-Type":"application/json",
  "User-Agent":"CryptoAI-Lab-Phase195L/1"})
 try:
  with urllib.request.urlopen(req,timeout=35) as f: response=json.load(f)
 except urllib.error.HTTPError as exc:
  raise ValueError("rpc_http_"+str(exc.code)+":"+method+":"+url.split("/")[2]) from exc
 except (urllib.error.URLError,TimeoutError) as exc:
  raise ValueError("rpc_transport:"+method+":"+url.split("/")[2]) from exc
 if not isinstance(response,dict) or response.get("jsonrpc")!="2.0" or response.get("id")!=195:
  raise ValueError("rpc_invalid_envelope:"+method)
 if "error" in response or "result" not in response:
  raise ValueError("rpc_error:"+method+":"+url.split("/")[2])
 return response["result"]
