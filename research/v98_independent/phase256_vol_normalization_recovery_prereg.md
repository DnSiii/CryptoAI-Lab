# V98 Independent Phase256 — Volatility-Normalization Recovery Sleeve

Status: PREREGISTERED BEFORE PHASE256 PNL.

## Architecture role

Phase256 tests a new **Stress/Recovery Sleeve** on top of the frozen Phase252 partial engine.

It is not Phase134/136 downside-jump rebound and not Phase248 de-risking:
- Phase134/136 traded the day immediately after broad downside jumps.
- Phase248 reduced exposure during high-vol downside states.
- Phase256 waits for a completed volatility-stress episode to **normalize and reverse**, then adds temporary long convex exposure.

The structural core and frozen Phase252 Opportunity Sleeve remain unchanged.

## Frozen signal

Use the equal-weight Clean-4 market log-return series.

At each hourly close t:
1. market hourly log return = mean of BTC/ETH/BNB/SOL log returns.
2. rv24(t) = rolling 24h standard deviation of market hourly returns.
3. normal_rv(t) = median rv24 over the prior 720h / 30d, excluding t.
4. market_ret24(t) = 24h market log return ending at t.
5. A STRESS observation occurs when rv24(t) >= 2.0 * normal_rv(t) AND market_ret24(t) < 0.

At each 23:00 UTC decision:
6. A recent stress exists if at least one STRESS observation occurred during the prior 72 completed hours.
7. RECOVERY is true iff recent stress exists AND rv24(t) <= normal_rv(t) AND market_ret24(t) > 0.
8. If RECOVERY: add +0.0625 BTC/ETH/BNB/SOL for the next daily decision interval (+0.25 gross).
9. Otherwise recovery sleeve is flat.
10. No stacking. Frozen Phase252 target remains unchanged underneath.

Integrated gross = Phase252 gross 1.00/1.25 plus at most 0.25 recovery sleeve, cap 1.50.

## Frozen constants

- stress RV window: 24h
- normal RV reference: prior 720h median
- stress multiple: 2.0x
- recent-stress memory: 72h
- recovery direction: market_ret24 > 0
- recovery normalization: rv24 <= normal_rv
- sleeve: +0.0625 per asset
- decision: 23:00 close -> next 00:00 open
- no parameter grid, threshold search, sign flip, asset subset, stop or rescue

## Frozen comparator

Exact Phase252 partial architecture under identical data, costs and funding.

## Promotion gate

Phase256 becomes **VOL_NORMALIZATION_RECOVERY_CANDIDATE** only if all are true:
1. BASE integrated return > Phase252 by >=3% relative.
2. BASE CAGR > Phase252 CAGR.
3. BASE PF >= Phase252 PF.
4. BASE DD not worse by >3pp.
5. BASE worst day >= -20%.
6. marginal fold return positive in at least 2/3 folds.
7. no fold underperforms Phase252 by >5pp.
8. SEVERE return > Phase252 SEVERE.
9. SUPERSEVERE return > Phase252 SUPERSEVERE.
10. at least 10 recovery decision-days in training.
11. no ruin.
12. max open gross <=1.500000001.
13. max asset contribution share <=70%.
14. top-10 absolute daily-return concentration <=45%.

Failure => REJECT_VOL_NORMALIZATION_RECOVERY_NO_RESCUE for this exact rule. Validation/holdout remain locked.
