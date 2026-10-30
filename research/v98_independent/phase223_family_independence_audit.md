# V98 Independent — Phase223 family-independence audit

## Decision
**DUPLICATE_FAMILY — NOT ELIGIBLE FOR PROMOTION OR SELECTION.**

This audit was performed while the first Phase223 workflow was queued/running and before harvesting its result. Phase223 must not be treated as a scientifically new hypothesis because Phase216 already tested the same core economic mechanism: fade large idiosyncratic hourly shocks over short holds under the same 2023/2024/2025 training-fold discipline and realistic cost/funding framework.

## Comparison with Phase216
Phase216 preregistered idiosyncratic hourly shock mean reversion after BTC adjustment, with z-thresholds, 3h/6h holds, gross exposure <=1, PIT funding, base/severe/supersevere costs, and the same mechanical fold gate. Its post-mortem is final: `REJECT_FAMILY_NO_RESCUE`, zero coherent specs, deterministic SHA `a536fa50f6034a0a065bb03fa28d1ade4d5ca6e2891636f80d9286f4ffc0632d`, holdout unopened.

Phase223 changes implementation details (raw-return sigma normalization over 168/336h, thresholds 2.5/3.5, holds 2h/6h, and a BTC co-shock veto), but still asks the same substantive question: whether an extreme idiosyncratic hourly shock should be faded over the next few hours. Those changes are neighborhood/rescue variations after Phase216 rejection, not a sufficiently orthogonal family.

## Governance consequence
- Any Phase223 output may be retained only as a reproducibility/infrastructure diagnostic.
- It cannot promote a V98 candidate, reopen Phase216, justify parameter rescue, or influence champion selection.
- No 2026+ holdout may be opened.
- No V99 information may be used.
- The next research family must be orthogonal to Phase216/223 and to the recent rejected families; preregistration must explicitly include a duplicate-family check against prior V98 work before execution.

## Integrity note
This audit does not alter Phase223 parameters after evidence; it removes selection eligibility based on prior-family provenance. The decision therefore strengthens, rather than weakens, anti-overfit discipline.
