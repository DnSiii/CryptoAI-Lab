# V99 R106 — Phase181 DATA semantics audit

Date: 2026-09-29
Status: DATA-ONLY / NO PNL

## Independent protocol audit

Phase181 remains scientifically plausible, but a missed slot is not a stored on-chain object. It is an absence inferred from two subsequently observed canonical beacon blocks whose slot numbers differ by more than one. Therefore a source that merely labels historical slots as `missed` is not sufficient provenance for causal market alignment.

Protocol facts used by the gate:
- beacon blocks carry `slot` and `parent_root` and block processing requires a newer slot and matching parent;
- slots are protocol-scheduled, so missing integer slot identities between canonical observations are descriptive gaps;
- canonicality/availability at market time must not be reconstructed using a later finalized view;
- pre-Merge beacon history is valid for slot-gap features, but execution-payload fields must never be required there.

## Fail-closed availability rule

For canonical observed blocks B_prev at slot s0 and B_next at slot s1>s0, slots s0+1..s1-1 may be marked descriptively absent only with `known_at = observed_at(B_next)`. A feature row may consume those statuses only after the existing additional market-bar t-1 lag. `slot scheduled time` is never accepted as `known_at` for a miss.

Historical explorer labels without point-in-time observation provenance can pass descriptive coverage/integrity checks but cannot by themselves pass the market-time causality gate.

## Source-quality audit requirements

A provider is admissible only if, without PnL inspection, it demonstrates:
1. full TRAIN + >=2048-slot pre-roll coverage;
2. canonical block root, parent root and slot identity for observed blocks;
3. a documented point-in-time observation timestamp or a conservative equivalent that does not depend on future canonicality;
4. deterministic export/retrieval semantics and immutable provenance hash;
5. no provider stitching selected after seeing gaps or alpha;
6. no post-2024-01-18 row used to infer TRAIN canonicality.

Ethereum.org lists beacon explorers and notes that slot data include proposed/missed status, slot number, time, block root and parent root. That is useful for descriptive discovery, not proof of historical point-in-time availability. Consensus clients are only required to serve a bounded recent block-request range, so a present-day public node cannot be assumed to provide the full historical archive.

## Decision

Do not reject Phase181 yet. First implement a deterministic source manifest/gate that separates (A) descriptive canonical slot coverage from (B) point-in-time market availability. Alpha/PnL remains forbidden unless both pass unchanged.
