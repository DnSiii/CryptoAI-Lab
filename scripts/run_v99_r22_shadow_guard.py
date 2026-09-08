from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import FuturesData
from paper_once_v15 import build_v15

REPORT = PROJECT / "reports" / "candidate_v99_r22_shadow_guard.json"
HORIZONS = (7, 30, 90, 180, 365)


def stats(e):
    e = e.dropna().astype(float)
    if len(e) < 2:
        return {"return":0.0,"max_drawdown":0.0,"best_day":0.0,"worst_day":0.0,"positive_days":0.0}
    n=e/e.iloc[0]; dd=n/n.cummax()-1
    d=n.resample("1D").last().pct_change(fill_method=None).dropna()
    return {"return":float(n.iloc[-1]-1),"max_drawdown":float(dd.min()),"best_day":float(d.max()) if len(d) else 0.0,"worst_day":float(d.min()) if len(d) else 0.0,"positive_days":float((d>0).mean()) if len(d) else 0.0}


def slice_data(data,start,end):
    return FuturesData(frames={k:v.loc[start:end].copy() for k,v in data.frames.items()},funding=data.funding.loc[start:end].copy(),symbols=data.symbols)


def cap_gross(t,cap):
    g=t.abs().sum(axis=1); f=(cap/g.replace(0,np.nan)).clip(upper=1).fillna(1); return t.mul(f,axis=0)


def run(data,t,execution,cost,gross,guard=None):
    kw={}
    if guard is not None:
        kw={"drawdown_guard_threshold":guard["drawdown_threshold"],"drawdown_guard_multiplier":guard["exposure_multiplier"],"drawdown_guard_cooldown_hours":guard["cooldown_hours"]}
    return exact_fast(data,t,cost_per_side=cost,maintenance_equity_fraction=execution["maintenance_equity_fraction"],gross_guard_cap=gross,**kw)


def shadow_guard_factor(eq,guard):
    e=eq.astype(float); vals=e.to_numpy(); out=np.ones(len(e)); peak=1.0; active=False; until=-1
    for i,x in enumerate(vals):
        if not np.isfinite(x): x=vals[i-1] if i else 1.0
        if active and i>=until:
            active=False; peak=x
        dd=x/peak-1 if peak>0 else -1
        if (not active) and dd<=-abs(float(guard["drawdown_threshold"])):
            active=True; until=i+int(guard["cooldown_hours"])
        out[i]=float(guard["exposure_multiplier"]) if active else 1.0
        peak=max(peak,x)
    return pd.Series(out,index=e.index)


def extra_scale(eq,btc,attack_scale,defense_scale,strength,defense_dd):
    e=eq.astype(float); dd=e/e.cummax()-1
    r24=e/e.shift(24)-1; r7=e/e.shift(168)-1; r30=e/e.shift(720)-1; r90=e/e.shift(2160)-1
    b7=btc/btc.shift(168)-1; b30=btc/btc.shift(720)-1
    ema=btc.ewm(span=336,adjust=False,min_periods=336).mean()
    v7=btc.pct_change(fill_method=None).rolling(168,min_periods=48).std(); v30=btc.pct_change(fill_method=None).rolling(720,min_periods=168).std()
    if strength==1:
        attack=(r7>0.015)&(r30>0.035)&(dd>-0.06)&(btc>ema)&(b30>-0.01)
    elif strength==2:
        attack=(r7>0.025)&(r30>0.055)&(r90>0.07)&(dd>-0.045)&(btc>ema)&(b7>0)&(b30>0)
    else:
        attack=(r7>0.04)&(r30>0.075)&(r90>0.10)&(dd>-0.035)&(btc>ema)&(b7>0.01)&(b30>0.02)&((v7<1.25*v30)|v30.isna())
    shock=((dd<=-abs(defense_dd))|(r24<-0.035)|((r7<-0.055)&(r30<0))).fillna(False)
    # keep defense active for 72 hours after a shock
    defense=shock.astype(float).rolling(72,min_periods=1).max().gt(0)
    s=pd.Series(1.0,index=e.index)
    s.loc[attack.fillna(False)&~defense]=float(attack_scale)
    s.loc[defense]=float(defense_scale)
    return s


def construct(raw_targets,shadow_eq,btc,guard,params):
    gf=shadow_guard_factor(shadow_eq,guard)
    xs=extra_scale(shadow_eq,btc,params["attack_scale"],params["defense_scale"],params["strength"],params["defense_dd"])
    # close-t state controls target executed at t+1 open; no future shift needed.
    total=gf*xs
    t=raw_targets.mul(total,axis=0)
    t=cap_gross(t,params["gross_cap"])
    return t,total


def build_on_slice(data,raw_targets,execution,guard,base_gross,base_cost,params,start,end):
    d=slice_data(data,start,end); raw=raw_targets.reindex(index=d.close.index,columns=d.close.columns).fillna(0)
    shadow=run(d,raw,execution,base_cost,base_gross,guard).equity
    t,_=construct(raw,shadow,d.close["BTCUSDT"],guard,params)
    candidate=run(d,t,execution,base_cost,params["gross_cap"],None).equity
    return stats(candidate),stats(shadow)


