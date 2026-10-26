#!/usr/bin/env python3
"""Read-only frozen GQ signed-futures exposure diagnostic; no strategy/gate changes, no 2025."""
import json
import numpy as np
import gq_30cell as engine

def run():
    original=engine.settle_hour
    observed={}
    def capture(*args,**kwargs):
        receipt=original(*args,**kwargs)
        key=kwargs.get("fee_mode","base")+"|"+kwargs.get("funding_order","carried_before_fill")
        d=observed.setdefault(key,{"settled_hours":0,"actual_short_hours":0,
                                    "max_actual_short_usd":0.,"max_gross_minus_abs_net_usd":0.,
                                    "actual_short_notional_hour_sum":0.})
        units=np.asarray(receipt["units"],dtype=float)
        price=np.asarray(args[6],dtype=float)
        short=float(np.sum(np.maximum(-units,0.)*price))
        gross=float(np.sum(np.abs(units*price)))
        net=abs(float(np.sum(units*price)))
        d["settled_hours"]+=1
        d["actual_short_hours"]+=int(short>1e-6)
        d["max_actual_short_usd"]=max(d["max_actual_short_usd"],short)
        d["max_gross_minus_abs_net_usd"]=max(d["max_gross_minus_abs_net_usd"],gross-net)
        d["actual_short_notional_hour_sum"]+=short
        return receipt
    engine.settle_hour=capture
    try:result=engine.run("GQ_full")
    finally:engine.settle_hour=original
    if len(result["cells"])!=6 or not all(x["passed"] for x in result["cells"]):
        raise ValueError("GQ_FROZEN_DIAGNOSTIC_PHYSICAL_REPLAY_FAILED")
    return {"architecture":"GQ","training_only":True,"strategy_modified":False,
            "validation_2025_read":False,"trading_authorized":False,
            "source_manifest_sha256":result["source_manifest_sha256"],
            "decision":"GQ_FROZEN_SIGNED_EXPOSURE_OBSERVED_ONLY",
            "actual_signed_exposure":observed}

if __name__=="__main__":
    output=run()
    with open("gq_frozen_short_exposure.json","w") as f:json.dump(output,f,indent=2,sort_keys=True)
    print("GQ_FROZEN_SHORT_DIAGNOSTIC",json.dumps(output["actual_signed_exposure"],sort_keys=True))
