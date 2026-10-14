"""V99 R106 new forward epoch DATA_ONLY gate, fully segregated from bad legacy.

Structural admission is NOT live-source authentication, authorization to
publish, portfolio optimization, or financial validation. The old epoch
remains byte-for-byte immutable and frozen in an archived Git blob.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

TRACKS=("r98","f1","f3","f7","f12")
ZERO=Decimal("0.00")
INITIAL=Decimal("10000.00")
CENT=Decimal("0.01")

def parse_utc(value):
    if not isinstance(value,str):
        raise ValueError("explicit UTC required")
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None or t.utcoffset()!=timedelta(0):
        raise ValueError("only explicit UTC timestamps allowed")
    return t.astimezone(timezone.utc)

def cents(value):
    if isinstance(value,bool) or value is None:
        raise ValueError("invalid monetary amount")
    try:
        a=Decimal(str(value))
        if not a.is_finite() or a.quantize(CENT)!=a:
            raise ValueError("non-finite or sub-cent amount")
        return a
    except (TypeError,InvalidOperation) as exc:
        raise ValueError("invalid decimal amount") from exc

def verify(legacy_raw:bytes, new:dict, receipt_raw:bytes) -> dict:
    if not isinstance(legacy_raw,bytes) or not isinstance(receipt_raw,bytes):
        raise ValueError("original source bytes required")
    if not isinstance(new,dict) or new.get("version")!="v99-r106-forward-epoch-v2":
        raise ValueError("new separate versioned epoch required")
    if new.get("mode")!="PAPER_ONLY" or new.get("real_orders_enabled") is not False:
        raise ValueError("simulation only; never submit exchange orders")
    old_sha=hashlib.sha256(legacy_raw).hexdigest()
    if new.get("old_immutable_paper_sha256")!=old_sha:
        raise ValueError("immutable legacy paper anchor mismatch")
    try:
        legacy=json.loads(legacy_raw)
        if legacy.get("mode")!="PAPER_ONLY" or legacy.get("real_orders_enabled") is not False:
            raise ValueError("legacy paper-only mode required")
        if set(legacy.get("variants",{}))!=set(TRACKS):
            raise ValueError("legacy five variants required")
        old_latest=parse_utc(legacy["latest_data_timestamp"])
        if parse_utc(legacy["paper_start_after_timestamp"])>=old_latest:
            raise ValueError("legacy boundary invalid")
    except (KeyError,TypeError,ValueError) as exc:
        raise ValueError("invalid legacy historical anchor") from exc
    start=parse_utc(new.get("new_forward_start_utc"))
    if start<=old_latest or start.minute or start.second or start.microsecond:
        raise ValueError("new epoch must begin strictly after old and on UTC hour")

    expected=hashlib.sha256(receipt_raw).hexdigest()
    if new.get("first_source_payload_sha256")!=expected:
        raise ValueError("first-party raw receipt hash mismatch")
    received=parse_utc(new.get("first_source_received_utc"))
    safe=received.replace(minute=0,second=0,microsecond=0)+timedelta(hours=2)
    if start<safe:
        raise ValueError("causal t-1 source-eligibility violation")
    if new.get("first_source_url") != "https://fapi.binance.com/fapi/v1/exchangeInfo":
        raise ValueError("verified first-party endpoint identifier required")
    def distinct_pairs(pairs):
        obj={}
        for k,v in pairs:
            if k in obj: raise ValueError("duplicate source field")
            obj[k]=v
        return obj
    def fail_constant(x):
        raise ValueError("non-finite source payload")
    try:
        exchange=json.loads(receipt_raw, object_pairs_hook=distinct_pairs,
                            parse_constant=fail_constant)
    except (TypeError,ValueError) as exc:
        raise ValueError("malformed first-party raw receipt") from exc
    if not isinstance(exchange,dict) or not isinstance(exchange.get("symbols"),list):
        raise ValueError("first-party exchangeInfo shape required")
    server_time=exchange.get("serverTime")
    if type(server_time) is not int or abs(server_time-int(received.timestamp()*1000))>60000:
        raise ValueError("first-party server clock not consistent with receipt")
    # Binance-provided onboardDate is NOT proof of historical first seen;
    # all admissible symbols start no earlier than this prospective receipt.
    active={r.get("symbol") for r in exchange["symbols"] if isinstance(r,dict) and
            r.get("quoteAsset")=="USDT" and r.get("contractType")=="PERPETUAL" and
            r.get("status")=="TRADING"}
    if not {"BTCUSDT","ETHUSDT"}.issubset(active):
        raise ValueError("expected original core symbols not in as-of observation")

    engines=new.get("variants")
    if not isinstance(engines,dict) or set(engines)!=set(TRACKS):
        raise ValueError("exactly five preregistered variants required")
    summary={}
    for name in TRACKS:
        track=engines[name]
        if track.get("real_orders_enabled") is not False:
            raise ValueError(name+": real orders forbidden")
        if cents(track.get("initial_capital_brl"))!=INITIAL:
            raise ValueError(name+": do not inherit legacy PnL/capital")
        curve=track.get("hourly_equity_and_pnl")
        if not isinstance(curve,list) or not curve:
            raise ValueError(name+": missing complete hourly journal")
        operations=track.get("operations")
        if not isinstance(operations,list):
            raise ValueError(name+": missing uncapped operations")
        if track.get("operations_capped") is not False or track.get("operation_journal_complete") is not True:
            raise ValueError(name+": journal completeness not asserted")
        required=("timestamp","capital_brl","gross_result_brl","fees_brl",
                  "funding_result_brl","transfer_result_brl","net_result_brl")
        previous_time,previous_cap=None,None
        for i,row in enumerate(curve):
            if not isinstance(row,dict) or not all(x in row for x in required):
                raise ValueError(name+": incomplete gross-fee-funding-transfer ledger")
            t=parse_utc(row["timestamp"])
            if t.minute or t.second or t.microsecond:
                raise ValueError(name+": nonhourly timestamp")
            if i==0 and t!=start:
                raise ValueError(name+": epoch baseline must start at new boundary")
            if previous_time is not None and t-previous_time!=timedelta(hours=1):
                raise ValueError(name+": gap or revision in hourly sequence")
            cap,gross,fees,funding,transfer,net=(
                cents(row[k]) for k in required[1:])
            if fees<ZERO:
                raise ValueError(name+": fees must be nonnegative")
            if gross-fees+funding+transfer!=net:
                raise ValueError(name+": PnL accounting identity broken")
            if i==0:
                if cap!=INITIAL or any(x!=ZERO for x in (gross,fees,funding,transfer,net)):
                    raise ValueError(name+": start a NEW independent zero-PnL baseline")
            elif cap-previous_cap!=net:
                raise ValueError(name+": equity != previous + fully accounted net PnL")
            previous_time,previous_cap=t,cap

        last_key=None
        seen=set()
        for op in operations:
            if not isinstance(op,dict) or not isinstance(op.get("symbol"),str) or not op["symbol"]:
                raise ValueError(name+": invalid operation event")
            t=parse_utc(op["timestamp"])
            if t<=start or t>previous_time:
                raise ValueError(name+": operation outside new epoch")
            key=(t,op["symbol"])
            if (last_key is not None and t<last_key[0]) or key in seen:
                raise ValueError(name+": reordered or duplicate operation")
            seen.add(key)
            last_key=key

        summary[name]={"hours":len(curve),"operations":len(operations),
                       "last_utc":previous_time.isoformat(),
                       "last_simulated_capital_brl":str(previous_cap)}
    return {
        "status":"STRUCTURE_PASS_QUARANTINE_PENDING_VERIFIED_SOURCE",
        "old_paper_sha256":old_sha,
        "old_latest_utc":old_latest.isoformat(),
        "new_start_utc":start.isoformat(),
        "first_source_received_utc":received.isoformat(),
        "first_source_payload_sha256":expected,
        "first_eligible_utc":safe.isoformat(),
        "separate_forward_epoch":True,
        "old_published_data_mutated":False,
        "source_first_party_authenticated_independently":False,
        "full_hourly_accounting_structurally_passed":True,
        "holdout_accessed":False,
        "publication_authorized":False,
        "promotion_authorized":False,
        "economic_trials":0,
        "variants":summary,
    }

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--old",type=Path,required=True)
    ap.add_argument("--candidate",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    report=verify(args.old.read_bytes(),json.loads(args.candidate.read_text()),
                  args.receipt.read_bytes())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"publication_authorized":False,
                      "promotion_authorized":False},sort_keys=True))

if __name__=="__main__":
    main()
