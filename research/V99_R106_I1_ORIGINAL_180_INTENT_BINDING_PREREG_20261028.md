# V99 I1 — original 182 signals to fixed 180 intent binding (preregistered 2026-10-28 06:xx BRT)

Status: **SOURCE_ONLY/HOLD**. This is a necessary integrity bridge, NOT a trading system, economic TRAIN, or proof of fills.

## Fixed protocol (before implementation)
1. Input must be the already archived ORIGINAL 182-row causal signal JSON, independently reconstructed from original OKX spot and Deribit DVOL artifacts; no synthetic or user-typed signal may count as source authentication.
2. Preserve all 182 ordered original signal observations. Match exactly the original 91-week × BTC/ETH schedule, with strictly fixed fold IDs and one of the three preregistered signals. Use only the 90-week, 180-decision executable schedule from `eligible(True)`; exclude the two right-censored observations without consulting validation/holdout.
3. Output each of 180 **intent** rows (clock, asset, fold, original signal) with **no OPEN/CASH classification**, no price, no hypothetical fill and no PnL. Compute source SHA256 from the original JSON bytes and an independently reproducible SHA256 for canonical intent rows.
4. Compare against any proposed nonfixture 180-row execution decision ledger and fail on any changed signal, shifted/duplicated/missing clock, changed fold, or unsupported action. Positive signals may only be OPEN with separately evidenced quotes/risk or CASH with independently proven quote/risk veto; a self-declared CASH reason is NOT sufficient. The intent audit must not pretend to prove that independent veto.
5. An independent verifier must rebuild the same intents from the original archived JSON, compare source hashes, counts and every row, and falsify a changed signal. This does not certify option tape, dated native fees, margin, fills, settlement or vendor gap coverage.
6. Execute in GitHub Actions using the original archived signal plus original OKX/DVOL artifact reconstruction, no new strategy tuning. Maintain 0 certified lifecycles, NO TRAIN/ROI/PROMOTION/ORDERS, sealed 2023-10-01+ and immutable Frozen/paper/champion.

Expected result is an original-signal-bound 180-row **non-executable intent manifest**, NOT an executable portfolio or a promoted strategy. Historical options provenance remains the external blocker.
