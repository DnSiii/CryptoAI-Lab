# V99 I1 — preregistered stale replacement gate (2026-10-26 12:xx BRT)

## Predeclared defect and invariant
The original-source signal × option-book join currently chooses the latest quote **after** restricting to 5-minute fresh event timestamps. That can preserve an older eligible quote when a newer arrived update for the **same contract** carries a stale exchange event clock. The independent oracle uses the same mistaken prefilter, so agreement alone cannot falsify this failure. This is a SOURCE-ONLY execution-readiness false-positive risk, not an alpha experiment.

For each decision and exact contract symbol, first select the **last physically received predecision update**, ordered by `local_timestamp`, with capture order resolving ties. Do not prefilter by event freshness before this selection. Then require that selected update has valid `event <= arrival < decision`, event and arrival no older than 5 minutes, positive uncrossed BBO and sizes, eligible same expiry and synchronized <=1 second event/arrival skew. A newer malformed/crossed/stale event update **revokes** an older valid quote; a future-arrival update cannot revoke an earlier decision. Never fall back to an older quote for the same symbol. This is a source-only gate and does not certify a fill.

## Fixed tests and execution
Before touching code: deterministic positive two-leg quote; latest crossed update; latest stale event update with fresh arrival (must veto); future-arrival update (must not veto); other-symbol update (must not veto); no second distinct strike; independent oracle agrees on each. Execute these in GitHub Actions and rerun the original 182 signal/4,000-row original Deribit source join and independent byte replay. No fabricated market PnL, no retuning of I1, no validation/holdout access. Reject/preserve any unexpected discrepancy rather than changing expected original counts. Document exact CI ID, outcome and limitations. Preserve V16/V99 Frozen, champion, paper, orders and public returns.

## Economic gate unchanged
Historical 2021-12-09..2023-09-30 original BTC/ETH option BBO/size with both clocks for complete entry/holding/exit lifecycles, licensed bytes, native lot/fee/margin/settlement receipts remain externally missing. The gate cannot promote the motor. **SOURCE_ONLY/HOLD — NO PROMOTION.**
