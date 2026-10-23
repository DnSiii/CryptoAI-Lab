# V98 Independent Phase1058 — Architecture R preregistration (2026-10-23)

**PRE-IMPLEMENTATION; no R economic results observed.** Q remains rejected and frozen. R is a genuinely different seven-slot portfolio hypothesis, not a Q threshold/sign/window/rounding rescue. No 2025+ training, Phase083, XRP or V14/V15/V99 access.

## North star and hypothesis
Maximize survivable long-run compounded wealth, not minimize volatility. The thesis is **asymmetric trend compounding + breakouts + funding-dispersion carry + stress-conditioned rebound** under a causal signed portfolio. Unlike Q's 72/504 signed dual momentum, volume impulse continuation, beta-neutral residual z-reversion and online shadow-performance allocator, R uses (1) long-biased multi-horizon trend efficiency, (2) channel breakout with activity confirmation, (3) native-funding cross-sectional carry, (4) post-downshock breadth reversal, and (5) deterministic regime-dependent capital budgets.

## Seven slots and fixed preregistered choices
1. **Growth Core**: long-only 48h/336h log-momentum agreement, normalized by 168h realized volatility; no forced short trend. Normalize across four assets.
2. **Opportunity Sleeve**: 24h high/low channel breach with contemporaneous 6h/168h quote-volume ratio >=1.5, signed direction; fixed 12h persistence.
3. **Relative-Value Sleeve**: 72h causal sum of native signed funding events, demean cross-sectionally, long lower funding/short higher funding, zero-net target. Never infer funding from prices.
4. **Stress/Recovery Sleeve**: 6h market downshock below -2 times prior 336h six-hour sigma, 3-of-4 positive 1h breadth, and positive mean close location; 12h long rebound exposure, not contrarian against every shock.
5. **Regime Router**: 48h market return and 168h realized downside-vs-upside volatility, causal 24h confirmation. Defensive/neutral/expansion.
6. **Dynamic Allocator**: deterministic state budgets: defensive (growth .25, opportunity .10, RV .50, recovery .15); neutral (.60,.20,.15,.05); expansion (.75,.20,.03,.02). Inactive sleeves retain their cash budget (no forced gross renormalization).
7. **Risk Governor**: state gross budgets (.40,.85,1.20), per-asset cap .45, net cap .70, gross cap 1.20, strictly causal t-1 fill; reserve shock/cost/funding buffer in a separately verified signed execution ledger. Signed weights may be negative; no hidden leverage.

All above numbers are fixed *before* any R historical economic result. No grid search, no post-result rescue, no holdout selection. A preregistered infrastructure contract requires cap-safe canonical serialization (8 decimals, conservative inward quantization) and a **post-serialization** invariant check. Any mismatch is BLOCKED_BEFORE_PNL, never mislabeled economic loss.

## Chronology and decision protocol
- Phase243 authenticated Clean-4 only, 2022-12 warmup; 2023 and 2024 distinct chronological training folds. 2025 separate validation only after R source, source hashes and training rules freeze; future holdout untouched.
- Five frozen ablations: R_core_only, R_full, R_minus_opportunity, R_minus_relative_value, R_minus_recovery. Economic grid: 5 paths x 3 fees x 2 funding orders x 3 capital modes = 90 cells. Base/severe/supersevere fee, native signed funding, full intrabar 16-corner survival, capacity, drawdown, CAGR/log wealth, PF, payoff, win rate, positive days, CVaR, asset HHI, regime attribution.
- Require all 90 valid full folds, positive compounded growth for R_full in 2023 and 2024 under base/severe, positive marginal contribution vs each ablation in those folds, no catastrophic margin/cost/tail/concentration breaches; only then evaluate untouched 2025. Reject on failure without cosmetic rescue.
- V14/V15/V99 are forbidden until complete R is frozen and passes internal separate validation.

## First work package
Implement R source-only seven-slot composer, post-serialization invariant oracle, deterministic synthetic tests (chronology, invariants, t-1, funding sign, ablations), then independently audit and freeze before authenticated 90-cell training. Do not change any Q/P/O frozen code or any non-V98 file.
