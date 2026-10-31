#!/usr/bin/env python3
"""V98 2022-25 Clean-4 SOURCE-ONLY bridge. 2025 exposed: training, never validation."""
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np,pandas as pd
from v98_clean4_training_reader import load as load_old,ASSETS
from v98_mark_envelope_settlement import read_envelope
START=1735689600000;HOUR=3600000;PIN="7ce4ec7e2a6980838fa0179729b3cc6da8f131806b03e070590146d6d6ca046b"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(old_root,old_envelope,new_root,corrected_root):
    old=load_old(old_root);lo0,hi0,_=read_envelope(old_envelope,old)
    new_root=Path(new_root);corrected_root=Path(corrected_root)
    rpath=new_root/"nh_2025_official_source_receipt.json"
    if sha(rpath)!=PIN:raise ValueError("V98_BRIDGE_2025_SOURCE_PIN")
    receipt=json.loads(rpath.read_text())
    fixed=json.loads((corrected_root/"v98_2025_boundary_receipt.json").read_text())
    if (receipt["decision"]!="PASS_NH_2025_OFFICIAL_SOURCE_ONLY_NOT_VALIDATION"
        or fixed["decision"]!="PASS_V98_2025_TRAINING_SOURCE_CROSSYEAR_BOUNDARY_NOT_VALIDATION"
        or set(receipt["assets"])!=set(ASSETS) or set(fixed["assets"])!=set(ASSETS)):
        raise ValueError("V98_BRIDGE_SOURCE_RECEIPT")
    x=np.empty((8760,4,5));rate=np.zeros((8760,4));event=np.zeros((8760,4),bool)
    lo=np.full((8760,4),np.nan);hi=np.full((8760,4),np.nan)
    for j,a in enumerate(ASSETS):
        cp=new_root/f"{a}_1h_2025.csv";fp=new_root/f"{a}_funding_2025.csv"
        bp=corrected_root/f"{a}_funding_2025_boundary_corrected.csv"
        if (sha(cp)!=receipt["assets"][a]["ohlc_csv_sha256"] or
            sha(fp)!=receipt["assets"][a]["funding_envelope_csv_sha256"] or
            sha(bp)!=fixed["assets"][a]["corrected_funding_sha256"]):
            raise ValueError("V98_BRIDGE_2025_SOURCE_SHA_"+a)
        f=pd.read_csv(cp)
        if list(f.columns)!=["open_time_ms","open","high","low","close","quote_volume"] or len(f)!=8760 or not np.array_equal(f["open_time_ms"].to_numpy(np.int64),START+np.arange(8760)*HOUR):
            raise ValueError("V98_BRIDGE_2025_HOUR_CALENDAR_"+a)
        v=f[["open","high","low","close","quote_volume"]].to_numpy(float)
        if not np.isfinite(v).all() or np.any(v[:,:4]<=0) or np.any(v[:,4]<0) or np.any(v[:,2]>np.minimum(v[:,0],v[:,3])) or np.any(v[:,1]<np.maximum(v[:,0],v[:,3])):
            raise ValueError("V98_BRIDGE_2025_OHLC_"+a)
        x[:,j,:]=v
        with bp.open(newline="") as handle:funding=list(csv.DictReader(handle))
        if len(funding)!=1095:raise ValueError("V98_BRIDGE_2025_FUNDING_COUNT_"+a)
        with fp.open(newline="") as handle:original=list(csv.DictReader(handle))
        if funding[1:]!=original[1:] or any(funding[0][k]!=original[0][k] for k in ("funding_slot_ms","funding_rate","exchange_offset_ms")):
            raise ValueError("V98_BRIDGE_NONBOUNDARY_MUTATION_"+a)
        for k,row in enumerate(funding):
            t=k*8
            if int(row["funding_slot_ms"])!=START+t*HOUR or not 0<=int(row["exchange_offset_ms"])<=60000:
                raise ValueError("V98_BRIDGE_2025_FUNDING_CALENDAR_"+a)
            rr,ll,hh=map(float,(row["funding_rate"],row["mark_lower_bound"],row["mark_upper_bound"]))
            if not all(map(math.isfinite,(rr,ll,hh))) or ll<=0 or hh<ll:
                raise ValueError("V98_BRIDGE_2025_FUNDING_GEOMETRY_"+a)
            rate[t,j]=rr;lo[t,j]=ll;hi[t,j]=hh;event[t,j]=True
    if len(old["time"])!=18288:raise ValueError("V98_BRIDGE_OLD_HOURS")
    full={k:np.concatenate((old[k],x[:,:,i]),axis=0) for i,k in enumerate(("o","h","l","c","q"))}
    full["rate"]=np.concatenate((old["rate"],rate),axis=0)
    full["event"]=np.concatenate((old["event"],event),axis=0)
    full["mark_lower"]=np.concatenate((lo0,lo),axis=0)
    full["mark_upper"]=np.concatenate((hi0,hi),axis=0)
    full["time"]=pd.date_range("2022-12-01",periods=27048,freq="h",tz="UTC")
    if (len(full["time"])!=27048 or full["time"][18288]!=pd.Timestamp("2025-01-01",tz="UTC")
        or full["time"][-1]!=pd.Timestamp("2025-12-31 23:00",tz="UTC")
        or int(full["event"].sum())!=13524
        or not np.all(np.isfinite(full["mark_lower"][full["event"]]))
        or not np.all(np.isfinite(full["mark_upper"][full["event"]]))):
        raise ValueError("V98_BRIDGE_FULL_CHRONOLOGY_OR_EVENTS")
    # A source hour with zero traded quote volume cannot support a physical fill.
    # 2024-10-28 20:00 UTC has zero volume for all four Clean-4 assets.
    full["execution_allowed"]=full["q"]>0
    full.update(training_only=True,year_2025_exposed=True,exact_funding_tick_mark=False,holdout_accessed=False)
    return full
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for field in ("old-root","old-envelope","new-root","corrected-root","output"):p.add_argument("--"+field,required=True)
    a=p.parse_args();d=load(a.old_root,a.old_envelope,a.new_root,a.corrected_root)
    receipt={"decision":"PASS_V98_FULL_CLEAN4_2022_2025_SOURCE_ONLY_NOT_VALIDATION",
             "hours":len(d["time"]),"funding_events":int(d["event"].sum()),
             "assets":list(ASSETS),"2025_exposed_training_only":True,
             "exact_funding_tick_mark_attested":False,"pnl_computed":False,
             "2026_accessed":False,"holdout_accessed":False,
             "zero_volume_execution_blocked_cells":int((~d["execution_allowed"]).sum()),
             "zero_volume_execution_blocked_hours":int((~d["execution_allowed"].all(axis=1)).sum())}
    Path(a.output).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
