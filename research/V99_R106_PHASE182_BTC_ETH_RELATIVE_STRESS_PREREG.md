# V99 R106 — Phase182 BTC/ETH Relative Stress preregistration

Date: 2026-09-29
Status: PREREGISTERED / TRAIN-ONLY / NO HOLDOUT

## Scientific distinction

Phase182 leaves node-observation/protocol-gap data entirely. It tests whether **relative market stress between BTC and ETH**, built only from already point-in-time exchange OHLCV bars, carries robust all-regime information beyond absolute momentum/volatility. This is deliberately orthogonal to Phase180/181 provenance failures.

## Frozen construction before PnL

Use only the existing canonical BTCUSDT and ETHUSDT bar source already admitted by the R106 market-data pipeline. No new vendor, no retrospective chain labels.

At decision bar t, every feature must be computed from data ending at t-1 or earlier.

Fixed feature family, no window search:

- relative log return: `r_eth - r_btc` over 1 bar;
- fixed 24-bar relative return sum;
- fixed 24-bar realized-volatility ratio `rv_eth / rv_btc`;
- fixed 24-bar volume-shock difference using each asset's own trailing median, shifted t-1;
- fixed stress interaction: negative relative return × positive relative-volatility excess.

No alternative windows, quantile search, sign flip after results, asset substitution, threshold optimization, or feature deletion after PnL inspection.

## Evaluation discipline

1. Verify exact timestamp intersection and no forward-filled bars.
2. Verify all feature dependencies terminate at t-1.
3. Selection is chronological TRAIN-only with existing temporal folds.
4. Candidate must face the unchanged benchmark envelope and regime matrix.
5. Severe and supersevere transaction-cost gates remain unchanged.
6. Tail/concentration audit is mandatory: top-day/top-week contribution, worst fold, worst regime, turnover concentration.
7. Reproducibility: deterministic source hashes, feature hash, config hash, repeated run equality.
8. Holdout remains inaccessible until a candidate is frozen under the existing R106 promotion protocol.

## Kill criteria

Reject Phase182 without modification if any of these occurs:

- timestamp intersection materially changes sample composition across folds;
- any feature leaks t or future data;
- improvement is isolated to one fold/regime or dominated by a small tail set;
- benchmark-envelope advantage disappears under severe/supersevere costs;
- sign/window/threshold changes would be required to obtain the result;
- deterministic rerun differs.

No holdout access is authorized by this preregistration.
