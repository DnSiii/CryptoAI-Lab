# V98 Independent — Phase187 orthogonal training preregistration

Status: **PREREGISTERED / TRAINING-ONLY / VALIDATION AND FINAL HOLDOUT CLOSED**

## Motivation

Phase186 rejected the frozen WALCL overlay on untouched validation. No WALCL rescue is permitted. Phase187 therefore moves to a scientifically distinct family rather than tuning the failed macro-liquidity gate.

## Hypothesis family

Test a **cross-sectional idiosyncratic-momentum dispersion state** derived only from the existing five V98 crypto instruments and information already available at decision time. The hypothesis is that the underlying V98 cross-sectional selection edge is more reliable when dispersion in asset-specific momentum is sufficiently large relative to common-market movement, because ranking contains more idiosyncratic information and less undifferentiated beta.

This is deliberately orthogonal to WALCL/T10YIE/VIX/external macro direction: no external macro series, V16, V99, validation data, or holdout data may be used.

## Frozen training protocol before PnL

- Training data only: **through 2025-12-31**. Do not read, download, summarize, or evaluate 2026 validation/final-holdout data.
- Preserve the existing V98 chronological folds and underlying stack exactly.
- At each decision timestamp, compute per-asset trailing momentum using only lagged/available prices, remove the equal-weight cross-sectional mean momentum, and measure cross-sectional dispersion of the residual momentum vector.
- Evaluate the dispersion state as a risk overlay on the existing V98 stack, never as a replacement universe or asset-specific rule.
- Use a very small preregistered structural grid only: trailing momentum horizon **24h or 72h**; dispersion reference window **30d or 90d**; state boundary is the rolling **50th percentile** calculated causally from prior observations; low-dispersion gross multiplier **0.50 or 0.75**, high-dispersion multiplier 1.00. No sign inversion, asset-specific thresholds, extra horizons, or post-result rescue.
- Selection must be chronological: choose one specification using training folds only and require directionally consistent improvement versus CONTROL across folds rather than best aggregate return alone.
- Preserve realistic funding/costs plus severe and supersevere schedules, gross-cap, no ruin, max drawdown, PF, payoff, win rate, positive days, monthly/regime analysis, concentration/tails and asset contribution.
- Require deterministic rerun identity and explicit causal/integrity assertions.

## Anti-overfit decision discipline

Reject the entire Phase187 family if improvements are concentrated in one fold/month/asset/tail event, if severe/supersevere expectancy is non-positive, if PF robustness is absent, or if the apparent benefit requires selecting different specifications by regime. At most one Phase187 specification may be frozen from training. Only a genuinely robust training candidate may later receive a separately preregistered untouched validation run; no 2026 result may influence Phase187 selection.

Phase186 validation evidence may motivate abandoning WALCL, but its detailed 2026 regime/month behavior must not be used to choose Phase187 horizons, thresholds, multipliers, or selection criteria.