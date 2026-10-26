#!/usr/bin/env python3
"""GY read-only requested-vs-physically-authorized long exposure audit, TRAINING only."""
import json
import numpy as np
import gy_30cell as engine

def run():
    original_trade=engine.GYBufferedGovernor.trade
    original_settle=engine.settle_hour
    authorization={}
    settled={}
    def capture_trade(self,*args,**kwargs):
        key=kwargs.get("fee_mode","base")+"|"+kwargs.get("funding_order","carried_before_fill")
        d=authorization.setdefault(key,{"epoch_authorizations":0,
            "requested_gross_usd_sum":0.,"authorized_gross_usd_sum":0.,
            "min_authorized_fraction":1.,"epochs_under_25pct":0,
            "max_requested_gross_usd":0.,"max_authorized_gross_usd":0.})
        was_new=bool(self.needs_authorization)
        price=np.asarray(args[3],dtype=float)
        request=np.asarray(self.requested,dtype=float).copy()
        target=original_trade(self,*args,**kwargs)
        if was_new:
            asked=float(np.sum(np.abs(request*price)))
            approved=float(np.sum(np.abs(np.asarray(target)*price)))
            fraction=min(1.,approved/max(asked,1e-12))
            d["epoch_authorizations"]+=1
            d["requested_gross_usd_sum"]+=asked
            d["authorized_gross_usd_sum"]+=approved
            d["min_authorized_fraction"]=min(d["min_authorized_fraction"],fraction)
            d["epochs_under_25pct"]+=int(fraction<.25)
            d["max_requested_gross_usd"]=max(d["max_requested_gross_usd"],asked)
            d["max_authorized_gross_usd"]=max(d["max_authorized_gross_usd"],approved)
        return target
    def capture_settle(*args,**kwargs):
        receipt=original_settle(*args,**kwargs)
        key=kwargs.get("fee_mode","base")+"|"+kwargs.get("funding_order","carried_before_fill")
        d=settled.setdefault(key,{"hours":0,"gross_notional_hour_sum":0.,
            "max_gross_usd":0.,"short_position_hours":0})
        units=np.asarray(receipt["units"],dtype=float)
        price=np.asarray(args[6],dtype=float)
        gross=float(np.sum(np.abs(units*price)))
        d["hours"]+=1
        d["gross_notional_hour_sum"]+=gross
        d["max_gross_usd"]=max(d["max_gross_usd"],gross)
        d["short_position_hours"]+=int(np.any(units< -1e-10))
        return receipt
    engine.GYBufferedGovernor.trade=capture_trade
    engine.settle_hour=capture_settle
    try:result=engine.run("GY_full")
    finally:
        engine.GYBufferedGovernor.trade=original_trade
        engine.settle_hour=original_settle
    if len(result["cells"])!=6 or not all(x["passed"] for x in result["cells"]):
        raise ValueError("GY_PHYSICAL_AUDIT_REPLAY_FAILED")
    if any(v["short_position_hours"] for v in settled.values()):
        raise ValueError("GY_LONG_ONLY_VIOLATED")
    return {"architecture":"GY","training_only":True,"strategy_modified":False,
            "validation_2025_read":False,"trading_authorized":False,
            "source_manifest_sha256":result["source_manifest_sha256"],
            "requested_vs_authorized":authorization,
            "settled_actual":settled,
            "decision":"GY_READ_ONLY_PHYSICAL_EXPOSURE_OBSERVED"}
if __name__=="__main__":
    out=run()
    with open("gy_read_only_exposure.json","w") as f:
        json.dump(out,f,sort_keys=True,indent=2,allow_nan=False)
    print("GY_PHYSICAL_EXPOSURE",json.dumps(out["requested_vs_authorized"],sort_keys=True))
    print("GY_ACTUAL_EXPOSURE",json.dumps(out["settled_actual"],sort_keys=True))
