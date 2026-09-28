# V99 R106 Phase166 — Positioning-ratios DATA-only audit

Status: **PREREGISTERED BEFORE ANY Phase166 PnL**.

## Scientific reason
Phase165 is scientifically closed as FAIL_DATA_ONLY under its frozen zero-invalid native-contract-OI gate: all five symbols have excellent coverage and checksums, but each contains 133–135 non-positive `sum_open_interest` records. That gate must not be weakened after observation. The same immutable Binance metrics archives expose distinct positioning observables, so Phase166 audits those fields without PnL.

## Scope / firewall
- DATA ONLY: no returns, PnL, PF, drawdown, direction/threshold selection, or holdout inspection.
- TRAIN only: 2021-12-01 through 2024-01-18 exclusive.
- Symbols fixed ex ante: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT.
- Frozen V16 and Frozen V99 remain read-only.
- Fields fixed before inspection: `count_toptrader_long_short_ratio`, `sum_toptrader_long_short_ratio`, `count_long_short_ratio`, `sum_taker_long_short_vol_ratio`.

## Source / integrity contract
Binance Vision USD-M daily metrics archives; every archive must pass its published SHA-256 `.CHECKSUM` and ZIP CRC. Native timestamps are retained with no interpolation.

## DATA gates
For every symbol/field report native coverage, duplicates, monotonicity, non-finite count and non-positive count. PASS_DATA_ONLY requires >=90% TRAIN coverage for each fixed field/symbol, unique strictly increasing timestamps, zero non-finite values, zero non-positive values, checksum verification for every loaded archive, and >=85% aligned cross-symbol coverage at the declared native cadence.

If any fixed field fails, Phase166 is FAIL_DATA_ONLY. No field may be dropped after seeing this audit to manufacture a pass.

## Future alpha authorization
None. Only a later separately preregistered phase may select one scientifically justified positioning mechanism, and it must freeze direction, normalization, lag, severe/supersevere costs, temporal folds, regime matrix, benchmark envelope and reproducibility gates before any PnL is observed.
