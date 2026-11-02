#!/usr/bin/env python3
"""V98 VX independent hourly cash, fill, funding and source oracle for exposed 2025.
Independent arithmetic; cannot establish account execution, edge or validation.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
import numpy as np
from vw_native_carry_physical import load as load_vw
from vx_spot_led_composed import ASSETS,HOURS

def replay_audit(ledger_path,data):
    with open(ledger_path,newline="") as f:
        reader=csv.DictReader(f);rows=list(reader)
    if len(rows)!=HOURS:raise ValueError("VX_ORACLE_HOURS")
    previous_spot=np.zeros(4);previous_perp=np.zeros(4)
    prev_spot_close=None;prev_perp_close=None;previous_equity=10000.
    previous_cash=10000.;mismatches=0;max_error=0.;turnover=0.
    for t,row in enumerate(rows):
        if int(row["hour"])!=t:raise ValueError("VX_ORACLE_HOUR_ORDER")
        get=lambda key:float(row[key])
        arr=lambda key:np.asarray(json.loads(row[key]),dtype=float)
        sq=arr("spot_qty");pq=arr("perp_qty")
        so=arr("spot_open");sc=arr("spot_close")
        po=arr("perp_open");pc=arr("perp_close")
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (sq,pq,so,sc,po,pc)):
            raise ValueError("VX_ORACLE_GEOMETRY")
        if np.any(sq< -1e-9) or np.any(pq>1e-9):raise ValueError("VX_ORACLE_SIDE")
        source_so=np.array([data[a][0][t][0] for a in ASSETS])
        source_sc=np.array([data[a][0][t][3] for a in ASSETS])
        source_po=np.array([data[a][1][t][0] for a in ASSETS])
        source_pc=np.array([data[a][1][t][3] for a in ASSETS])
        if any(np.max(np.abs(x-y))>1e-8 for x,y in ((so,source_so),(sc,source_sc),
                                                    (po,source_po),(pc,source_pc))):
            raise ValueError("VX_ORACLE_SOURCE_PRICE_CONFLICT")
        expected_spot_gap=float(previous_spot@(so-prev_spot_close)) if t else 0.
        expected_perp_gap=float(previous_perp@(po-prev_perp_close)) if t else 0.
        expected_trade_cash=float(-(sq-previous_spot)@so)
        expected_perp_pnl=float(pq@(pc-po))
        expected_cost=.0015*float(np.abs(sq-previous_spot)@so)+.0010*float(np.abs(pq-previous_perp)@po)
        expected_funding=0.
        if t%8==0:
            q=previous_perp
            # Ledger is base / carried-before-fill only.
            for j,a in enumerate(ASSETS):
                rate,lo,hi=data[a][2][t]
                expected_funding+=-q[j]*rate*(lo if rate>=0 else hi)
        expected_cash=previous_cash+expected_perp_gap+expected_trade_cash-expected_cost+expected_funding+expected_perp_pnl
        expected_equity=expected_cash+float(sq@sc)
        vals=((get("equity_before"),previous_equity),
              (get("cash_before"),previous_cash),
              (get("perp_gap"),expected_perp_gap),
              (get("spot_gap"),expected_spot_gap),
              (get("spot_trade_cash"),expected_trade_cash),
              (get("perp_intrahour_pnl"),expected_perp_pnl),
              (get("funding"),expected_funding),
              (get("cost"),expected_cost),
              (get("cash_after"),expected_cash),
              (get("equity_after"),expected_equity))
        for observed,expected in vals:
            err=abs(observed-expected);max_error=max(max_error,err)
            if err>max(1e-6,1e-10*max(abs(expected),1)):mismatches+=1
        previous_spot=sq;previous_perp=pq
        prev_spot_close=sc;prev_perp_close=pc
        previous_cash=expected_cash;previous_equity=expected_equity
        turnover+=float(np.abs(sq-previous_spot)@so) if False else 0.
    return {"decision":"PASS_INDEPENDENT_VX_HOURLY_ACCOUNTING_ONLY" if mismatches==0 else "FAIL_VX_ACCOUNTING",
            "hours":HOURS,"identities_checked":HOURS*10,
            "mismatches":mismatches,"max_absolute_error":max_error,
            "final_equity":previous_equity,
            "exact_marks_authenticated":False,"account_costs_authenticated":False,
            "economic_gate_passed":False,"paper_live_authorized":False}

def main():
    p=argparse.ArgumentParser()
    for key in ("spot-dir","nh-dir","ledger","receipt"):p.add_argument("--"+key,required=True)
    a=p.parse_args()
    data=load_vw(a.spot_dir,a.nh_dir)
    out=replay_audit(a.ledger,data)
    receipt=json.loads(Path(a.receipt).read_text())
    full=next((x for x in receipt["cells"] if x["book"]=="VX_full"
               and x["tier"]=="base" and x["order"]=="carried_before_fill"),None)
    if full is None or not full["passed"]:raise ValueError("VX_ORACLE_NO_PHYSICAL_FULL")
    if abs(out["final_equity"]-full["final_equity"])>1e-6:
        raise ValueError("VX_ORACLE_RECEIPT_MISMATCH")
    print(json.dumps(out,sort_keys=True))
    if out["mismatches"]:raise SystemExit(1)

if __name__=="__main__":main()
