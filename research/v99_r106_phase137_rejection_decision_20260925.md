# V99 R106 Phase137 — Cross-Venue Dislocation Reversion Decision

Date: 2026-09-25
Decision: **TRAIN_ALPHA_REJECT / NO RESCUE**

Phase137 was the first economic hypothesis tested after Phase136 admitted the independent OKX hourly source.

## Result

Frozen train-only hypothesis:
- log(Binance/OKX) price spread;
- 168h rolling median baseline;
- 168h MAD scale;
- negative tanh standardized dislocation (mean reversion);
- cross-sectional demeaning;
- complete score t-1;
- five frozen assets;
- alpha gross 0.20;
- severe selection cost.

Observed training evidence:
- ROI: -98.58%;
- Profit Factor: 0.265;
- max drawdown: -98.58%;
- robust mean without top 1%: negative;
- valid folds: 4;
- healthy folds: 0/4.

Fold results were uniformly negative, with ROI between roughly -60% and -69% and PF around 0.25-0.29.

## Integrity

- All five Phase136 OKX full-row hashes were reproduced before PnL.
- OKX coverage remained 100% across the frozen window.
- Binance BTC/ETH/DOGE coverage was 100%; SOL/XRP were 99.36% because of known canonical gaps.
- Missing Binance prices were not filled.
- Train inputs were strictly before the train boundary.
- Post-train targets were zero.
- V16 Frozen and V99 Frozen remained untouched.

## Scientific decision

The exact cross-venue **price-level dislocation mean-reversion** hypothesis is permanently rejected.

Forbidden rescue:
- sign flip to continuation;
- alternate lookback;
- threshold search;
- symbol subset;
- gross/cadence tuning;
- post-hoc regime filter.

Phase136 remains a valid source-level result: OKX is still admitted as an independent historical venue. A future OKX experiment is allowed only if it tests a distinct economic mechanism/information object rather than a renamed or sign-flipped price-spread hypothesis.
