# V99 R106 — Phase177 first-party options-IV source probe

Date: 2026-09-28
Scope: DATA DISCOVERY ONLY. No alpha/PnL/holdout access.

## Sources inspected

### OKX

Official OKX documentation confirms that option mark prices use the Black model and that implied volatility is derived from market data in real time. This establishes the economic meaning of IV, but OKX's historical-data catalogue does not advertise a historical options-IV archive covering the frozen TRAIN. Therefore OKX is not admitted for Phase177.

### Deribit

Deribit first-party material confirms that DVOL launched on 2021-03-31 and is a 30-day annualized implied-volatility index derived from the implied-volatility smile of relevant option expiries. This predates the frozen TRAIN start and is economically orthogonal to the previously exhausted feature families.

Deribit also published first-party material in January 2022 describing historical high-frequency Deribit options data replayed exactly as real-time WebSocket messages via its Tardis partnership, including Q4 2021 and Q1 2022. That is useful contemporaneous evidence that point-in-time options observations existed during the early TRAIN.

But the referenced historical storage/distribution is operated by a data partner, and the evidence inspected does not establish first-party immutable full coverage through 2024-01-18. Under the preregistered gate, this is insufficient for admission.

## Decision

**PHASE177 SOURCE NOT YET ADMITTED.**

Positive evidence:
- DVOL existed before TRAIN;
- DVOL is explicitly implied-volatility based;
- contemporaneous Deribit material demonstrates historical replay of options market messages for part of TRAIN.

Missing evidence:
- first-party deterministic full TRAIN archive or first-party historical DVOL series;
- immutable point-in-time provenance across all temporal folds;
- complete timestamps/schema/hashes for `[2021-12-01, 2024-01-18)`.

No third-party backfill is silently substituted. No TRAIN boundary is shortened. No alpha formula, sign, threshold, expiry, strike, asset, or window has been selected.

## Next deterministic action

Continue searching only for a first-party Deribit historical DVOL/options endpoint or archive with full frozen-TRAIN coverage and publication semantics. If unavailable, reject Phase177 and move to another orthogonal first-party family rather than weakening the source gate.

V16 Frozen and V99 Frozen remain untouched. Holdout remains untouched.
