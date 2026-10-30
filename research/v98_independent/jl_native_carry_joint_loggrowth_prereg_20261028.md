# V98 Independent JL — pre-result preregistration (2026-10-28)

**Status: hypothesis only. No source gate, PnL or economic selection has yet been run.** This file is committed before implementing or evaluating JL. Prior rejected architectures remain frozen and are not candidates for rescue.

## Distinct hypothesis: signed native funding auction and log-utility composition
JL tests a **native-carry-and-liquidity-aware joint log-growth portfolio** rather than a price-only specialist router, wick rejection, migration, or JK shadow-performance gate. A fully funded seven-slot portfolio jointly evaluates four specialist target vectors, with opportunity, relative-value and stress/recovery contributing only when their combined causal forecasts compensate for opportunity cost, concentration and turnover. Positive standalone alpha is not required; positive physical full-minus-ablation net log growth is.

1. **Growth Core:** trend persistence and realized volatility on 504h close-to-close returns, net of actual event funding; diversified inverse-volatility fallback. No fixed asset selection.
2. **Opportunity Sleeve:** native **negative-funding-receiver** long selected by 336h lagged signed funding, 96h positive price drift and trailing quote-volume capacity; never uses future funding.
3. **Relative-Value Sleeve:** market-neutral long the most attractive **funding-adjusted relative trend** and short the least attractive, with 336h funding receipts and 168h beta-residual return. Net exposure zero, gross 1.
4. **Stress/Recovery Sleeve:** stress beta-resilience spread; recovery long positive-return drawdown survivor; in normal regime a positive-carry long/short spread. This is not a synthetic risk-free hedge.
5. **Regime Router:** uses 336h drawdown, 72h market return and 168h realized market volatility, all observed at decision close.
6. **Dynamic Allocator:** a single causal covariance-aware log-utility proxy across four experts, using trailing 336h return covariance, 168h expert mean and a frozen turnover penalty; simplex weights and Core floor 0.50, no grid or hindsight. Full and leave-one-out each re-optimize with the removed expert forbidden; no synthetic ablation PnL.
7. **Risk Governor:** existing V98 order-invariant shared-collateral buffered governor, prior-only adverse-gap/funding/exit-liquidity bounds, gross <=1, stress gross 0.80, recovery gross 0.95, normal 1.00; actual next-hour open and signed funding settlement.

## Frozen source/decision settings
Universe BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT Binance USD-M 1h; pinned source run 40064588623, expected manifest SHA256 `833013a2e18836a203afd267ca698175907cff8f4c153c919a7811f14cb80752`. 2022-12 warmup, 2023-2024 training; **no 2025 or later**. Decisions after completed close t, execution next actual open t+1. Epoch 168h, lookbacks 504/336/168/96/72, min quote-positive window 336h. No XRP, Phase083, benchmark internals, Frozen, paper or live.

Source-only viability: at least eight epochs in each year with L1 Full-vs-each-ablation target difference >0.025. Missing quote quarantines optional modules. Exact causal future mutation, L1 gross, finite values and source provenance gates before historical PnL.

## Physical economics and non-negotiable gates
Five independently financed USD10,000 books: Core, Full, minus Opportunity, minus RV, minus Stress/Recovery. Base/severe/supersevere native fees, slippage, mark/funding, both event orderings, Ubuntu 22.04/24.04. Thirty unique physical cases (60 cross-OS receipts). Independent all-hour settlement oracle and separate original-receipt economic audit. Positive net log growth each 2023 and 2024; Full two-year CAGR >50% base and >30% severe, severe max DD <45%, turnover <=USD600k base and severe. Every optional module: Full-minus-physical-ablation combined 2023+2024 log growth >0.02 in base and severe and each annual contribution >=-0.03, both funding orders. Profit factor, payoff, win rate, positive UTC days, CVaR, concentration and no hidden borrow audited. No post-result sign, budget, window, gross, fee, threshold or parameter rescue.

If and only if all precommitted training/source/physical/independent gates pass, freeze JL and preregister separate untouched 2025 validation. Only after validation may external V14/V15/V99 benchmarking occur. 2026+ untouched future holdout never opened during training.