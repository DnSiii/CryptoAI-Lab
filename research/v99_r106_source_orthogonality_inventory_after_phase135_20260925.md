# V99 R106 — Source-Level Orthogonality Inventory after Phase135

Date: 2026-09-25
Status: RESEARCH FRONTIER CONTROL / NO ALPHA / NO HOLDOUT

## Purpose

Prevent further low-information phase churn after Phase135 and require the next V99 alpha to introduce genuinely new information rather than another transform of already exhausted sources.

## Exhausted or closed source families

### Canonical OHLCV / price-derived
Consumed extensively through trend, reversal, residual momentum, realized volatility, volatility-of-volatility, downside asymmetry, compression/expansion, dispersion, volume surprise, return-volume coupling and related transforms.

Recent decisive failures:
- Phase125 volatility efficiency: rejected.
- Phase126 range compression/expansion: rejected.
- Phase127 market residual momentum: rejected.
- Phase128 vol-normalized momentum: rejected.
- Phase129 short-horizon reversal: rejected.
- Phase130 downside asymmetry: rejected.
- Phase131 idiosyncratic-volatility shock: -70.33%, PF 0.530, 0/4 healthy folds.
- Phase132 vol-of-vol reversal: -23.02%, PF 0.868, 0/4.
- Phase133 residual dispersion: -49.16%, PF 0.707, 0/4.
- Phase134 dollar-volume surprise: -38.53%, PF 0.791, 0/4.
- Phase135 return/volume coupling: -42.78%, PF 0.784, 0/4.

Decision: no new alpha may be admitted merely because it uses a different lookback, normalization, sign, threshold, cadence, or algebraic combination of canonical OHLCV.

### Funding / premium / basis-like Binance futures information
Funding-pressure, funding-divergence, funding-crowding, premium-index and related families have already been tested. Phase112 established premium-index data availability; Phase113 premium crowding reversal then failed at -60.86%, PF 0.564, 0/4 healthy folds.

Decision: no rescue transform of the same funding/premium/basis information.

### Positioning / open interest / top-trader / crowding
Multiple direct, change, divergence, dispersion, continuation and contrarian constructions have been consumed. Recent Phases105–109 all failed with 0/4 healthy folds.

Decision: this source family is closed unless a materially different external source adds information not represented by the Binance ratios already used.

### Raw aggTrades / taker / aggressor / trade structure
Phase118 availability audit passed and Phase119 integrity probe passed, so raw data quality was not the problem. Phases120–124 then failed decisively under the causal train-only contract.

Decision: further thresholds, large-trade cuts, run definitions, sign flips or aggregation horizons are not independent hypotheses.

### Mark/index dislocation
Phase116 established strong paired mark/index coverage. Phase117 dislocation-stress alpha failed: -39.07%, PF 0.747, 0/4 healthy folds.

Decision: source remains technically valid, but the tested dislocation-stress family is rejected and cannot be rescued by parameter tuning.

### Liquidations
Phase115 found no usable official Binance USD-M liquidationSnapshot archive for the required pre-train period.

Decision: closed under the current official source. A third-party replacement requires a separate provenance/licensing/PIT audit before any PnL.

### Book depth
Phase114 found high archive coverage from 2023 onward, but the prior research path identified temporal-admissibility/boundary concerns before alpha launch.

Decision: not an immediate alpha source. Any revisit must first solve admissible train-history/PIT coverage and must not reuse the previous rejected launch logic.

## What qualifies as genuinely new information now

A next V99 alpha is admissible only if it starts with DATA_ONLY provenance/integrity work and belongs to an information source not already represented above. Examples of admissible categories, subject to actual availability and PIT integrity:

1. cross-venue price/liquidity dislocation using a second exchange with auditable historical point-in-time data;
2. options-derived information (term structure/skew/IV) from a reproducible historical source;
3. on-chain flow/state information with immutable timestamps and survivorship-safe asset mapping;
4. stablecoin issuance/redemption/flow information with point-in-time timestamps;
5. macro/liquidity information only when its publication/revision timing is explicitly modeled;
6. another source only if its economic mechanism and information set are demonstrably distinct from the exhausted Binance/OHLCV families.

These are categories for data feasibility, not pre-approved alpha directions.

## Admission gate for the next V99 phase

Before any PnL:
- identify source and exact field(s);
- prove training-period coverage across enough temporal folds;
- prove timestamp semantics and PIT availability;
- prove deterministic retrieval/checksum or immutable archive provenance;
- document survivorship/symbol mapping;
- document why information is not a cosmetic proxy for an exhausted family;
- freeze one economic hypothesis only after the data gate passes.

If those conditions cannot be met, do not create the next alpha phase.

## Current decision

Phase135 is permanently rejected. F7/F9 remains champion. The next V99 work is source discovery/feasibility, not another OHLCV formula.
