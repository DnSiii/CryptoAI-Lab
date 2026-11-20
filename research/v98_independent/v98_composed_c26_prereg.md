# V98 Independent C26 — preregistration (2026-11-20)

Status: **new untested architectural hypothesis**; NOT a C25 rescue, not approved, no benchmark inspection. C22/C23/C24/C25 remain rejected. No 2026+ data, no Phase083 holdout, no XRP.

Hypothesis: persistent, sparse participation in *multi-month breakouts* with weekly allocation and asymmetric trend exits can retain more gross compounding after native funding and severe costs than continuously reallocated momentum. This is a distinct complete seven-slot portfolio hypothesis, not an isolated alpha.

Seven slots, fixed ex ante:
1. Growth Core (55%): long only above prior 180-day closing high and positive 90-day trend; weight proportional to positive 90-day log drift divided by 30-day realized volatility.
2. Opportunity Sleeve (20%): 30-day consolidation followed by a new 30-day high, conditional on positive 90-day drift and 14-day volatility below 90-day volatility.
3. Relative-Value Sleeve (15%): strongest positive 90-day volatility-adjusted momentum relative to median of four Clean-4 assets, conditional on being above 90-day moving-average close.
4. Stress/Recovery Sleeve (10%): 14-day recovery from a 60-day drawdown of at least 15%, with price above 30-day mean.
5. Regime Router: benchmark BTC positive 180-day trend, BTC above 90-day mean, and 14-day realized volatility <= 2x 90-day volatility; multiplier 1, 0.5 or 0, never short.
6. Dynamic Allocator: normalize each sleeve independently, leave unused budgets in cash; rebalance only every 168 hours after initial 4320-hour warmup.
7. Risk Governor: existing causal completed-equity governor; hourly post-fill enforcement of 90% gross and 40% per-asset caps.

No signal uses future bars; execute at next open, native funding and cost scales 1x/2x/4x. Clean-4 only, Dec-2022 through Dec-2025. Training must include annual returns, PF, payoff, positive days, max drawdown, tails, concentration, exposure, independent full-ledger reconciliation. Reject for any arithmetic/causality/cap failure, any cost scenario nonpositive total growth, or nonpositive 4x return in any 2023-2025 calendar year. No post-result parameter rescue. A training pass is not chronological validation, holdout access, benchmark approval, or promotion.
