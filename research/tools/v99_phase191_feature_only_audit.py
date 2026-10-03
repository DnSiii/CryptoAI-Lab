#!/usr/bin/env python3
"""Phase191 DATA_ONLY causal feature audit.

Consumes a decoded immutable-event JSON file only. No price/PnL/regime/benchmark/
holdout inputs. Builds block-level issuer-native net flow and a strict t-1 feature,
then reports temporal coverage, missingness, concentration and tails without any
outcome-conditioned selection.

Input JSON: list of objects accepted by Event in v99_phase191_event_semantics_guard.
"""
from __future__ import annotations
import argparse,json,math
from collections import Counter,defaultdict
from pathlib import Path
from v99_phase191_event_semantics_guard import Event,USDC,USDT,validate

WINDOWS=((17000000,17000199),(18000000,18000199),(19000000,19000199))

def signed(e):
    t=e.token.lower()
    if t==USDC and e.kind=="Mint": return e.amount
    if t==USDC and e.kind=="Burn": return -e.amount
    if t==USDT and e.kind=="Issue": return e.amount
    if t==USDT and e.kind=="Redeem": return -e.amount
    return 0

def q(xs,q):
    if not xs:return None
    ys=sorted(xs); i=min(len(ys)-1,max(0,math.ceil(q*len(ys))-1)); return ys[i]

def audit(events):
    events=sorted(events,key=lambda e:(e.block_number,e.log_index))
    validate(events)
    by_block=defaultdict(int); by_token=Counter(); by_kind=Counter(); by_tx=Counter()
    for e in events:
        d=signed(e); by_block[e.block_number]+=d; by_token[e.token.lower()]+=abs(d); by_kind[e.kind]+=1; by_tx[e.tx_hash.lower()]+=abs(d)
    rows=[]
    for lo,hi in WINDOWS:
        running=0; feats=[]; deltas=[]; active=0
        # Strict t-1: feature for b is accumulated flow through b-1 only.
        for b in range(lo,hi+1):
            feats.append(running); d=by_block.get(b,0); deltas.append(d); active+=int(d!=0); running+=d
        absd=[abs(x) for x in deltas]
        rows.append({"from":lo,"to":hi,"blocks":hi-lo+1,"feature_missing":0,
                     "active_flow_blocks":active,"active_fraction":active/(hi-lo+1),
                     "abs_delta_p50":q(absd,.50),"abs_delta_p90":q(absd,.90),"abs_delta_p99":q(absd,.99),
                     "max_abs_delta":max(absd),"ending_net":running,"tminus1_first":feats[0],"tminus1_last":feats[-1]})
    total=sum(by_tx.values()); top=sorted(by_tx.values(),reverse=True)
    return {"phase":191,"scope":"DATA_ONLY_FEATURE_AUDIT","economic_trials":0,
            "events":len(events),"windows":rows,"event_kind_counts":dict(sorted(by_kind.items())),
            "abs_flow_by_token":dict(sorted(by_token.items())),
            "tx_abs_flow_top1_share":(top[0]/total if total else 0),
            "tx_abs_flow_top5_share":(sum(top[:5])/total if total else 0)}

def self_test():
    h=lambda c:"0x"+c*64; tx=lambda c:"0x"+c*64
    ev=[Event(USDT,"Issue",10,17000000,h("1"),tx("4"),0,1),Event(USDC,"Mint",20,17000001,h("2"),tx("5"),0,2)]
    o=audit(ev); w=o["windows"][0]
    assert w["tminus1_first"]==0 and w["active_flow_blocks"]==2 and w["feature_missing"]==0
    assert o["economic_trials"]==0

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--events");ap.add_argument("--self-test",action="store_true");a=ap.parse_args()
    if a.self_test:self_test();print("PASS: Phase191 feature-only t-1/missingness/concentration audit");return
    if not a.events:raise SystemExit("--events required unless --self-test")
    raw=json.loads(Path(a.events).read_text()); events=[Event(**x) for x in raw]
    print(json.dumps(audit(events),sort_keys=True,separators=(",",":")))
if __name__=="__main__":main()
