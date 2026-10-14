# V98 Independent Phase254 — Shadow-Equity Opportunity Risk Governor

Status: PREREGISTERED BEFORE PHASE254 PNL.

## Architecture role

Phase254 tests a scientifically distinct Risk Governor on the frozen Phase252 partial architecture.

Frozen baseline remains unchanged:
- Growth Core primitive: +0.25 BTC/ETH/BNB/SOL continuously.
- Opportunity Sleeve candidate: +0.0625 per asset when the frozen 168h mean realized-funding condition is <= 0.
- Baseline gross = 1.00 or 1.25.

The governor never reduces, reallocates, shorts or otherwise modifies the structural 1.00-gross core. It only suppresses the already-frozen +0.25 Opportunity Sleeve during deep drawdowns of a causal shadow copy of the Phase252 system.

This is distinct from Phase246, which used a market-price drawdown state to replace the entire long core with a short portfolio. Phase254 uses strategy-equity health and only blocks incremental leverage.

## Frozen governor

1. Run a causal shadow copy of frozen Phase252 under the canonical BASE cost/funding tier.
2. At each 23:00 UTC decision after close(t), compute the shadow-equity trailing peak over the previous 90 days / 2160 hours, using only shadow equity known through t.
3. shadow drawdown = shadow_equity(t) / trailing_peak(t) - 1.
4. BLOCK the Opportunity Sleeve iff shadow drawdown <= -20%.
5. While blocked, integrated target = structural core only (+0.25 each, gross 1.00).
6. Otherwise, original Phase252 funding rule applies unchanged and can raise gross to 1.25.
7. Governor never changes sign or asset allocation of the core and never creates new leverage.
8. Decision after 23:00 close(t) executes next 00:00 open.

90d and -20% are frozen conventional local-peak/deep-drawdown risk definitions. No hysteresis, threshold grid, alternate lookback, delay, asset subset, sign change or rescue.

## Frozen comparator

Exact Phase252 architecture under identical data, execution and cost/funding tiers.

## Promotion gate

Phase254 becomes SHADOW_EQUITY_RISK_GOVERNOR_CANDIDATE only if all are true:

1. BASE governed return >= Phase252 BASE return.
2. BASE governed CAGR >= Phase252 CAGR.
3. BASE governed daily PF >= Phase252 PF.
4. BASE max DD improves by at least 3 percentage points versus Phase252.
5. BASE worst day >= Phase252 worst day.
6. Marginal fold return versus Phase252 non-negative in at least 2/3 folds.
7. No fold underperforms Phase252 by more than 5 percentage points.
8. SEVERE governed return >= Phase252 SEVERE return.
9. SUPERSEVERE governed return >= Phase252 SUPERSEVERE return.
10. No ruin.
11. Max open gross <= 1.250000001.
12. Core gross never below 1.00 after 2023 begins.
13. Max asset contribution share <=70%.
14. Top-10 absolute daily-return concentration <=45%.

Risk reduction without preserved/increased compounded wealth is insufficient.

Failure => REJECT_SHADOW_EQUITY_GOVERNOR_NO_RESCUE for this exact 90d/-20% rule. No validation/holdout.