def main():
    candidate,data,raw_targets,v15_result,_,quarantined,metadata=build_v15()
    v14=json.loads((PROJECT/"config"/candidate["parent_candidate_config"]).read_text())
    finalist=json.loads((PROJECT/"config"/v14["frozen_core_config"]).read_text())
    base=json.loads((PROJECT/"config"/finalist["base_candidate_config"]).read_text())
    execution=base["execution"]; guard=v14["circuit_breaker"]; base_gross=float(v14["allocation"]["gross_drift_guard_cap"])
    base_cost=float(execution["base_cost_per_side"]); severe_cost=float(execution["severe_cost_per_side"])

    shadow=run(data,raw_targets,execution,base_cost,base_gross,guard).equity
    v15=stats(shadow)
    v15_severe=stats(run(data,raw_targets,execution,severe_cost,base_gross,guard).equity)

    rows=[]; cache={}; split=int(len(data.close.index)*0.60); train_end=data.close.index[split]; hold_start=data.close.index[min(split+1,len(data.close.index)-1)]
    for attack_scale,defense_scale,strength,defense_dd,gross_cap in itertools.product((1.15,1.25,1.35,1.50),(0.35,0.55,0.75),(1,2,3),(0.06,0.09),(1.9,2.2,2.5)):
        params={"attack_scale":attack_scale,"defense_scale":defense_scale,"strength":strength,"defense_dd":defense_dd,"gross_cap":gross_cap}
        t,scale=construct(raw_targets,shadow,data.close["BTCUSDT"],guard,params)
        result=run(data,t,execution,base_cost,gross_cap,None).equity
        full=stats(result)
        train=stats(result.loc[:train_end]); hold=stats(result.loc[hold_start:]); train_v=stats(shadow.loc[:train_end]); hold_v=stats(shadow.loc[hold_start:])
        wr=(1+full["return"])/(1+v15["return"]); tr=(1+train["return"])/(1+train_v["return"]); hr=(1+hold["return"])/(1+hold_v["return"])
        dr=abs(full["max_drawdown"])/abs(v15["max_drawdown"]); hdr=abs(hold["max_drawdown"])/max(1e-12,abs(hold_v["max_drawdown"])); worst=abs(full["worst_day"])/abs(v15["worst_day"])
        score=3*np.log(max(wr,1e-12))+2*np.log(max(hr,1e-12))+1.5*max(0,1-dr)-3*max(0,dr-1)-1.5*max(0,worst-1)
        key=f"a{attack_scale:.2f}_d{defense_scale:.2f}_s{strength}_dd{defense_dd:.2f}_g{gross_cap:.1f}"
        row={"key":key,"params":params,"summary":full,"wealth_ratio_to_v15":float(wr),"train_wealth_ratio":float(tr),"holdout_wealth_ratio":float(hr),"drawdown_ratio_to_v15":float(dr),"holdout_drawdown_ratio":float(hdr),"worst_day_ratio_to_v15":float(worst),"attack_scale_fraction":float((scale>1).mean()),"defense_fraction":float((scale<1).mean()),"average_scale":float(scale.mean()),"score":float(score)}
        rows.append(row); cache[key]=t

    ranking=sorted(rows,key=lambda x:x["score"],reverse=True)
    finalists=[]; end=data.close.index[-1]
    for row in ranking[:10]:
        params=row["params"]; t=cache[row["key"]]
        iso={}; iso_v={}; wins={}; ddwins={}
        for days in HORIZONS:
            start=end-pd.Timedelta(days=days)
            a,b=build_on_slice(data,raw_targets,execution,guard,base_gross,base_cost,params,start,end)
            iso[str(days)]=a; iso_v[str(days)]=b; wins[str(days)]=a["return"]>=b["return"]; ddwins[str(days)]=abs(a["max_drawdown"])<=abs(b["max_drawdown"])
        severe=stats(run(data,t,execution,severe_cost,params["gross_cap"],None).equity); severe_ratio=(1+severe["return"])/(1+v15_severe["return"])
        gate=bool(all(wins.values()) and row["wealth_ratio_to_v15"]>=1.25 and row["drawdown_ratio_to_v15"]<=0.80 and row["worst_day_ratio_to_v15"]<=0.85 and row["holdout_wealth_ratio"]>=1.15 and row["holdout_drawdown_ratio"]<=0.85 and severe_ratio>=1.15)
        finalists.append({**row,"isolated":iso,"isolated_v15":iso_v,"isolated_return_wins_vs_v15":wins,"isolated_drawdown_wins_vs_v15":ddwins,"severe_cost":severe,"severe_wealth_ratio_to_v15":float(severe_ratio),"superior_gate_passed":gate})
    finalists.sort(key=lambda x:(x["superior_gate_passed"],sum(x["isolated_return_wins_vs_v15"].values()),x["holdout_wealth_ratio"],x["wealth_ratio_to_v15"],-x["drawdown_ratio_to_v15"]),reverse=True)
    selected=finalists[0] if finalists else None
    report={"study":"V99 R22 shadow-guard convex scaling","status":"RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER","objective":"preserve the untouched V15 shadow circuit-breaker schedule while scaling actual V99 exposure causally, seeking materially higher compounding and materially lower risk","disclosure":"Historical research only. No future data is used in the signal, but parameters are researched on history. Any winner still requires freezing and independent forward paper.","grid_size":len(rows),"v15":{"summary":v15,"severe_cost":v15_severe},"selected":selected,"finalists":finalists,"top_screen":ranking[:30],"promotion_rule":{"beat_v15_isolated_all_horizons":True,"full_wealth_ratio_minimum":1.25,"full_drawdown_ratio_maximum":0.80,"worst_day_ratio_maximum":0.85,"holdout_wealth_ratio_minimum":1.15,"holdout_drawdown_ratio_maximum":0.85,"severe_cost_wealth_ratio_minimum":1.15},"funding_quarantined_symbols":quarantined,"v15_metadata":metadata}
    REPORT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"study":report["study"],"grid_size":len(rows),"v15":report["v15"],"selected":selected},indent=2),flush=True)

if __name__=="__main__": main()
