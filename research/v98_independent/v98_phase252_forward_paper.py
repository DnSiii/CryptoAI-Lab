#!/usr/bin/env python3
"""V98 Phase252 forward paper shadow.

Runs only on a network lawfully authorized to access Binance USD-M public API.
No endpoint fallback. HTTP 451/403/418 hard-stop.
Forward results are quarantined from V98 model selection.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,json,math,time,urllib.parse,urllib.request
from pathlib import Path
from urllib.error import HTTPError

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
BASE="https://fapi.binance.com"
EPOCH=dt.datetime(2026,11,5,20,0,0,tzinfo=dt.timezone.utc)
CORE=.25
SLEEVE=.0625
MAX_GROSS=1.25
WINDOW_H=168
COST_PER_SIDE=.0007
UA="CryptoAI-Lab-V98-Phase252-Forward-Paper/1.0"
HOUR_MS=3_600_000

def ms(x:dt.datetime)->int:return int(x.timestamp()*1000)
def iso_ms(x:int)->str:return dt.datetime.fromtimestamp(x/1000,dt.timezone.utc).isoformat()
def floor_hour(x:dt.datetime)->dt.datetime:return x.replace(minute=0,second=0,microsecond=0)
def jread(path:Path,default):
    return json.loads(path.read_text()) if path.exists() else default
def api(path:str,params:dict):
    qs=urllib.parse.urlencode(params)
    url=f"{BASE}{path}?{qs}"
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read()
    except HTTPError as e:
        if e.code in (403,418,451):
            raise RuntimeError(f"HARD_ACCESS_BLOCK_HTTP_{e.code}_NO_FALLBACK") from e
        raise
    obj=json.loads(raw)
    return obj,url

def fetch_klines(asset,start_ms,end_ms):
    out=[];cursor=start_ms
    while cursor<=end_ms:
        rows,url=api("/fapi/v1/klines",{"symbol":asset,"interval":"1h","startTime":cursor,"endTime":end_ms,"limit":1000})
        if not rows:break
        for r in rows:
            ot=int(r[0])
            if start_ms<=ot<=end_ms:
                out.append({"open_time_ms":ot,"open":float(r[1]),"high":float(r[2]),"low":float(r[3]),"close":float(r[4])})
        nxt=int(rows[-1][0])+HOUR_MS
        if nxt<=cursor:break
        cursor=nxt
        if len(rows)<1000:break
    uniq={r["open_time_ms"]:r for r in out}
    return [uniq[k] for k in sorted(uniq)]

def fetch_funding(asset,start_ms,end_ms):
    out=[];cursor=start_ms
    while cursor<=end_ms:
        rows,url=api("/fapi/v1/fundingRate",{"symbol":asset,"startTime":cursor,"endTime":end_ms,"limit":1000})
        if not rows:break
        for r in rows:
            t=int(r["fundingTime"])
            if start_ms<=t<=end_ms:
                out.append({"funding_time_ms":t,"rate":float(r["fundingRate"]),"mark":float(r["markPrice"])})
        nxt=int(rows[-1]["fundingTime"])+1
        if nxt<=cursor:break
        cursor=nxt
        if len(rows)<1000:break
    uniq={r["funding_time_ms"]:r for r in out}
    return [uniq[k] for k in sorted(uniq)]

def funding_signal(funding_by_asset,decision_ms):
    start=decision_ms-WINDOW_H*HOUR_MS
    sums=[]
    for a in ASSETS:
        vals=[x["rate"] for x in funding_by_asset[a] if start < x["funding_time_ms"] <= decision_ms]
        sums.append(sum(vals))
    return sum(sums)/len(sums),sums

def write_ledger(path:Path,row:dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    exists=path.exists()
    with path.open("a",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(row))
        if not exists:w.writeheader()
        w.writerow(row)

def latest_ledger(path:Path):
    if not path.exists():return None
    with path.open(newline="") as f:
        rows=list(csv.DictReader(f))
    return rows[-1] if rows else None

def load_state(path:Path):
    if path.exists():return json.loads(path.read_text())
    return {
      "paper_epoch_utc":EPOCH.isoformat(),
      "cash":1.0,
      "units":{a:0.0 for a in ASSETS},
      "pending_weights":{a:CORE for a in ASSETS},
      "last_processed_hour_ms":None,
      "last_decision_ms":None,
      "peak_nav":1.0,
      "cum_turnover":0.0,
      "cum_costs":0.0,
      "cum_funding":0.0,
      "research_feedback_forbidden":True,
    }

def mark_nav(cash,units,prices):
    return cash+sum(units[a]*prices[a] for a in ASSETS)

def rebalance(cash,units,weights,opens):
    nav=mark_nav(cash,units,opens)
    if nav<=0:raise RuntimeError("PAPER_NAV_NONPOSITIVE")
    if sum(abs(weights[a]) for a in ASSETS)>MAX_GROSS+1e-12:raise RuntimeError("PAPER_GROSS_CAP")
    targets={a:weights[a]*nav/opens[a] for a in ASSETS}
    turnover=sum(abs(targets[a]-units[a])*opens[a] for a in ASSETS)
    cost=turnover*COST_PER_SIDE
    cash-=cost
    return cash,targets,turnover,cost

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path("research/v98_independent/paper_phase252_forward"))
    ap.add_argument("--now-utc",default=None,help="ISO UTC override for deterministic testing")
    a=ap.parse_args()
    now=dt.datetime.fromisoformat(a.now_utc.replace("Z","+00:00")) if a.now_utc else dt.datetime.now(dt.timezone.utc)
    now=now.astimezone(dt.timezone.utc)
    closed=floor_hour(now)-dt.timedelta(hours=1)
    if closed<EPOCH:
        raise SystemExit("NO_FORWARD_CLOSED_HOUR_YET")

    state_path=a.root/"state.json";ledger_path=a.root/"ledger.csv"
    state=load_state(state_path)
    last=state["last_processed_hour_ms"]
    start_dt=EPOCH if last is None else dt.datetime.fromtimestamp((last+HOUR_MS)/1000,dt.timezone.utc)
    if start_dt>closed:
        print(json.dumps({"status":"UP_TO_DATE","through":closed.isoformat()}));return

    warmup_start=start_dt-dt.timedelta(hours=WINDOW_H+24)
    k={};fund={}
    for asset in ASSETS:
        k[asset]=fetch_klines(asset,ms(start_dt),ms(closed))
        fund[asset]=fetch_funding(asset,ms(warmup_start),ms(closed)+HOUR_MS-1)

    maps={asset:{x["open_time_ms"]:x for x in k[asset]} for asset in ASSETS}
    hours=sorted(set.intersection(*[set(maps[a]) for a in ASSETS]))
    expected=list(range(ms(start_dt),ms(closed)+1,HOUR_MS))
    if hours!=expected:raise RuntimeError("PAPER_PRICE_HOURLY_COVERAGE_GAP")

    cash=float(state["cash"]);units={a:float(state["units"][a]) for a in ASSETS}
    pending={a:float(state["pending_weights"][a]) for a in ASSETS}
    peak=float(state["peak_nav"])

    for t in hours:
        hh=dt.datetime.fromtimestamp(t/1000,dt.timezone.utc)
        opens={a:maps[a][t]["open"] for a in ASSETS}
        closes={a:maps[a][t]["close"] for a in ASSETS}

        # Funding belongs to positions carried into the settlement timestamp.
        funding_cash=0.0
        for asset in ASSETS:
            for ev in fund[asset]:
                if t<=ev["funding_time_ms"]<t+HOUR_MS:
                    f=-units[asset]*ev["mark"]*ev["rate"]
                    cash+=f;funding_cash+=f
        state["cum_funding"]+=funding_cash

        turnover=cost=0.0
        if hh.hour==0:
            cash,units,turnover,cost=rebalance(cash,units,pending,opens)
            state["cum_turnover"]+=turnover;state["cum_costs"]+=cost

        nav=mark_nav(cash,units,closes)
        if nav<=0:raise RuntimeError("PAPER_RUIN")
        peak=max(peak,nav);dd=nav/peak-1

        opportunity_on=(sum(pending.values())>1.0+1e-12)
        mean_signal=""
        if hh.hour==23:
            decision_ms=t+HOUR_MS-1
            mean_signal,asset_sums=funding_signal(fund,decision_ms)
            on=mean_signal<=0
            pending={x:CORE+(SLEEVE if on else 0.0) for x in ASSETS}
            state["last_decision_ms"]=decision_ms
            opportunity_on=on

        write_ledger(ledger_path,{
          "hour_open_utc":hh.isoformat(),"nav":format(nav,".12g"),"drawdown":format(dd,".12g"),
          "gross_target_next":format(sum(abs(v) for v in pending.values()),".12g"),
          "opportunity_on_next":str(bool(opportunity_on)).lower(),
          "funding_signal_mean_168h":"" if mean_signal=="" else format(mean_signal,".12g"),
          "turnover":format(turnover,".12g"),"cost":format(cost,".12g"),
          "funding_cash":format(funding_cash,".12g"),
          **{f"{x}_close":format(closes[x],".12g") for x in ASSETS}
        })
        state["last_processed_hour_ms"]=t
        state["cash"]=cash;state["units"]=units;state["pending_weights"]=pending;state["peak_nav"]=peak

    a.root.mkdir(parents=True,exist_ok=True)
    state_path.write_text(json.dumps(state,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"PAPER_UPDATED","through":iso_ms(state["last_processed_hour_ms"]),
      "nav":mark_nav(state["cash"],state["units"],{x:maps[x][hours[-1]]["close"] for x in ASSETS}),
      "gross_target_next":sum(abs(v) for v in state["pending_weights"].values()),
      "research_feedback_forbidden":True},indent=2))

if __name__=="__main__":main()
