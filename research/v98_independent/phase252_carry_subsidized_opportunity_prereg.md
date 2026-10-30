# V98 Independent Phase252 — Carry-Subsidized Opportunity Sleeve

Status: PREREGISTERED BEFORE PHASE252 PNL.

## Architecture role

Phase252 returns to the **Opportunity Sleeve** slot with a mechanism distinct from Phase247 breakout timing and from the rejected Phase250/251 funding reallocation family.

The structural Clean-4 Growth Core remains unchanged:
+0.25 BTCUSDT, ETHUSDT, BNBUSDT and SOLUSDT continuously, gross 1.00.

Phase252 never reduces or reallocates that core. Funding is used only as a financing-cost condition for temporary extra structural-beta exposure.

## Frozen hypothesis

When aggregate realized perpetual funding is non-positive, additional long market exposure is economically subsidized rather than penalized by carry.

At each 23:00 UTC close(t):

1. For each Clean-4 asset, sum realized funding rates over the previous **168 hours / 7 days**.
2. Compute the simple cross-asset mean of those four trailing sums.
3. Opportunity ON iff the mean trailing funding sum is **<= 0**.
4. Core target remains +0.25 per asset at all times.
5. Opportunity sleeve when ON = +0.0625 per asset = +0.25 extra gross.
6. Combined target when ON = +0.3125 per asset, gross 1.25.
7. Combined target when OFF = +0.25 per asset, gross 1.00.
8. Decision after 23:00 executes at next 00:00 open and persists to the next daily decision.

Zero is the economic break-even sign and is not fitted to returns.

No alternate funding window, threshold, gross, sleeve size, asset subset, rank, price filter, momentum filter, breakout filter, regime filter, stop, hold search or post-result rescue.

## Distinction from prior funding families

- no long/short funding-carry portfolio;
- no funding-shock reversal;
- no ranking/reallocation among assets;
- no de-risking;
- no price or return signal;
- funding controls only whether the complete structural beta core is temporarily levered from gross 1.00 to 1.25.

## Frozen data / execution

Authenticated Phase243 Clean-4 only; native V98 funding; XRP quarantined.
Training only 2023-2025.
No 2026+, validation, holdout, V14, V15 or V99.

Existing V98 BASE/SEVERE/SUPERSEVERE cost and funding stress tiers remain unchanged.
Combined open-gross cap = 1.25.

## Frozen comparator

Exact equal-weight structural Clean-4 core under identical backtester and cost/funding tiers.

## Opportunity promotion gate

Phase252 becomes **CARRY_SUBSIDIZED_OPPORTUNITY_CANDIDATE** only if all are true:

1. BASE combined return > core BASE return by at least 5% relative.
2. BASE combined CAGR > core CAGR.
3. BASE daily PF >= core PF.
4. BASE max DD is not worse than core by more than 5 percentage points.
5. BASE worst day >= -20%.
6. Marginal calendar return positive in at least 2/3 folds.
7. No calendar fold underperforms core by more than 10 percentage points.
8. SEVERE combined return > core SEVERE return.
9. SUPERSEVERE combined return > core SUPERSEVERE return.
10. No ruin.
11. Max open gross <= 1.250000001.
12. Max absolute asset PnL contribution share <=70%.
13. Top-10 absolute daily-return concentration <=45%.

Failure => REJECT_CARRY_SUBSIDIZED_OPPORTUNITY_NO_RESCUE for this exact 7d / funding<=0 / +0.25 gross sleeve. No validation/holdout.
