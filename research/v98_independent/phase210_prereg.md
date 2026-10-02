# V98 Independent — Phase210 preregistration

## Hypothesis
**Hour-of-week residual reversal.** Crypto has persistent intraday/hour-of-week structure in volatility, liquidity and funding/flow. A raw one-hour move that is extreme relative to that asset's own causal hour-of-week distribution may contain a short-horizon transitory component. Trade only the residual surprise, not raw momentum, dispersion, funding level, or volatility compression. This is scientifically distinct from Phase206 funding dislocation, Phase207 BTC-residual momentum, Phase208 volatility-compression breakout, and Phase209 cross-sectional dispersion-shock reversal.

## Data firewall
- Branch `research/v98-independent-zero` only; V98 Independent namespaced files only.
- Assets: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. BTCUSDT may be used only for the established causal regime diagnostic, never for selection/tuning.
- Canonical 1h prices and frozen realized funding, strictly `<2026-01-01`.
- Folds scored separately: calendar 2023, 2024, 2025; prior observations are warm-up only.
- Validation/final holdout remains unopened.

## Fixed causal signal
At decision open `t`, for each asset:
1. Observe completed open-to-open return `r(t-1)` only.
2. Determine the UTC hour-of-week bucket of `t-1` (0..167).
3. From observations strictly ending at `t-2`, estimate that asset/bucket causal location and scale over trailing L calendar days using median and MAD. Require at least 8 historical observations in the bucket; otherwise no signal.
4. Robust residual z = `(r(t-1)-median)/(1.4826*MAD)`. If MAD is zero/non-finite, no signal.
5. If `|z| >= Z`, enter at `t` open in the opposite direction of the residual: z>0 short, z<0 long.
6. Each asset is evaluated independently. If multiple assets signal, equal-weight active signals with portfolio gross exposure 1.0. No new entry for an asset while its position is active.
7. Hold exactly H hours open-to-open. No stops, take-profit, regime/funding filters, asset exclusions, signal inversion or post-hoc rescue.

## Closed grid — exactly 8 specs
Cartesian product: L `{84,168}` days × Z `{2.0,3.0}` × H `{4,12}` hours = 8 specs. No additional parameter search.

## Economics
Use the frozen V98 Independent base/severe/supersevere execution-cost schedule and realized-funding accounting. Charge entry and exit turnover. Funding is aligned to each active position interval; no synthetic funding imputation. Preserve existing V98 portfolio/equity conventions.

## Required outputs
Per spec/fold/cost: return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99 trade tails, asset contribution/concentration, bull/bear/sideways regime decomposition, and funding contribution.

## Reproducibility/invariants
- Unique monotonic timestamps and strict `<2026-01-01` assertions.
- Scoring starts exactly at fold start; warm-up cannot create an entering position.
- Every median/MAD reference sample ends at `t-2`; no current-bar contamination.
- Hour-of-week bucket uses UTC consistently.
- Execute twice from frozen inputs and require identical deterministic result SHA256.

## Mechanical promotion discipline
No candidate advances unless base return > 0 and PF > 1 in all 2023/2024/2025 folds, drawdown/tails/concentration are acceptable, edge is not dominated by one asset/regime, and severe/supersevere remain credible under existing V98 governance. If family fails, reject without rescue/tuning and move to a scientifically distinct hypothesis. Do not inspect validation/final holdout.
