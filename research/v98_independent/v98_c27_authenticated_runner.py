"""C27 Clean-4 causal two-clock replay. Research only; never paper/live."""
import argparse
import json
import math
from pathlib import Path
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import HOUR_MS, ASSETS
from .v98_composed_c26 import c26_model, c26_allocator, WARMUP
from .v98_c27_two_clock_governor import planned_trim, execute_queued_units
from .v98_c27_gap_envelope import preemptive_asset_cap, preemptive_gross_cap, prove_envelope
from .v98_b0_causal_overlay import governor_multiplier

ASSET_BUFFER=preemptive_asset_cap(.40,.20,.20)
GROSS_BUFFER=preemptive_gross_cap(.90,.20)
prove_envelope(ASSET_BUFFER,GROSS_BUFFER)
SCALES=(1.,2.,4.)

def replay(bars, funding, scale):
    n=len(bars["BTCUSDT"])
    if n!=27048 or any(len(bars[a])!=n for a in ASSETS):
        raise ValueError("C27_INCOMPLETE_CLEAN4")
    for a in ASSETS:
        for row in bars[a]:
            if len(row)!=5 or any(not math.isfinite(float(v)) for v in row):
                raise ValueError("C27_BAD_OHLC")
            o,h,l,c,vol=map(float,row)
            if min(o,h,l,c)<=0 or l>min(o,c) or h<max(o,c) or vol<0:
                raise ValueError("C27_BAD_OHLC")
        if any(not math.isfinite(float(v)) for v in funding[a].values()):
            raise ValueError("C27_BAD_FUNDING")
    equity=peak=10000.
    weights={a:0. for a in ASSETS}
    histories={a:[] for a in ASSETS}
    model,router=c26_model()
    cached=None
    queued={a:0. for a in ASSETS}
    ledger=[]
    max_dd=0.
    # Previous completed opening ledger state; never use the current opening mark
    # to select a same-open strategic order or feed the drawdown governor.
    decision_equity=equity
    decision_peak=peak
    for i in range(n):
        if i:
            previous=dict(weights)
            returns={a:bars[a][i][0]/bars[a][i-1][0]-1 for a in ASSETS}
            gross_by_asset={a:previous[a]*returns[a] for a in ASSETS}
            funding_by_asset={a:-previous[a]*funding[a].get(i,0.) for a in ASSETS}
            gross=sum(gross_by_asset.values())
            carry=sum(funding_by_asset.values())
            factor=1+gross+carry
            if factor<=0 or not math.isfinite(factor):
                raise ValueError("C27_INSOLVENT_MARK")
            equity*=factor
            weights={a:previous[a]*(1+returns[a])/factor for a in ASSETS}
            marked=dict(weights)
            # The queue was calculated at the previous open, never from this open.
            post_queue=execute_queued_units(marked,queued)
            strategic=(i>=WARMUP+1 and (i-(WARMUP+1))%168==0)
            if strategic:
                history={a:tuple(histories[a]) for a in ASSETS}
                cached=model(history)
                router_value=router(history["BTCUSDT"])
                routers={a:router_value for a in ASSETS}
                target=c26_allocator(cached,routers,governor_multiplier(decision_equity,decision_peak))
                # Precommitted gap-envelope buffers; never retuned to realized PnL.
                target={a:max(0.,min(float(target[a]),ASSET_BUFFER)) for a in ASSETS}
                total=sum(target.values())
                if total>GROSS_BUFFER:
                    target={a:target[a]*GROSS_BUFFER/total for a in ASSETS}
                order_type="strategic"
            else:
                target=post_queue
                order_type="safety" if any(queued.values()) else "hold"
            turnover=sum(abs(target[a]-marked[a]) for a in ASSETS)
            cost=turnover*.0006*scale
            if cost>=1 or not math.isfinite(cost):
                raise ValueError("C27_INSOLVENT_COST")
            before_cost=equity
            # Audit includes the pre-fee opening mark in the equity high-water mark.
            # Using only post-fee peaks understates drawdown and breaks reconciliation.
            peak=max(peak,before_cost)
            max_dd=max(max_dd,1-before_cost/peak)
            equity*=1-cost
            # Replay uses target fractions as the post-cost book convention;
            # independent audit must confirm the identical accounting convention.
            weights=dict(target)
            peak=max(peak,equity)
            max_dd=max(max_dd,1-equity/peak)
            # Queue reductions only: the current mark cannot trigger a current fill.
            # The next-open safety queue is based on the PRECOMMITTED buffered
            # limits, not the hard limits.  This is a delayed sell-only order:
            # no fill is permitted at the observation open.
            buffered=planned_trim(weights,asset_cap=ASSET_BUFFER,gross_cap=GROSS_BUFFER)
            queued={a:0. if weights[a]<=1e-12 else max(0.,min(1.,1-buffered[a]/weights[a]))
                    for a in ASSETS}
            ledger.append(dict(index=i,equity=equity,pre_fill_equity=before_cost,
                weights_before_fill=marked,weights_after_fill=dict(weights),
                turnover=turnover,cost_return=cost,drawdown=1-equity/peak,
                gross_return=gross,funding_return=carry,gross_by_asset=gross_by_asset,
                funding_by_asset=funding_by_asset,order_type=order_type,
                queued_next_open_sell_fractions=dict(queued),
                hard_cap_breach_after_fill=(max(weights.values())>.40+1e-10 or sum(weights.values())>.90+1e-10)))
        if i:
            decision_equity=equity
            decision_peak=peak
        for a in ASSETS:
            histories[a].append(bars[a][i][3])
    final_factor=1+sum(weights[a]*(bars[a][-1][3]/bars[a][-1][0]-1) for a in ASSETS)
    if final_factor<=0:
        raise ValueError("C27_INSOLVENT_FINAL")
    equity*=final_factor
    max_dd=max(max_dd,1-equity/max(peak,equity))
    if len(ledger)!=27047:
        raise ValueError("C27_LEDGER_LENGTH")
    return dict(final_equity=equity,max_drawdown=max_dd,total_turnover=sum(e["turnover"] for e in ledger),
                funding_return_sum=sum(e["funding_return"] for e in ledger),hours=n,
                execution="C27_NEXT_OPEN_TWO_CLOCK",last_mark_factor=final_factor),ledger

