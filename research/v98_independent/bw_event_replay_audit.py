#!/usr/bin/env python3
"""BW independent hourly source/event-level accounting and 81-corner replay.

Uses BW only to obtain submitted units and source/decision stream. All cashflow,
signed native funding, and intrabar margin identities are independently
reconstructed from raw pinned arrays, not copied from the settlement function.
Training-only; does not access 2025 or external engines.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math
from pathlib import Path
import numpy as np
import bw_90cell as engine

CORNERS=np.array(list(itertools.product(range(3),repeat=4)),dtype=int)
FEES={"base":(.0005,.0005),"severe":(.002,.003)}
ORDERS=("carried_before_fill","new_after_fill")
def near(a,b):
    return math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-7)
def replay():
    frames,manifest=engine.load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    assert len(c)==18288 and c.shape==(18288,4)
    assert int(e.sum())==9144 and np.array_equal(np.flatnonzero(e[:,0]),np.arange(0,18288,8))
    assert all(np.array_equal(np.flatnonzero(e[:,j]),np.arange(0,18288,8)) for j in range(4))
    sources=engine.source_bundle(c,q,r,e)
    decisions=engine.preregistered_decisions("BW_full",frames,sources)
    risks=engine.prepare_risk(frames)
    old_settle=engine.settle_hour
    results=[]
    for fee,order in itertools.product(FEES,ORDERS):
        count=0;native_events=0;exposed_events=0;funding_total=0.
        fee_total=0.;slip_total=0.;turn_total=0.
        minimum_intrabar_headroom=float("inf")
        digest=hashlib.sha256()
        def checked(previous,old,prev_close,opening,high,low,closing,target,
                    rate,event,mark_low,mark_high,fee_mode, funding_order):
            nonlocal count,native_events,exposed_events,funding_total
            nonlocal fee_total,slip_total,turn_total,minimum_intrabar_headroom
            assert fee_mode==fee and funding_order==order
            t=engine.START_EXECUTION+count
            assert t<engine.HOURS
            for provided,expected in ((opening,o[t]),(high,h[t]),(low,l[t]),
                (closing,c[t]),(rate,r[t]),(event,e[t]),
                (mark_low,ml[t]),(mark_high,mh[t])):
                if not np.array_equal(np.asarray(provided),expected):
                    raise ValueError("BW_EVENT_SOURCE_MISMATCH_T"+str(t))
            old=np.asarray(old,dtype=float);target=np.asarray(target,dtype=float)
            p=np.asarray(opening,dtype=float)
            gap=float(np.dot(old,p-prev_close))
            turnover=float(np.sum(np.abs(target-old)*p))
            fees=FEES[fee][0]*turnover
            slip=FEES[fee][1]*turnover
            payer=old if order=="carried_before_fill" else target
            obligations=payer*rate*event
            marks=np.where(obligations>=0,mark_high,mark_low)
            funding=-float(np.sum(obligations*marks))
            cash_open=float(previous)+gap+funding-fees-slip
            pnl=float(np.dot(target,closing-p))
            expected_close=cash_open+pnl
            if not cash_open>0 or not expected_close>0:
                raise ValueError("BW_EVENT_LEDGER_INSOLVENCY_T"+str(t))
            # All 81 low/open/high corners independently generated here.
            prices=np.stack((low,p,high))[CORNERS,np.arange(4)]
            corner_cash=cash_open+(prices-p)@target
            maintenance=.18*np.sum(np.abs(target)*prices,axis=1)
            headroom=np.min(corner_cash-np.maximum(maintenance,.35*float(previous)))
            minimum_intrabar_headroom=min(minimum_intrabar_headroom,float(headroom))
            if headroom< -1e-7:
                raise ValueError("BW_EVENT_INTRABAR_VIOLATION_T"+str(t))
            out=old_settle(previous,old,prev_close,opening,high,low,closing,target,
                           rate,event,mark_low,mark_high,
                           fee_mode=fee_mode,funding_order=funding_order)
            for key,value in (("gap_pnl",gap),("intrabar_pnl",pnl),
                              ("funding",funding),("turnover",turnover),
                              ("fees",fees),("slippage",slip),
                              ("cash",expected_close)):
                if not near(out[key],value):
                    raise ValueError("BW_EVENT_REPLAY_"+key+"_T"+str(t))
            if not np.array_equal(out["units"],target):
                raise ValueError("BW_EVENT_UNITS_T"+str(t))
            count+=1
            native_events+=int(np.count_nonzero(event))
            exposed_events+=int(np.count_nonzero(obligations))
            funding_total+=funding
            fee_total+=fees;slip_total+=slip;turn_total+=turnover
            digest.update(np.asarray([t,previous,gap,turnover,fees,slip,
                funding,pnl,expected_close,headroom],dtype="<f8").tobytes())
            return out
        engine.settle_hour=checked
        try:
            receipt=engine.cell("BW_full","immediate",fee,order,frames,risks,decisions)
            if count!=engine.HOURS-engine.START_EXECUTION:
                raise ValueError("BW_EVENT_INCOMPLETE_HOURS")
            for key,expected in (("fees",fee_total),("slippage",slip_total),
                                 ("funding",funding_total),("turnover",turn_total)):
                if not near(receipt[key],expected):
                    raise ValueError("BW_EVENT_AGGREGATE_"+key)
            results.append({"fee":fee,"order":order,"hours_replayed":count,
                "native_source_events_replayed":native_events,
                "nonzero_inventory_funding_events":exposed_events,
                "funding_cashflow":funding_total,"fees":fee_total,
                "slippage":slip_total,"turnover":turn_total,
                "min_81_corner_headroom":minimum_intrabar_headroom,
                "final_nav":receipt["final_nav"],"ledger_sha256":digest.hexdigest(),
                "passed":True})
        finally:
            engine.settle_hour=old_settle
    return {"architecture":"BW","training_only":True,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "raw_native_events":int(e.sum()),
            "source_manifest_sha256":hashlib.sha256(json.dumps(manifest,
                sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            "cases":results,
            "independent_funding_events_rederived":True,
            "independent_81_corner_replay":True,
            "decision":"PASS_BW_EVENT_LEDGER_ACCOUNTING_ONLY_NOT_ECONOMIC"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    a=p.parse_args();result=replay()
    Path(a.output).write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))
    print("BW_EVENT_LEDGER",result["decision"],
          [(x["fee"],x["order"],x["hours_replayed"],x["native_source_events_replayed"])
           for x in result["cases"]])
