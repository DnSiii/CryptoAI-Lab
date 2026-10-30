# V98 Independent — Phase205 preregistration

## Hypothesis

A large lagged BTC impulse may propagate to liquid altcoins with a short delay. When an altcoin has moved in the same direction as BTC but by materially less over the same lagged window, the residual underreaction may continue for a few hours. This is a cross-asset information-propagation hypothesis, scientifically distinct from Phase202 single-asset range reversal, Phase203 path efficiency, and Phase204 own-asset volatility expansion.

## Frozen causal construction

All state for an entry at hour t is computed using observations through t-1 only.

Universe driver: BTCUSDT. Tradable responders: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. BTC itself is never traded in this family.

For each frozen impulse window `w`:

1. BTC lagged impulse = `BTC close(t-1) / BTC close(t-1-w) - 1`.
2. BTC scale = rolling standard deviation of hourly BTC log returns over 168 hours, available through t-1, multiplied by `sqrt(w)`.
3. normalized BTC impulse = impulse / scale.
4. responder lagged impulse is computed over the identical window through t-1.
5. underreaction ratio = responder impulse / BTC impulse when directions agree; observations with opposite sign are ineligible.

Long entry: normalized BTC impulse >= +`z`, responder impulse > 0, and responder/BTC impulse <= 0.50.

Short entry: normalized BTC impulse <= -`z`, responder impulse < 0, and responder/BTC impulse <= 0.50 using absolute magnitudes (`abs(responder impulse)/abs(BTC impulse)`).

The underreaction ceiling is fixed at 0.50. No cross-sectional ranking, no future information, no 2026+ information, no rescue after results.

## Frozen grid

Exactly 8 specifications:

- BTC impulse window `w`: 3h, 6h
- normalized impulse threshold `z`: 1.5, 2.0
- holding period: 3h, 6h

Equal weight across independently active responder assets. No pyramiding within an asset while a position is active.

## Evaluation

Training-only chronological folds: calendar 2023, 2024, 2025. Validation/final holdout remain untouched.

For every spec/fold report:

- return and max drawdown;
- Profit Factor, payoff, win rate, positive days;
- trade count/activity;
- funding and realistic base transaction costs;
- severe and supersevere transaction-cost scenarios;
- bear/bull/sideways decomposition based only on lagged BTC state;
- responder concentration and asset-level returns;
- **complete holding-period trade PnL** p01/p05/p50/p95/p99 and worst/best trade (fixing the Phase204 entry-bar tail diagnostic limitation);
- deterministic/reproducibility hash and temporal-firewall invariant.

## Decision discipline

A family cannot be promoted because of one year, one responder or one regime. Base profitability must be broad across chronological folds, PF must be credibly above 1 rather than marginal, and the family must retain meaningful robustness under severe/supersevere costs. Excessive responder concentration, pathological complete-trade tails, insufficient activity, or any reproducibility/causality/invariant failure rejects the candidate. No threshold rescue, inversion, responder deletion, regime cherry-picking, or post-result grid expansion is permitted.
