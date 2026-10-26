#!/usr/bin/env python3
"""Read-only HJ frozen 2023-24 base ledger physical authorization diagnosis. No PnL output."""
from __future__ import annotations
import argparse,json
import numpy as np
import hj_30cell as engine
from cg_buffered_governor import buffered_safe

def stats(xs):
    if not xs:return None
    a=np.asarray(xs,dtype=float)
    return {"n":len(a),"min":float(a.min()),"p10":float(np.quantile(a,.1)),
            "median":float(np.median(a)),"p90":float(np.quantile(a,.9)),
            "mean":float(a.mean()),"max":float(a.max())}

def run():
    frames,manifest=engine.load_official()
    source=engine.bundle(frames[0],frames[1],frames[2],frames[3],
                         frames[5],frames[6],frames[4])
    risks=engine.prepare_risks(frames)
    original=engine.HEBufferedGovernor.trade
    rows=[]
    def capture(self,*args,**kwargs):
        was_new=bool(self.needs_authorization)
        requested=np.asarray(self.requested,dtype=float).copy()
        old=np.asarray(args[1],dtype=float)
        opening=np.asarray(args[3],dtype=float)
        fee=kwargs.get("fee_mode","base")
        cash,prev,down,up,f,priorq,exitq=(args[0],args[2],args[4],args[5],
                                          args[6],args[7],args[8])
        before=int(self.forced_ratchets)
        actual=original(self,*args,**kwargs)
        if was_new:
            fresh=engine.HEBufferedGovernor()
            fresh.signal_components(requested)
            zero=np.zeros(4)
            fresh_units=original(fresh,cash,zero,prev,opening,down,up,f,priorq,exitq,
                                 fee_mode=fee,funding_order=kwargs.get("funding_order","carried_before_fill"))
            asked=float(np.sum(np.abs(requested*opening)))
            approved=float(np.sum(np.abs(actual*opening)))
            fresh_gross=float(np.sum(np.abs(fresh_units*opening)))
            old_gross=float(np.sum(np.abs(old*opening)))
            old_safe=buffered_safe(cash,old,prev,opening,old,down,up,f,exitq,
                                   fee,"carried_before_fill")
            rows.append({"asked":asked,"approved":approved,"fresh":fresh_gross,
                         "old_gross":old_gross,"old_safe":bool(old_safe),
                         "ratchet_delta":int(self.forced_ratchets)-before})
        return actual
    engine.HEBufferedGovernor.trade=capture
    try:
        result=engine.cell("HJ_full","immediate","base","carried_before_fill",
                           frames,risks,source)
    finally:
        engine.HEBufferedGovernor.trade=original
    if not result.get("passed") or not rows:
        raise ValueError("READ_ONLY_HJ_FROZEN_REPLAY_NOT_SURVIVED")
    valid=[x for x in rows if x["asked"]>1e-10]
    if len(valid)!=len(rows):
        raise ValueError("UNEXPECTED_ZERO_REQUEST")
    out={"audit":"V98_FROZEN_HJ_READ_ONLY_CARRIED_INVENTORY",
         "historical_training_only":True,"validation_2025_read":False,
         "external_benchmarks_used":False,"trading_authorized":False,
         "strategy_modified":False,"pnl_reported":False,
         "epoch_authorizations":len(rows),
         "actual_requested_fraction":stats([x["approved"]/x["asked"] for x in valid]),
         "fresh_requested_fraction":stats([x["fresh"]/x["asked"] for x in valid]),
         "actual_vs_fresh_fraction":stats([x["approved"]/x["fresh"] for x in valid if x["fresh"]>1e-10]),
         "old_inventory_gross_usd":stats([x["old_gross"] for x in rows]),
         "old_inventory_unsafe_at_refresh":sum(not x["old_safe"] for x in rows),
         "forced_ratchets_at_refresh":sum(x["ratchet_delta"] for x in rows),
         "decision":"PASS_READ_ONLY_CARRIED_INVENTORY_DIAGNOSTIC_NO_PNL"}
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True);a=p.parse_args()
    out=run()
    with open(a.output,"w") as f:json.dump(out,f,indent=2,sort_keys=True,allow_nan=False)
    print("V98_CARRIED_INVENTORY",json.dumps(out,sort_keys=True))
