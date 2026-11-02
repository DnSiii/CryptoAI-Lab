#!/usr/bin/env python3
"""V98 VW preregistered Clean-4 monthly spot-long/perp-short physical cash ledger.
2025 EXPOSED training ONLY; NOT a seven-slot engine, validated return or trading advice.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,datetime as dt
from pathlib import Path
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
SPOT_SHA="069bec10906e476e19470b042d40ce3fa7d654228de9cff50bd53ad91ed74156"
NH_SHA="7ce4ec7e2a6980838fa0179729b3cc6da8f131806b03e070590146d6d6ca046b"
START=1735689600000
HOUR=3600000
TIERS={"base":(12,7),"severe":(25,20),"supersevere":(40,35)}
ORDERS=("funding_before_fill","funding_after_fill")
FIELDS=("scenario","hour_index","utc_ms","cash","spot_value","perp_unrealized","equity","funding_delta","friction_delta","turnover_delta","adverse_equity","short_notional","trades_closed")
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p,fields):
    with open(p,newline="") as f:
        r=csv.DictReader(f)
        if tuple(r.fieldnames or ())!=fields:raise ValueError("VW_SCHEMA_"+str(p))
        return list(r)
def number(x):
    v=float(x)
    if not math.isfinite(v):raise ValueError("VW_NONFINITE")
    return v
def geometry(row):
    o,h,l,c,q=(number(row[k]) for k in ("open","high","low","close","quote_volume"))
    if min(o,h,l,c)<=0 or q<=0 or l>min(o,c) or h<max(o,c):
        raise ValueError("VW_OHLC_OR_EXECUTION_VOLUME")
    return (o,h,l,c,q)
def load(spot_dir,nh_dir):
    s=Path(spot_dir);n=Path(nh_dir)
    spot_path=s/"v98_spot_2025_observed_only.csv"
    if digest(spot_path)!=SPOT_SHA:raise ValueError("VW_SPOT_SOURCE_SHA")
    sr=json.loads((s/"v98_spot_2025_masked_source_receipt.json").read_text())
    if sr.get("canonical_sha256")!=SPOT_SHA or sr.get("decision")!="PASS_MASKED_SPOT_2025_SOURCE_ONLY_NOT_ECONOMIC":
        raise ValueError("VW_SPOT_RECEIPT")
    if digest(n/"nh_2025_official_source_receipt.json")!=NH_SHA:raise ValueError("VW_NH_SOURCE_SHA")
    nr=json.loads((n/"nh_2025_official_source_receipt.json").read_text())
    if nr.get("decision")!="PASS_NH_2025_OFFICIAL_SOURCE_ONLY_NOT_VALIDATION" or set(nr["assets"])!=set(ASSETS):
        raise ValueError("VW_NH_RECEIPT")
    sp=rows(spot_path,("asset","open_time_ms","open","high","low","close","quote_volume","source_zip_sha256"))
    if len(sp)!=35040:raise ValueError("VW_SPOT_COUNT")
    archives={a["archive"]:a["sha256"] for a in sr["archives"]}
    data={}
    for j,a in enumerate(ASSETS):
        pp=n/(a+"_1h_2025.csv");fp=n/(a+"_funding_2025.csv")
        if digest(pp)!=nr["assets"][a]["ohlc_csv_sha256"] or digest(fp)!=nr["assets"][a]["funding_envelope_csv_sha256"]:
            raise ValueError("VW_PERP_FUNDING_SHA_"+a)
        perp=rows(pp,("open_time_ms","open","high","low","close","quote_volume"))
        funding=rows(fp,("funding_slot_ms","funding_rate","exchange_offset_ms","mark_lower_bound","mark_upper_bound"))
        if len(perp)!=8760 or len(funding)!=1095:raise ValueError("VW_PERP_FUNDING_COUNT")
        spot=[];fut=[];events={}
        for k in range(8760):
            ts=START+k*HOUR
            z=sp[j*8760+k];p=perp[k]
            if z["asset"]!=a or int(z["open_time_ms"])!=ts or int(p["open_time_ms"])!=ts:
                raise ValueError("VW_HOUR_ALIGNMENT")
            ym=dt.datetime.fromtimestamp(ts/1000,dt.timezone.utc).strftime("%Y-%m")
            if z["source_zip_sha256"]!=archives.get(a+"-1h-"+ym+".zip"):
                raise ValueError("VW_SPOT_MONTH_SHA")
            spot.append(geometry(z));fut.append(geometry(p))
        for k,f in enumerate(funding):
            ts=START+k*8*HOUR
            if int(f["funding_slot_ms"])!=ts or not 0<=int(f["exchange_offset_ms"])<=60000:
                raise ValueError("VW_EVENT_ALIGNMENT")
            rate=number(f["funding_rate"]);lo=number(f["mark_lower_bound"]);hi=number(f["mark_upper_bound"])
            if not -1<=rate<=1 or lo<=0 or hi<lo:raise ValueError("VW_EVENT_GEOMETRY")
            events[k*8]=(rate,lo,hi)
        data[a]=(spot,fut,events)
    return data
def physical(data,tier,order):
    sc=TIERS[tier][0]/10000;pc=TIERS[tier][1]/10000
    cash=10000.;positions={};ledger=[];trades=[];fees=0.;turnover=0.;funding_sum=0.
    monthly=[];previous_month=None;high_water=10000.;dd=0.;adverse_dd=0.
    daily=[];last_day=None;funding_count=0;trades_closed=0
    def funding_event(k):
        nonlocal cash,funding_sum,funding_count
        delta=0.
        for a in ASSETS:
            e=data[a][2].get(k)
            if e is None:continue
            funding_count+=1
            if a in positions:
                rate,lo,hi=e
                q=positions[a]["q"]
                # Conservative short-perpetual receipt at lower mark, payment at upper.
                v=q*(lo if rate>=0 else hi)*rate
                delta+=v;positions[a]["funding"]+=v
        cash+=delta;funding_sum+=delta
        return delta
    def equity_at(k,field):
        sv=0.;pv=0.;short=0.
        for a,p in positions.items():
            spot,perp,_=data[a]
            q=p["q"];sv+=q*spot[k][field];pv+=q*(p["perp_entry"]-perp[k][field])
            short+=q*perp[k][field]
        return cash+sv+pv,sv,pv,short
    for k in range(8760):
        ts=START+k*HOUR
        month=dt.datetime.fromtimestamp(ts/1000,dt.timezone.utc).strftime("%Y-%m")
        rebalance=month!=previous_month
        exit_final=k==8759
        funding_delta=0.;friction=0.;turn=0.;closed=0
        if k%8==0 and (not rebalance or order=="funding_before_fill"):
            funding_delta+=funding_event(k)
        if rebalance or exit_final:
            if positions:
                before_close,_sv,_pv,_sn=equity_at(k,0)
                for a,p in list(positions.items()):
                    spot,perp,_=data[a];q=p["q"];so=spot[k][0];po=perp[k][0]
                    sell=q*so;closep=q*po
                    exit_fee=sell*sc+closep*pc
                    cash+=sell+q*(p["perp_entry"]-po)-exit_fee
                    fees+=exit_fee;friction+=exit_fee;turn+=sell+closep
                    gross=q*(so-p["spot_entry"])+q*(p["perp_entry"]-po)
                    realized=gross+p["funding"]-p["entry_fee"]-exit_fee
                    trades.append({"asset":a,"month":p["month"],"net_pnl":realized,
                                   "entry_notional":p["entry_notional"]})
                    closed+=1;trades_closed+=1
                positions.clear()
                if abs(cash-before_close)>max(1e-7,abs(before_close)*1e-10):
                    raise ValueError("VW_CLOSE_ACCOUNTING")
            if rebalance and not exit_final:
                if cash<=0:raise ValueError("VW_NEGATIVE_CAPITAL")
                entry_cash=cash
                for a in ASSETS:
                    spot,perp,_=data[a];so=spot[k][0];po=perp[k][0]
                    q=0.10*entry_cash/max(so,po)
                    entry_fee=q*(so*sc+po*pc)
                    cash-=q*so+entry_fee
                    fees+=entry_fee;friction+=entry_fee;turn+=q*(so+po)
                    positions[a]={"q":q,"spot_entry":so,"perp_entry":po,
                                  "entry_fee":entry_fee,"funding":0.,"month":month,
                                  "entry_notional":q*max(so,po)}
                if sum(p["q"]*(data[a][0][k][0]+data[a][1][k][0]) for a,p in positions.items())>0.80000001*entry_cash:
                    raise ValueError("VW_HIDDEN_GROSS")
            previous_month=month
        if k%8==0 and rebalance and order=="funding_after_fill":
            funding_delta+=funding_event(k)
        turnover+=turn
        # Mark at completed hourly close, never use this close to decide a fill.
        eq,sv,pv,short=equity_at(k,3)
        worst_sv=sum(p["q"]*data[a][0][k][2] for a,p in positions.items())
        worst_pv=sum(p["q"]*(p["perp_entry"]-data[a][1][k][1]) for a,p in positions.items())
        adverse=cash+worst_sv+worst_pv
        if not math.isfinite(eq) or eq<=0 or adverse<=0.05*short or cash<0.15*short:
            raise ValueError("VW_MARGIN_OR_ADVERSE_SOLVENCY_"+tier+"_"+order+"_"+str(k))
        high_water=max(high_water,eq)
        dd=min(dd,eq/high_water-1);adverse_dd=min(adverse_dd,adverse/high_water-1)
        ledger.append((tier+"/"+order,k,ts,cash,sv,pv,eq,funding_delta,friction,turn,adverse,short,closed))
        day=dt.datetime.fromtimestamp(ts/1000,dt.timezone.utc).strftime("%Y-%m-%d")
        if day!=last_day:
            daily.append(eq);last_day=day
        else:daily[-1]=eq
    if len(trades)!=48 or len(daily)!=365 or funding_count!=4380 or positions:
        raise ValueError("VW_COUNT_OR_UNCLOSED_POSITIONS")
    vals=[x["net_pnl"] for x in trades]
    wins=[x for x in vals if x>0];losses=[x for x in vals if x<0]
    pf=sum(wins)/-sum(losses) if losses else None
    payoff=(sum(wins)/len(wins))/(-sum(losses)/len(losses)) if wins and losses else None
    positives=sum(daily[i]>daily[i-1] for i in range(1,len(daily)))
    negatives=sum(daily[i]<daily[i-1] for i in range(1,len(daily)))
    final=ledger[-1][6]
    if abs(final-10000-sum(vals))>max(1e-5,abs(final)*1e-8):
        raise ValueError("VW_TRADE_CASH_RECONCILIATION")
    return {"scenario":tier+"/"+order,"final_equity":final,"2025_net_return":final/10000-1,
            "max_hourly_drawdown":dd,"max_adverse_drawdown":adverse_dd,
            "positive_days":positives,"negative_days":negatives,"trades":len(vals),
            "win_rate":len(wins)/len(vals),"profit_factor":pf,"payoff":payoff,
            "funding_net":funding_sum,"fees_and_slippage":fees,"turnover":turnover,
            "funding_events_checked":funding_count,"monthly_trade_pnl":trades},ledger
def run(spot,nh,out):
    data=load(spot,nh);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    scenarios=[];all_ledger=[]
    for tier in TIERS:
        for order in ORDERS:
            row,ledger=physical(data,tier,order)
            scenarios.append(row);all_ledger+=ledger
            print("VW_SCENARIO",row["scenario"],"2025_NET",round(row["2025_net_return"],8),
                  "MAX_DD",round(row["max_hourly_drawdown"],8),flush=True)
    fail=[x["scenario"] for x in scenarios if x["scenario"].split("/")[0] in ("severe","supersevere") and x["2025_net_return"]<=0]
    decision="REJECT_VW_NATIVE_CARRY_GROWTH_FEASIBILITY" if fail else "PASS_VW_EXPLORATORY_2025_NOT_SEVENSLOT_OR_VALIDATED"
    receipt={"decision":decision,"gate_failures":fail,"preregistration":"vw_native_carry_physical_prereg_20261101.md",
             "training_period":"2025 exposed only","assets":list(ASSETS),
             "source_spot_sha256":SPOT_SHA,"source_nh_receipt_sha256":NH_SHA,
             "scenarios":scenarios,"holdout_accessed":False,"2026_accessed":False,
             "benchmarks_accessed":False,"paper_live_authorized":False,
             "exact_event_mark_attested":False,"account_fees_verified":False}
    p=out/"vw_hourly_ledger.csv"
    with p.open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(FIELDS)
        for row in all_ledger:w.writerow([format(v,".15g") if isinstance(v,float) else v for v in row])
    receipt["hourly_ledger_sha256"]=digest(p)
    (out/"vw_result.json").write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("VW_DECISION",decision,flush=True)
    return receipt
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("spot-dir","nh-dir","output-dir"):p.add_argument("--"+name,required=True)
    a=p.parse_args();run(a.spot_dir,a.nh_dir,a.output_dir)
