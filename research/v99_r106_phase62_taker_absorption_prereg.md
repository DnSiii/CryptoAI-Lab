# V99 R106 Phase62 — native taker-flow absorption (pre-registration)

Decision time: 2026-09-18, before any Phase62 outcome is computed.

## Prior evidence
Phase61A native 24h taker-flow continuation is rejected train-only (0/4 healthy folds; severe ROI < 0). This rejection must not be rescued by sign-flipping, horizon search, threshold search, or holdout inspection.

## Independent mechanism
Test **absorption**, not continuation: aggressive taker imbalance that fails to produce commensurate same-direction price movement can indicate passive-liquidity absorption. The feature is computed per asset from native Binance USD-M 1h taker-buy quote volume and canonical close returns, with every decision feature shifted by one completed bar.

Fixed specification: over 24 completed hours, `flow = mean(2*taker_buy_quote_volume/quote_volume-1)` and `ret = close/close.shift(24)-1`. Define signed absorption score `-(flow * sign(ret)) * abs(flow) / (abs(ret)+1e-4)`, winsorized cross-sectionally each hour at 5/95% only for numerical tail control, then cross-sectional weights through the existing deterministic Phase31 weight mapper. Gross alpha budget remains 0.20. No alternative horizon, epsilon, winsorization percentile, sign, or gross budget will be tested in Phase62.

## Gates
1. Train only through the already registered `train_end`; Phase62 code must not download/parse taker-flow after train_end.
2. Causal t-1 feature only.
3. Same severe-cost engine and four temporal train folds used by the prior alpha gates.
4. Pass only if the existing `stable_train` gate passes; otherwise reject with no holdout access.
5. Only after a train pass may the exact frozen specification proceed to a separately implemented untouched-holdout gate, followed by supersevere costs, regime matrix and benchmark envelope as required.

V16 Frozen and V99 Frozen are read-only and must remain untouched.