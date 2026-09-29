# V98 Independent — Phase183 MOVE index DATA_ONLY preregistration

Status: **PREREGISTERED / DATA_ONLY / NO PNL**

## Scientific rationale

Phase182 was closed before execution because VIX/VIXCLS had already been audited and economically tested in Phases145/156/163/164. The next family must be genuinely distinct. Phase183 therefore investigates Treasury-option implied volatility through the ICE BofA MOVE Index as a rates-volatility/stress observable, distinct from equity-option volatility, Treasury yields/curve level, breakeven inflation, NFCI/STLFSI, HY spread, DXY, WTI, TGA, and RRP families previously studied.

## Frozen scope before acquisition

- Observable: ICE BofA MOVE Index only; no VIX substitution.
- Research period: 2023-01-01 through 2025-12-31 only.
- DATA_ONLY: no crypto positions, returns, labels, thresholds, PnL, validation, or final holdout may be read or computed.
- Use one public/officially attributable historical source if accessible without credentials. No source shopping after observing values.
- Acquisition must be repeated twice independently; normalized observation SHA-256 must match.
- Required integrity checks: source identity, first/last usable date, yearly usable counts, missing values, duplicate dates, monotonic dates, maximum calendar gap, descriptive quantiles, and publication/causal availability.
- Conservative causal policy for any later experiment: a daily MOVE close cannot affect crypto exposure until the next UTC day; same-day use is forbidden.
- Business-day cadence is expected; weekends and market holidays are not defects by themselves.

## Pass/fail gate

PASS_DATA_ONLY requires all of: source provenance unambiguous; non-empty 2023/2024/2025 coverage; >=200 usable observations in each complete year; monotonic unique dates; no parsed missing/nonfinite values; max calendar gap <=7 days; duplicate acquisition hashes identical; no access to dates >=2026-01-01; no V16/V99 use.

If provenance/access/coverage fails, decision is `REJECT_DATA_AVAILABILITY_NO_RESCUE`. No alternative-source shopping, interpolation, backfill, threshold search, economic test, or rescue is allowed after failure.

If and only if DATA_ONLY passes, a later phase may preregister exactly one fixed training-only economic transformation before any PnL is observed. Phase183 itself cannot select a lookback, threshold, sign, or sizing rule.
