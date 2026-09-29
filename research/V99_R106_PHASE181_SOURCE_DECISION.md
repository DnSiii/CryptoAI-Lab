# V99 R106 — Phase181 source decision

Date: 2026-09-29
Decision: REJECTED AT DATA GATE / NO PNL INSPECTED

## Evidence harvested

The Phase181 invariant CI at commit `fb479a3d778afb695663d09c6b3e8864c96d7441` completed successfully: four deterministic gate tests passed under Python 3.11 with `PYTHONHASHSEED=0`.

That success validates only the gate implementation; it does not admit the hypothesis to alpha evaluation.

## Independent source audit

The required signal is historical Ethereum beacon missed-slot stress. A missed slot is an absence and is only causally known when a later block is actually observed. Therefore scheduled slot time and a present-day finalized explorer label are descriptive timestamps, not point-in-time market availability timestamps.

Sources inspected without PnL:

- beaconcha.in exposes deep historical slot status/root/time, including missed/orphaned slots, but the displayed slot time is protocol schedule time and does not establish when a historical observer first saw the subsequent canonical block.
- EthPandaOps Xatu explicitly provides beacon event `event.date_time` / propagation timing from sentries and is semantically suitable for point-in-time arrival research. However its public documentation/examples center on 2024 event-stream partitions; the public event-stream evidence found does not establish full immutable coverage of the required TRAIN beginning 2021-12-01 plus 2048-slot pre-roll and ending before 2024-01-18.
- Present-day canonical/finalized history can establish descriptive chain structure, but using it to manufacture historical `known_at` would reconstruct future canonicality.

No single inspected source therefore proves both full TRAIN coverage and historical point-in-time observation provenance under the preregistered gate.

## Failure mechanism

This is a provenance failure, not a performance failure. Allowing any of the following would weaken the preregistration and is forbidden:

1. use protocol scheduled time as `known_at`;
2. use current finalized explorer status as if it were historically available;
3. stitch observers/providers after inspecting coverage or alpha;
4. backfill missing arrival timestamps from block/slot time;
5. shorten TRAIN to the Xatu era;
6. inspect PnL to decide whether the provenance compromise is worthwhile.

## Decision

Phase181 is **REJECTED at the DATA gate**. No alpha, PnL, benchmark, regime, severe-cost, supersevere-cost or holdout evaluation is authorized for this phase.

V16 Frozen and V99 Frozen remain untouched. Holdout remains untouched.
