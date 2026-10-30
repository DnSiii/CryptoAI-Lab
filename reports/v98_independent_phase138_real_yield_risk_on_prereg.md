# V98 Independent Phase138 — Real-Yield Risk-On preregistration

Status: **FROZEN BEFORE DFII10 VALUES / CRYPTO RETURNS / ALPHA / PNL ARE INSPECTED TOGETHER**.

## Causal economic hypothesis

Lower/falling U.S. 10-year real yields reduce the discount-rate headwind on long-duration/risk assets. The single frozen hypothesis is therefore: when the most recently available DFII10 observation is below its value 20 available observations earlier, V98 holds a modest equal-weight long basket of the five canonical crypto assets; otherwise it is flat.

Phase137 passed the independent data-only gate without exposing yield values or computing returns/correlations/PnL. No Phase137 descriptive statistic is used to choose this rule.

## Frozen signal and execution

- Macro source: FRED `DFII10`, exactly the Phase137 family.
- Training evaluation only: 2023-01-01 through 2025-12-31.
- Signal: `DFII10[t] - DFII10[t-20 available observations] < 0`.
- No magnitude threshold, normalization, percentile, volatility scaling, optimization, or parameter sweep.
- Publication causality guard: a dated FRED observation may affect crypto exposure only from **00:00 UTC on the next calendar day**. This deliberately adds a full-day safety lag rather than assuming intraday release availability.
- Missing/non-business dates: carry only the latest already-released signal state forward; never interpolate yield values.
- Basket: equal-weight BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- Gross exposure when active: **0.50** total (0.10 each); otherwise 0.
- Rebalance decision at 00:00 UTC only; positions persist until the next decision.

## Frozen training gates

All must pass without rescue:

1. Aggregate training total return > 0; daily Profit Factor >= 1.05; max drawdown >= -35%.
2. Every frozen chronological fold has total return > 0 and daily Profit Factor >= 1.02.
3. Severe costs/funding: return > 0 and PF >= 1.02.
4. Supersevere costs/funding: return > 0 and PF >= 1.00.
5. Single-asset share of positive raw price contribution <=45%.
6. Top-10 positive-day contribution share <35%.
7. Open gross <=0.50 plus numerical tolerance 1e-6.
8. Repeated execution must be byte-identical at report level in workflow.

Report must include payoff, win rate, positive days, max drawdown, PF, regimes, concentration, tails, stress cases, fold metrics and reproducibility hashes. Validation and final holdout remain `None` unless this frozen training gate passes and a later, separately authorized validation stage is reached.

## Anti-overfit / isolation

No parameter search, rescue, alternate lookback, inverse direction, threshold adjustment, post-hoc regime filter, or cherry-picking is allowed if Phase138 fails. No Phase083 holdout use. No V16 or V99 evidence/state/workflow/report may be used or modified. Phase138 failure closes this exact real-yield economic hypothesis; any later macro hypothesis must be scientifically distinct and separately preregistered.