def run(prices,manifest,funding):
    data=load(prices,manifest,funding)
    indexed={a:{} for a in ASSETS}
    for a in ASSETS:
        for stamp,rate in data["funding"][a].items():
            offset=stamp-START_MS
            if offset%HOUR_MS or not 0<=offset<data["hours"]*HOUR_MS:
                raise ValueError("C27_INVALID_FUNDING_STAMP")
            indexed[a][offset//HOUR_MS]=rate
    results={}
    ledgers={}
    for scale in SCALES:
        summary,rows=replay(data["bars"],indexed,scale)
        key=str(int(scale))+"x"
        results[key]=summary
        ledgers[key]=rows
    return dict(status="C27_TRAINING_ONLY_NO_PROMOTION",source="AUTHENTICATED_CLEAN4",
        holdout_accessed=False,price_manifest_sha256=data["price_manifest_sha256"],
        funding_manifest_sha256=data["funding_manifest_sha256"],
        buffer_asset=ASSET_BUFFER,buffer_gross=GROSS_BUFFER,results=results,ledgers=ledgers)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--export-training-checkpoints",action="store_true",help="Export UNATTESTED continuation checkpoints for each cost scenario")
    for name in ("prices","manifest","funding","output"):
        p.add_argument("--"+name,type=Path,required=True)
    args=p.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("C27_NAMESPACE_REQUIRED")
    result=run(args.prices,args.manifest,args.funding)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    ledgers=result.pop("ledgers")
    if args.export_training_checkpoints:
        # Re-load through the same authenticated Clean-4 reader, never from a
        # fabricated or truncated ledger. This is NOT independent attestation.
        from .v98_c27_training_checkpoint import write_checkpoint
        authenticated=load(args.prices,args.manifest,args.funding)
        for key,rows in ledgers.items():
            cp=args.output.with_name(args.output.stem+"_"+key+"_checkpoint.json")
            receipt=write_checkpoint(authenticated["bars"],rows,cp)
            result.setdefault("training_checkpoint_receipts",{})[key]=receipt
    for key,rows in ledgers.items():
        with args.output.with_name(args.output.stem+"_"+key+"_ledger.jsonl").open("w") as out:
            for row in rows:
                out.write(json.dumps(row,sort_keys=True,allow_nan=False)+"\n")
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
