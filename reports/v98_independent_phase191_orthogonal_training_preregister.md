# V98 Independent — Phase191 preregistration

Status: **TRAINING ONLY — PREREGISTERED BEFORE RESULTS**.

## Hypothesis

Test a scientifically distinct **low-volatility cross-sectional trend persistence** family. Phase190 tested continuation conditional on volatility shocks; Phase191 instead asks whether persistent relative trend has positive expectancy specifically when realized volatility is subdued, where turnover and adverse selection may be lower.

No Phase190 parameter rescue, sign flip, validation feedback, V99 information, or holdout information may be used.

## Frozen research window

- Training/evaluation for selection: 2023-01-01 through 2025-12-31 only.
- Chronological folds: calendar 2023, 2024, 2025; all must be reported separately.
- Validation: forbidden in Phase191.
- Final holdout: forbidden and remains closed.
- Assets: the existing five canonical V98 Independent assets only.

## Causal signal definition

At each decision timestamp use only information available at or before that timestamp. Compute each asset's trailing 72h return and trailing 24h realized volatility. Rank the five assets cross-sectionally by 72h return. Trade only when the cross-sectional median 24h realized volatility is below its own trailing reference quantile, calculated from past observations only.

When enabled, hold a dollar-neutral long/short portfolio: long the strongest trend asset and short the weakest trend asset, equal absolute weights, subject to the existing V98 gross/risk invariants. No future return may enter feature construction or eligibility.

## Closed structural grid

Exactly 8 specifications:

- volatility reference window: 336h or 720h;
- low-vol quantile: 0.35 or 0.50;
- rebalance/holding interval: 12h or 24h.

The trend lookback is fixed at 72h. No other parameter may be searched in Phase191.

## Required economics and diagnostics

For every specification report base, severe, and supersevere realistic transaction-cost/funding cases; total return/CAGR; max drawdown; daily Profit Factor; payoff; win rate; positive/negative days; turnover; chronological fold metrics; bull/bear/sideways attribution; asset contribution; mean/p95 top-1 concentration; top/bottom-10 tail contribution; max gross and max absolute net exposure.

## Training promotion gate

A candidate may advance only if, without discretionary rescue:

1. base, severe, and supersevere total return > 0 and PF > 1.0;
2. base MDD <= 35%, severe MDD <= 40%, supersevere MDD <= 45%;
3. each chronological fold has positive total return and PF > 1.0 in base costs;
4. at least two of bull/bear/sideways have non-negative approximate return;
5. mean top-1 concentration <= 0.60;
6. top10 positive and bottom10 negative contribution shares each < 0.50;
7. gross/net exposure invariants hold and no ruin occurs;
8. a second complete run is byte-identical.

If none passes: `REJECT_FAMILY_NO_RESCUE`. If one or more pass, freeze the candidate using a deterministic robustness-first ordering established before inspecting validation; validation still must not be opened inside Phase191.

## Reproducibility and isolation

Workflow must assert branch `research/v98-independent-zero`, rebuild/use training-only V98 canonical data with max timestamp < 2026-01-01, run twice byte-identically, and commit only V98 Independent namespaced output. V16 Frozen, V99 Frozen/research/workflows/reports/paper state are prohibited.

Final holdout remains closed.