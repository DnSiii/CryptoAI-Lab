#!/usr/bin/env python3
"""Independent VW read-only hourly cash/mark replay and deliberate tamper rejection."""
import csv,hashlib,json,math,sys
from pathlib import Path
FIELDS=("scenario","hour_index","utc_ms","cash","spot_value","perp_unrealized",
        "equity","funding_delta","friction_delta","turnover_delta","adverse_equity",
        "short_notional","trades_closed")
START=1735689600000;HOUR=3600000
def near(a,b):
    return abs(a-b)<=max(2e-6,abs(b)*2e-10)
def validate(receipt,records):
    scenarios=receipt["scenarios"]
    if len(scenarios)!=6 or len(records)!=6*8760:raise ValueError("VW_AUDIT_SIZE")
    if receipt["2026_accessed"] or receipt["holdout_accessed"] or receipt["benchmarks_accessed"] or receipt["paper_live_authorized"]:
        raise ValueError("VW_AUDIT_FIREWALL")
    names=[s["scenario"] for s in scenarios]
    if len(set(names))!=6:raise ValueError("VW_AUDIT_DUPLICATE")
    for i,scenario in enumerate(scenarios):
        group=records[i*8760:(i+1)*8760]
        hwm=10000.;dd=0.;adverse_dd=0.;fees=0.;funding=0.;turnover=0.;closed=0
        for k,r in enumerate(group):
            if tuple(r)!=FIELDS:raise ValueError("VW_AUDIT_SCHEMA")
            if r["scenario"]!=scenario["scenario"] or int(r["hour_index"])!=k or int(r["utc_ms"])!=START+k*HOUR:
                raise ValueError("VW_AUDIT_CLOCK")
            cash,spot,perp,eq,fd,fr,turn,adverse,short=[float(r[z]) for z in
                ("cash","spot_value","perp_unrealized","equity","funding_delta",
                 "friction_delta","turnover_delta","adverse_equity","short_notional")]
            if not all(map(math.isfinite,(cash,spot,perp,eq,fd,fr,turn,adverse,short))):
                raise ValueError("VW_AUDIT_NONFINITE")
            if not near(eq,cash+spot+perp):raise ValueError("VW_AUDIT_EQUITY_IDENTITY")
            if fr<0 or turn<0 or spot<0 or short<0 or adverse<=.05*short or cash<.15*short:
                raise ValueError("VW_AUDIT_SOLVENCY_OR_FRICTION")
            if k%8 and fd!=0:raise ValueError("VW_AUDIT_FUNDING_CLOCK")
            hwm=max(hwm,eq);dd=min(dd,eq/hwm-1);adverse_dd=min(adverse_dd,adverse/hwm-1)
            fees+=fr;funding+=fd;turnover+=turn;closed+=int(r["trades_closed"])
        if not near(float(group[-1]["cash"]),float(group[-1]["equity"])):raise ValueError("VW_AUDIT_FINAL_FLAT")
        checks=(("final_equity",float(group[-1]["equity"])),
                ("2025_net_return",float(group[-1]["equity"])/10000-1),
                ("max_hourly_drawdown",dd),("max_adverse_drawdown",adverse_dd),
                ("funding_net",funding),("fees_and_slippage",fees),("turnover",turnover))
        for key,val in checks:
            if not near(float(scenario[key]),val):raise ValueError("VW_AUDIT_METRIC_"+key)
        if closed!=48 or scenario["trades"]!=48 or scenario["funding_events_checked"]!=4380:
            raise ValueError("VW_AUDIT_TRADE_EVENT_COUNT")
        trades=scenario["monthly_trade_pnl"]
        if len(trades)!=48 or not near(sum(float(t["net_pnl"]) for t in trades),
                                        float(group[-1]["equity"])-10000):
            raise ValueError("VW_AUDIT_TRADE_CASH")
    failures=[s["scenario"] for s in scenarios if s["scenario"].split("/")[0] in
              ("severe","supersevere") and s["2025_net_return"]<=0]
    decision="REJECT_VW_NATIVE_CARRY_GROWTH_FEASIBILITY" if failures else "PASS_VW_EXPLORATORY_2025_NOT_SEVENSLOT_OR_VALIDATED"
    if receipt["gate_failures"]!=failures or receipt["decision"]!=decision:
        raise ValueError("VW_AUDIT_GATE")
    return {"decision":"PASS_VW_INDEPENDENT_HOURLY_REPLAY_NOT_ENGINE",
            "scenarios":6,"hourly_rows":len(records),"cash_mark_identities":len(records),
            "trades_closed":288,"source_event_slots":4380,
            "economic_decision":decision}
def main(folder):
    folder=Path(folder);receipt=json.loads((folder/"vw_result.json").read_text())
    raw=(folder/"vw_hourly_ledger.csv").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=receipt["hourly_ledger_sha256"]:
        raise ValueError("VW_AUDIT_LEDGER_SHA")
    reader=csv.DictReader(raw.decode().splitlines())
    if tuple(reader.fieldnames)!=FIELDS:raise ValueError("VW_AUDIT_HEADER")
    rows=list(reader);result=validate(receipt,rows)
    # Deliberate tamper controls, independent of receipt SHA (tests semantic checks).
    def tamper(index,key,value):
        r=[x.copy() for x in rows];r[index][key]=value
        try:validate(receipt,r)
        except ValueError:return True
        return False
    controls=(tamper(0,"cash",str(float(rows[0]["cash"])+1)),
              tamper(1,"utc_ms",str(START)),
              tamper(0,"friction_delta","-1"),
              tamper(8759,"equity",str(float(rows[8759]["equity"])+1)))
    if not all(controls):raise ValueError("VW_AUDIT_TAMPER_ESCAPE")
    result["tamper_controls_rejected"]=sum(controls)
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main(sys.argv[1])
