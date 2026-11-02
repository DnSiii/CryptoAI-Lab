#!/usr/bin/env python3
"""V98 VX: preregistered spot-led seven-slot causal targets, NOT a PnL simulator.
Frozen rejected VW/PU signals and parameters are not imported. Exposed 2025 only.
"""
from __future__ import annotations
import json,math
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=8760
WARMUP=744
STEP=168
CLOCK=tuple(range(WARMUP,HOURS,STEP))
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"VX_full":(0,1,2,3),"VX_core_only":(0,),
       "VX_minus_opportunity":(0,2,3),"VX_minus_RV":(0,1,3),
       "VX_minus_stress":(0,1,2)}
# Weights: [slot, instrument(0=spot,1=USD-M), asset].
# A short USD-M leg is a real short, not a free spot-perp carry.
SPOT_COST=.003
PERP_COST=.002
HORIZON=168

def from_vw_data(data):
    if set(data)!=set(ASSETS):raise ValueError("VX_UNIVERSE")
    spot=np.empty((HOURS,4));perp=np.empty((HOURS,4));vol=np.empty((HOURS,4))
    rate=np.zeros((HOURS,4));event=np.zeros((HOURS,4),bool)
    for j,a in enumerate(ASSETS):
        s,p,e=data[a]
        if len(s)!=HOURS or len(p)!=HOURS or len(e)!=1095:
            raise ValueError("VX_SOURCE_LENGTH")
        for t in range(HOURS):
            spot[t,j]=float(s[t][3]);perp[t,j]=float(p[t][3])
            vol[t,j]=float(s[t][4])
        for t,v in e.items():
            if type(t)!=int or t<0 or t>=HOURS or t%8:
                raise ValueError("VX_FUNDING_TIME")
            rate[t,j]=float(v[0]);event[t,j]=True
    return {"spot":spot,"perp":perp,"vol":vol,"rate":rate,"event":event}

def source_gate(d):
    for name in ("spot","perp","vol","rate","event"):
        if np.asarray(d[name]).shape!=(HOURS,4):raise ValueError("VX_SOURCE_SHAPE_"+name)
    if not all(np.isfinite(d[k]).all() for k in ("spot","perp","vol","rate")):
        raise ValueError("VX_NONFINITE")
    if np.any(d["spot"]<=0) or np.any(d["perp"]<=0) or np.any(d["vol"]<0):
        raise ValueError("VX_PRICE_OR_VOLUME")
    if np.asarray(d["event"]).dtype!=bool or int(d["event"].sum())!=4380:
        raise ValueError("VX_EVENT_COUNT")
    if not np.all(d["event"][::8]) or np.any(d["event"][np.arange(HOURS)%8!=0]):
        raise ValueError("VX_EVENT_CLOCK")
    if np.any(np.abs(d["rate"][d["event"]])>1) or np.any(d["rate"][~d["event"]]!=0):
        raise ValueError("VX_RATE_GEOMETRY")
    return {"decision":"PASS_VX_SOURCE_SHAPE_NOT_PROVENANCE_OR_PNL",
            "hours":HOURS,"funding_events":4380}

def incremental_utility(spot_leg,perp_leg,spot_log,perp_log,volatility,funding_8h):
    # Ex-ante fixed heuristic, not an expected return estimate or fitted model.
    projected_spot=spot_log*.5
    projected_perp=perp_log*.5
    carry=HORIZON/8*funding_8h
    directional=float(spot_leg@projected_spot+perp_leg@projected_perp)
    funding=float(-perp_leg@carry)
    costs=float(SPOT_COST*np.abs(spot_leg).sum()+PERP_COST*np.abs(perp_leg).sum())
    variance=float(.5*np.dot(spot_leg**2+perp_leg**2,volatility**2))
    return directional+funding-costs-variance

