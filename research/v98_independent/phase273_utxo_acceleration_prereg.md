# V98 Independent Phase273 — UTXO Growth Acceleration Opportunity Sleeve

Status: **PREREGISTERED BEFORE PHASE273 PNL / BEFORE UTXO-RETURN INSPECTION**.

Execution requires Phase272 == PASS_DATA_ONLY.

## Hypothesis

The Bitcoin UTXO set is a confirmed-chain state variable. Sustained acceleration in UTXO-set growth can proxy expansion of the network's active ownership/settlement footprint. If recent UTXO growth is positive and faster than the immediately preceding period, crypto-wide structural demand may be strengthening.

Phase273 tests this as an additive Opportunity Sleeve on top of frozen Phase252.

## Frozen causal signal

At each daily 23:00 UTC decision on calendar day D, only completed prior-day UTXO observations are admissible.

Define, using exact UTC dates:
- recent_growth(D) = UTXO(D-1) / UTXO(D-31) - 1
- prior_growth(D) = UTXO(D-31) / UTXO(D-61) - 1

ON iff:
1. all three exact observations exist;
2. recent_growth(D) > 0;
3. recent_growth(D) > prior_growth(D).

Otherwise OFF.

No interpolation or forward-fill is allowed. Missing exact dates => OFF for that decision.

## Frozen portfolio action

When ON:
- add +0.0625 to BTCUSDT
- add +0.0625 to ETHUSDT
- add +0.0625 to BNBUSDT
- add +0.0625 to SOLUSDT

Total extra gross = +0.25.
Frozen Phase252 remains unchanged underneath.
Maximum integrated target gross = 1.50.
Decision after 23:00 close executes next 00:00 open.

No alternate growth window, smoothing, threshold, sign flip, asset subset, leverage change, regime conjunction, stop, or post-result rescue.

## Comparator

Exact frozen Phase252 under identical Clean-4 data, funding, execution, and BASE/SEVERE/SUPERSEVERE costs.

## Promotion gate

Phase273 becomes **UTXO_ACCELERATION_OPPORTUNITY_CANDIDATE** only if all are true:

1. BASE integrated return > Phase252 by >=3% relative;
2. BASE CAGR > Phase252 CAGR;
3. BASE daily PF >= Phase252 PF;
4. BASE max DD not worse by >5 percentage points versus Phase252;
5. BASE worst day >= -20%;
6. positive marginal return versus Phase252 in at least 2/3 calendar folds;
7. no fold underperforms Phase252 by >10 percentage points;
8. SEVERE return > Phase252 SEVERE;
9. SUPERSEVERE return > Phase252 SUPERSEVERE;
10. >=60 ON decision-days in training;
11. no ruin;
12. max open gross <=1.500000001;
13. max absolute asset contribution share <=70%;
14. top-10 absolute daily-return concentration <=45%.

Failure => **REJECT_UTXO_ACCELERATION_NO_RESCUE**.

No validation or holdout access. V14/V15/V99 excluded.
