#!/usr/bin/env python3
"""JF independent EVERY-SETTLED-HOUR native ledger oracle replay, no engine changes.
Patches only settlement receipt observation, newer source/governor/execution decisions.
Historical TRAINING ONLY. No 2025/benchmarks/Frozen/paper/live access.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
import numpy as np
import jf_30cell as engine
from v98_independent_settlement_oracle import verify_hour,static_check
PATIC=engine.PATIC
def run(path):
    assert static_check()
    original=engine.settle_hour
    totals={"settled_hours":0,"funding_event_hours":0,"trade_hours":0,
            "verified_turnover":0.,"verified_funding":0.}
    digest=hashlib.sha256()
    def independently_checked(*args,**kwargs):
        receipt=original(*args,**kwargs)
        check=verify_hour(*args,fee_mode=kwargs.get("fee_mode","base"),
                          funding_order=kwargs.get("funding_order","carried_before_fill"),
                          receipt=receipt)
        totals["settled_hours"]+=1
        totals["funding_event_hours"]+=int(np.any(np.asarray(args[9])>0))
        totals["trade_hours"]+=int(check["turnover"]>1e-5)
        totals["verified_turnover"]+=check["turnover"]
        totals["verified_funding"]+=check["funding"]
        digest.update(struct.pack("<4d",check["cash"],check["gross"],
                                  check["turnover"],check["funding"]))
        return receipt
    engine.settle_hour=independently_checked
    try:
        result=engine.run(path)
    finally:
        engine.settle_hour=original
    if len(result["cells"])!=6 or not all(x["passed"] for x in result["cells"]):
        raise ValueError("JF_ORACLE_PHYSICAL_CELL_FAILURE")
    if totals["settled_hours"]<=0 or totals["funding_event_hours"]<=0:
        raise ValueError("JF_ORACLE_INCOMPLETE_LEDGER")
    return {"architecture":"JF","path":path,"training_only":True,
            "validation_2025_read":False,"trading_authorized":False,
            "source_manifest_sha256":result["source_manifest_sha256"],
            "ledger_oracle":"independent_each_settled_hour",
            "oracle":{**totals,"sha256":digest.hexdigest()},
            "physical_cells":result["cells"],
            "decision":"PASS_JF_INDEPENDENT_LEDGER_ONLY_NOT_ECONOMIC"}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--path",required=True,choices=PATIC)
    p.add_argument("--output",required=True)
    a=p.parse_args();out=run(a.path)
    with open(a.output,"w") as f:json.dump(out,f,indent=2,sort_keys=True,allow_nan=False)
    print("JF_INDEPENDENT_LEDGER",a.path,out["decision"],
          out["oracle"]["settled_hours"],"hours",
          out["oracle"]["funding_event_hours"],"funding-hours")
