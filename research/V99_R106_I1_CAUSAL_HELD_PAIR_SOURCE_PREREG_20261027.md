# V99 I1 — causal Monday entry plus exact held-contract source gate (2026-10-27 18:50 BRT)

**Precommitted before implementation. SOURCE_ONLY/HOLD — NO PROMOTION.** No strategy retune or economic backtest.

## Discovered causal false positive
The 661-day continuity gate can report a positive same-contract lifecycle even if its first available quote arrives **after** the fixed Monday 00:00 UTC decision. The existing 1/180 positive fixture inserts all contract quotes on Monday at 00:00:03/04 UTC, after the decision. Its "same-contract" count is a weak pre-expiry daily presence screen, **not causal entry readiness**. The native quote/vertical model already requires both legs received before decision, at most five minutes old, with two-leg arrival and venue skew <=1 second.

## Fixed deterministic source-only correction
- Preserve the existing 180-week weak daily-presence and same-contract pre-expiry counters unchanged, and legacy schema unchanged.
- Add a distinct fixed-tenor `asset_weeks_with_causal_entry_and_same_contract_pair_presence` count. Only qualify when the **same two original option symbols**, same BTC/ETH and same 28–35-day expiry (<2023-10-01), each have a last valid original Sunday quote within [Monday 00:00 - 300 seconds, Monday 00:00), with venue event <= arrival, venue event no older than 300 seconds, both positive-size uncrossed two-sided books, and venue/arrival two-leg skew <= 1000 milliseconds. These same exact symbols must each be present on every Monday-through-pre-expiry day per the already preregistered weak continuity masks.
- No invented entry fills or guaranteed size, strike/moneyness, margin, fees, index, expiry delivery or profit. Even positive source count remains **necessary but not sufficient** for economic TRAIN.
- Independent oracle must re-read original daily bytes, reconstruct latest Sunday quotes and exact-contract masks, recompute counter and reject a forged report.
- Adversarial synthetic controls: Monday-after-decision-only same-contract fixture yields 1/180 continuity but **0/180 causal**; a Sunday 23:59:59 synchronized pair plus complete Monday-through-expiry original daily fixture yields 1/180 causal; a >1s two-leg skew or stale Sunday quotes must fail. The original fixture remains visibly synthetic.
- Only TRAIN 2021-12-09..2023-09-30; no validation/holdout, no Frozen, paper, champion, orders, dashboard performance claims or model promotion.

**External dependency unchanged:** licensed and independently authenticated BTC/ETH Deribit original historical full quote/size tape with venue+arrival clocks and dated account-specific fees, contract/lot, margin, liquidation and delivery indices.