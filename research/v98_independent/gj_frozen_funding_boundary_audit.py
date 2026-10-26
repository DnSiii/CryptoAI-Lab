#!/usr/bin/env python3
"""GJ frozen path: funding-boundary turnover and immediate funding-order delta.
Observational wrapper only; rejected GJ candidate remains byte-identical.
"""
from __future__ import annotations
import argparse,json,math
import numpy as np
import gj_30cell as engine
from phase1246_ai_two_stage_margin import signed_funding

def run():
    original=engine.settle_hour
    stats={}
    def observe(*args,**kwargs):
        fee=kwargs.get("fee_mode","base")
        order=kwargs.get("funding_order","carried_before_fill")
        key=fee+"|"+order
        s=stats.setdefault(key,{"funding_event_hours":0,"funding_event_trade_hours":0,
            "event_trade_notional":0.,"same_trajectory_new_minus_carried_funding":0.,
            "max_abs_event_funding_order_delta":0.,"all_trade_hours":0})
        old=np.asarray(args[1],dtype=float)
        opening=np.asarray(args[3],dtype=float)
        target=np.asarray(args[7],dtype=float)
        rate=np.asarray(args[8],dtype=float)
        event=np.asarray(args[9],dtype=float)
        low=np.asarray(args[10],dtype=float)
        high=np.asarray(args[11],dtype=float)
        turnover=float(np.sum(np.abs(target-old)*opening))
        s["all_trade_hours"]+=int(turnover>1e-5)
        if np.any(event):
            s["funding_event_hours"]+=1
            if turnover>1e-5:
                s["funding_event_trade_hours"]+=1
                s["event_trade_notional"]+=turnover
                delta=(signed_funding(target,rate,event,low,high)-
                       signed_funding(old,rate,event,low,high))
                s["same_trajectory_new_minus_carried_funding"]+=delta
                s["max_abs_event_funding_order_delta"]=max(
                    s["max_abs_event_funding_order_delta"],abs(delta))
        return original(*args,**kwargs)
    engine.settle_hour=observe
    try:
        result=engine.run("GJ_full")
    finally:
        engine.settle_hour=original
    if len(result["cells"])!=6 or not all(c["passed"] for c in result["cells"]):
        raise ValueError("GJ_FROZEN_REPLAY_INVALID")
    return {"architecture":"GJ","path":"GJ_full","training_only":True,
            "validation_2025_read":False,"trading_authorized":False,
            "candidate_modified":False,
            "source_manifest_sha256":result["source_manifest_sha256"],
            "funding_boundary":stats,
            "decision":"PASS_GJ_FROZEN_FUNDING_BOUNDARY_OBSERVATION_ONLY"}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    a=p.parse_args();r=run()
    with open(a.output,"w") as f:json.dump(r,f,sort_keys=True,indent=2)
    for k,v in sorted(r["funding_boundary"].items()):
        print("GJ_FUNDING_BOUNDARY",k,json.dumps(v,sort_keys=True))
    print(r["decision"])
