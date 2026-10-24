#!/usr/bin/env python3
"""BV frozen post-rejection per-asset funding/friction attribution; diagnostic only.

Uses original BV source and physical ledger; no signal, threshold, or budget changes.
Recomputes native per-asset cashflow from the pinned source, compares against
original BV settlement totals, never opens 2025 or external benchmark engines.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
import bv_90cell as eng
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
KEYS=("funding","fees","slippage","turnover","gap_pnl","intrabar_pnl","gross_notional_hours")
def run():
    frames,manifest=eng.load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    assert c.shape==(18288,4) and int(e.sum())==9144
    sources=eng.source_bundle(c,q,r,e)
    risks=eng.prepare_risk(frames)
    results=[]
    for path in ("BV_full","BV_core_only"):
        decisions=eng.preregistered_decisions(path,frames,sources)
        for fee in ("base","severe"):
            order="carried_before_fill"
            sums={yr:{key:np.zeros(4) for key in KEYS} for yr in ("2023","2024")}
            original=eng.settle_hour
            count=0
            def audited(previous,old,prev_close,opening,high,low,closing,target,
                        rate,event,mark_low,mark_high,fee_mode,funding_order):
                nonlocal count
                t=eng.START_EXECUTION+count
                year="2023" if t<eng.FIRST_2024 else "2024"
                a=sums[year]
                old=np.asarray(old);target=np.asarray(target)
                opening=np.asarray(opening);closing=np.asarray(closing)
                delta=np.abs(target-old)*opening
                payer=old if funding_order=="carried_before_fill" else target
                marks=np.where(payer*rate*event>=0,mark_high,mark_low)
                a["funding"][:]-=payer*rate*event*marks
                friction=eng.FEES[fee_mode]
                a["fees"][:]+=delta*friction[0]
                a["slippage"][:]+=delta*friction[1]
                a["turnover"][:]+=delta
                a["gap_pnl"][:]+=old*(opening-prev_close)
                a["intrabar_pnl"][:]+=target*(closing-opening)
                a["gross_notional_hours"][:]+=np.abs(target*closing)
                count+=1
                return original(previous,old,prev_close,opening,high,low,closing,
                                target,rate,event,mark_low,mark_high,fee_mode,funding_order)
            eng.settle_hour=audited
            try:
                receipt=eng.cell(path,"immediate",fee,order,frames,risks,decisions)
            finally:
                eng.settle_hour=original
            assert count==eng.HOURS-eng.START_EXECUTION
            totals={key:sum(float(sums[y][key].sum()) for y in sums) for key in KEYS}
            for key in ("funding","fees","slippage","turnover"):
                if not math.isclose(totals[key],float(receipt[key]),rel_tol=1e-9,abs_tol=1e-6):
                    raise ValueError("BV_ATTRIBUTION_MISMATCH_"+key)
            yearly={year:{asset:{key:float(sums[year][key][j]) for key in KEYS}
                          for j,asset in enumerate(ASSETS)} for year in sums}
            results.append({"path":path,"fee":fee,"order":order,
                            "hours":count,"totals":totals,
                            "years":yearly,"final_nav":receipt["final_nav"],
                            "two_year_cagr":receipt["two_year_cagr"],
                            "passed":True})
    return {"architecture":"BV","post_rejection_diagnostic_only":True,
            "training_only":True,"validation_2025_read":False,
            "source_native_events":int(e.sum()),"cases":results,
            "decision":"PASS_BV_FROZEN_COST_ATTRIBUTION_NO_REFIT"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    a=p.parse_args()
    result=run()
    Path(a.output).write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))
    for x in result["cases"]:
        print("BV_COST_ATTRIBUTION",x["path"],x["fee"],
              "funding",round(x["totals"]["funding"],4),
              "fees",round(x["totals"]["fees"],4),
              "slippage",round(x["totals"]["slippage"],4),
              "funding_by_asset",
              {a:round(sum(x["years"][y][a]["funding"] for y in x["years"]),4) for a in ASSETS})
    print(result["decision"])