def decisions(d):
    source_gate(d)
    sp=np.log(np.asarray(d["spot"],float))
    pp=np.log(np.asarray(d["perp"],float))
    q=np.asarray(d["vol"],float)
    rate=np.asarray(d["rate"],float)
    out={}
    for t in CLOCK:
        r336=sp[t]-sp[t-336];r168=sp[t]-sp[t-168]
        r72=sp[t]-sp[t-72];r24=sp[t]-sp[t-24]
        pr336=pp[t]-pp[t-336]
        # Trailing 336 completed hourly returns; no future data.
        vol336=np.std(np.diff(sp[t-336:t+1],axis=0),axis=0)*math.sqrt(HORIZON)
        funding=np.mean(rate[t-160:t+1:8],axis=0)
        breadth=int(np.sum(r336>0))
        regime="risk_on" if breadth>=3 else "risk_off" if breadth<=1 else "mixed"
        raw=np.zeros((4,2,4),float)
        eligible=sorted((j for j in range(4) if r336[j]>0),
                        key=lambda j:(-r336[j],j))
        for j,w in zip(eligible[:2],(.28,.18)):
            raw[0,0,j]=w
        if regime!="risk_off":
            eligible_opp=[j for j in range(4)
                          if sp[t,j]>float(np.max(sp[t-72:t,j]))
                          and r24[j]>0 and
                          float(q[t-23:t+1,j].sum())>=1.3*max(float(q[t-47:t-23,j].sum()),1.)]
            if eligible_opp:
                j=min(eligible_opp,key=lambda k:(-r24[k],k))
                raw[1,0,j]=.10
        leader=min(range(4),key=lambda j:(-r168[j],j))
        laggard=min(range(4),key=lambda j:(r168[j],j))
        if (leader!=laggard and r168[leader]-r168[laggard]>=.15
                and r168[laggard]<0 and funding[laggard]>=0):
            raw[2,0,leader]=.08
            raw[2,1,laggard]=-.08
        if regime!="risk_on" and int(np.sum(r72<=-.08))>=3:
            raw[3,1,0]=-.12
        selected=raw.copy()
        for slot in (1,2,3):
            if incremental_utility(raw[slot,0],raw[slot,1],r336,pr336,vol336,funding)<=.005:
                selected[slot]=0.
        # Deterministic optional clipping, core never increased by risk budget.
        room=max(0.,.80-float(np.abs(selected[0]).sum()))
        for slot in (1,2,3):
            gross=float(np.abs(selected[slot]).sum())
            if gross>room and gross>0:selected[slot]*=room/gross
            room=max(0.,room-float(np.abs(selected[slot]).sum()))
        if (np.abs(selected).sum()>.80+1e-10 or
            np.abs(selected[:,0]).sum()>.65+1e-10 or
            np.abs(selected[:,1]).sum()>.20+1e-10):
            raise ValueError("VX_GROSS_OR_INSTRUMENT_CAP")
        out[t]={"regime":regime,"weights":selected,"raw":raw}
    if len(out)!=len(CLOCK):raise ValueError("VX_CLOCK")
    return out

def books(d):
    dec=decisions(d)
    result={}
    for name,slots in BOOKS.items():
        book={}
        for t,x in dec.items():
            w=x["weights"].copy()
            for k in range(4):
                if k not in slots:w[k]=0.
            book[t]=w
        result[name]=book
    return result

def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    spot=100*np.exp(.00008*t*(1+j/9)+.07*np.sin(t/40+j))
    perp=spot*(1+.0003*np.cos(t/60+j))
    vol=np.broadcast_to(1e6*(1+.2*np.sin(t/15+j)),(HOURS,4)).copy()
    rate=np.zeros((HOURS,4));event=np.zeros((HOURS,4),bool)
    rate[::8]=.0001;event[::8]=True
    d={"spot":spot,"perp":perp,"vol":vol,"rate":rate,"event":event}
    a=decisions(d);b={k:v.copy() for k,v in d.items()}
    b["spot"][5000:]*=np.array([2.,.6,1.5,.7])
    b["perp"][5000:]*=np.array([1.8,.7,1.3,.8])
    b["vol"][5000:]*=2.;b["rate"][5000:]*=4.
    c=decisions(b)
    for k in CLOCK:
        if k>=5000:continue
        if a[k]["regime"]!=c[k]["regime"] or not np.array_equal(a[k]["weights"],c[k]["weights"]):
            raise ValueError("VX_FUTURE_MUTATION_LEAK")
    result=books(d)
    if set(result)!=set(BOOKS) or any(len(x)!=len(CLOCK) for x in result.values()):
        raise ValueError("VX_BOOK_COVERAGE")
    return {"decision":"PASS_VX_CAUSAL_TARGETS_ONLY_NOT_ECONOMIC",
            "decisions":len(CLOCK),"books":len(BOOKS),
            "future_mutation_safe":True,"historical_pnl_computed":False,
            "account_costs_authenticated":False,"2026_accessed":False,
            "paper_live_authorized":False}

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
