#!/usr/bin/env python3
"""V98-only source uncertainty; no candidate PnL, holdout or exact-tick claims."""
import argparse,csv,datetime as dt,hashlib,json,math
from pathlib import Path
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
HOURS=27048
CAP=.84
FIELDS=("asset","funding_hour_utc","funding_rate","mark_lower","mark_upper",
        "mark_width_bps","hypothetical_equity_width_bps")

def event_rows(d):
    for k in ("rate","event","mark_lower","mark_upper"):
        if np.asarray(d[k]).shape!=(HOURS,4):
            raise ValueError("V98_MARK_UNCERTAINTY_SOURCE_SHAPE_"+k)
    if not d.get("training_only") or not d.get("year_2025_exposed") or d.get("exact_funding_tick_mark"):
        raise ValueError("V98_MARK_UNCERTAINTY_SOURCE_SCOPE")
    if int(d["event"].sum())!=13524 or not np.all(d["event"][::8]) or np.any(d["event"][1::8]):
        raise ValueError("V98_MARK_UNCERTAINTY_EVENT_CALENDAR")
    if np.any(d["event"][np.arange(HOURS)%8!=0]):
        raise ValueError("V98_MARK_UNCERTAINTY_OFFSLOT")
    if np.any(d["rate"][~d["event"]]!=0):
        raise ValueError("V98_MARK_UNCERTAINTY_OFFEVENT_RATE")
    rows=[]
    for t in range(0,HOURS,8):
        stamp=(START+dt.timedelta(hours=t)).isoformat()
        for j,asset in enumerate(ASSETS):
            if not bool(d["event"][t,j]):
                raise ValueError("V98_MARK_UNCERTAINTY_MISSING_EVENT")
            r=float(d["rate"][t,j]);lo=float(d["mark_lower"][t,j]);hi=float(d["mark_upper"][t,j])
            if not all(math.isfinite(x) for x in (r,lo,hi)) or lo<=0 or hi<lo:
                raise ValueError("V98_MARK_UNCERTAINTY_INVALID_MARK_OR_RATE")
            width=(hi-lo)/lo*10000.
            budget=CAP*abs(r)*width
            rows.append((asset,stamp,r,lo,hi,width,budget))
    if len(rows)!=13524:raise ValueError("V98_MARK_UNCERTAINTY_COUNT")
    return rows

def nearest(values,p):
    ordered=sorted(values)
    return ordered[max(0,math.ceil(p*len(ordered))-1)]

def summarize(rows):
    if len(rows)!=13524 or len({(r[0],r[1]) for r in rows})!=13524:
        raise ValueError("V98_MARK_UNCERTAINTY_ROW_COUNT_OR_DUPLICATE")
    by_hour={}
    by_asset={a:[] for a in ASSETS}
    for asset,stamp,rate,lo,hi,width,budget in rows:
        if asset not in by_asset or not all(math.isfinite(x) for x in (rate,lo,hi,width,budget)):
            raise ValueError("V98_MARK_UNCERTAINTY_NONFINITE")
        if lo<=0 or hi<lo or abs(width-(hi-lo)/lo*10000)>1e-8 or abs(budget-CAP*abs(rate)*width)>1e-8:
            raise ValueError("V98_MARK_UNCERTAINTY_IDENTITY")
        by_asset[asset].append(width)
        by_hour[stamp]=max(by_hour.get(stamp,0.),budget)
    if len(by_hour)!=3381 or any(len(v)!=3381 for v in by_asset.values()):
        raise ValueError("V98_MARK_UNCERTAINTY_HOURLY_COVERAGE")
    widths=[r[5] for r in rows]
    budgets=list(by_hour.values())
    def stats(x):
        return {"p50":nearest(x,.5),"p95":nearest(x,.95),
                "p99":nearest(x,.99),"max":max(x)}
    return {"decision":"PASS_ENVELOPE_UNCERTAINTY_QUANTIFIED_NOT_EXACT_MARK",
            "assets":list(ASSETS),"funding_asset_events":len(rows),
            "funding_hour_slots":len(by_hour),"width_bps":stats(widths),
            "hypothetical_equity_width_bps_per_slot":stats(budgets),
            "hour_slots_above_equity_width_bps":{str(x):sum(v>x for v in budgets) for x in (1,5,10,50)},
            "max_width_bps_by_asset":{a:max(v) for a,v in by_asset.items()},
            "top10_widest_event_intervals":[
                {"asset":r[0],"funding_hour_utc":r[1],"width_bps":r[5]}
                for r in sorted(rows,key=lambda r:(-r[5],r[1],r[0]))[:10]],
            "hypothetical_gross_cap":CAP,
            "hypothetical_local_equity_fraction_only":True,
            "not_a_dynamic_nav_or_cagr_bound":True,
            "exact_exchange_funding_event_marks_present":False,
            "2025_exposed_training_only":True,"2026_data_accessed":False,
            "holdout_accessed":False,"benchmarks_accessed":False,
            "pnl_computed":False,"trading_authorized":False}

def synthetic_test():
    # Prove local bound for arbitrary signed 4-asset positions under gross at lower marks.
    rng=np.random.default_rng(98)
    tested=0
    for _ in range(1000):
        lo=rng.uniform(1,1000,4);hi=lo*rng.uniform(1,1.1,4)
        rate=rng.uniform(-.003,.003,4);q=rng.normal(size=4)
        q*=CAP/max(float(np.dot(np.abs(q),lo)),1e-15)
        actual=float(np.dot(np.abs(q*rate),hi-lo))
        upper=CAP*float(np.max(np.abs(rate)*(hi-lo)/lo))
        if actual>upper+1e-12:raise ValueError("V98_MARK_UNCERTAINTY_LOCAL_BOUND_FAIL")
        tested+=1
    return {"decision":"PASS_SYNTHETIC_LOCAL_BOUND_NOT_PNL","signed_cases":tested}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--old-root");p.add_argument("--old-envelope")
    p.add_argument("--new-root");p.add_argument("--corrected-root")
    p.add_argument("--output-dir");p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        print(json.dumps(synthetic_test(),sort_keys=True));return
    if not all((a.old_root,a.old_envelope,a.new_root,a.corrected_root,a.output_dir)):
        p.error("all four authenticated source paths and output-dir required")
    from v98_2025_full_training_source_bridge import load
    d=load(a.old_root,a.old_envelope,a.new_root,a.corrected_root)
    rows=event_rows(d)
    result=summarize(rows)
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    target=out/"v98_mark_uncertainty_events.csv"
    with target.open("w",newline="") as f:
        writer=csv.writer(f,lineterminator="\\n")
        writer.writerow(FIELDS)
        for row in rows:
            writer.writerow([row[0],row[1]]+[format(x,".17g") for x in row[2:]])
    result["canonical_csv_sha256"]=hashlib.sha256(target.read_bytes()).hexdigest()
    (out/"v98_mark_uncertainty_receipt.json").write_text(
        json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\\n")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
if __name__=="__main__":main()
