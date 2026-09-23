# V99 R106 Phase120 — independent pre-result audit (2026-09-23)

Scope: code/protocol audit while the train-only workflow is still running. No Phase120 PnL/result and no holdout market values were inspected.

## Confirmed invariants
- `TRAIN_END = 2024-01-18 00:00:00 UTC`; every scheduled archive date is asserted `< TRAIN_END`.
- Parsed trade timestamps at or beyond `TRAIN_END` raise immediately.
- Each daily archive is checked against the official SHA256 CHECKSUM and ZIP CRC before use.
- Missing archives from Phase118 remain omitted; there is no future fill or synthetic replacement.
- Feature direction is continuation and the entire robust cross-sectional signal is shifted one hour (`t-1`) before target construction.
- Severe-cost execution uses the canonical R106 harness; temporal-fold stability is delegated to the existing Phase47 diagnostic.
- Phase120 has no parameter/sign/horizon grid in the implementation.
- Workflow snapshots files matching V16/V99 frozen patterns before execution and verifies byte hashes after execution.

## Independent executable-universe risk found before result
The current implementation chooses 12 symbols by the preregistered Phase118 compressed-byte resource rule, computes the robust cross-section over those 12, then writes targets only for symbols also present in the canonical executable data columns. It does not currently assert that all 12 selected symbols are executable.

This is not evidence about alpha and must not be repaired using Phase120 performance. Decision rule frozen now, before harvest:
1. When Phase120 finishes, record the selected 12 and the executable intersection before interpreting PnL.
2. If fewer than 8 selected symbols are executable, classify the run as an operational/protocol rejection, irrespective of PnL.
3. If at least 8 but fewer than 12 are executable, do not silently treat the nominal 12-asset cross-section as a fully executable portfolio. The exact run may only be interpreted after explicitly reporting the executable count and gross actually deployed; no substitution of symbols is allowed after seeing PnL.
4. Phase121 therefore preregisters the stricter executable-intersection invariant in advance.

## Frozen-asset continuity audit
Repository compare from Phase120 implementation commit `d06099d45cdf16508d1ce8a8b71491927c704331` through the Phase121 preregistration commit shows changes only to the Phase120 workflow/script and the Phase121 preregistration document. No V16 Frozen or V99 Frozen path was modified in that interval.

## Holdout decision
Holdout remains sealed. Phase120 cannot reach holdout from this train gate. A train PASS only permits freezing the exact specification for supersevere cost, regime, benchmark-envelope and reproducibility gates first.
