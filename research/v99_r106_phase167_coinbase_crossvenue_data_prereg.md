# V99 R106 Phase167 — Coinbase cross-venue spot DATA-only audit

## Frozen before any Phase167 PnL

**DATA ONLY. BEFORE ANY Phase167 PnL.** This phase tests whether an independent cross-venue spot source is sufficiently complete and causal for a later, separately preregistered hypothesis. It does not compute returns, signals, thresholds, rankings, portfolio weights, or PnL.

### Scientific motivation
Phase165/166 showed that Binance derivatives auxiliary fields fail their frozen integrity contracts. Rather than rescue those fields, Phase167 moves to an orthogonal venue/source: Coinbase Exchange spot hourly candles. A later hypothesis may study cross-venue dislocation only if this DATA gate passes and is separately preregistered before any PnL.

### Frozen scope
- TRAIN only: `[2021-12-01T00:00:00Z, 2024-01-18T00:00:00Z)`.
- Fixed products: `BTC-USD`, `ETH-USD`, `SOL-USD`, `XRP-USD`, `DOGE-USD`.
- Source: Coinbase Exchange public `/products/{product}/candles`, granularity 3600 seconds.
- Deterministic chronological 300-hour request windows; deduplicate only exact timestamp collisions returned by the source.
- No forward fill, interpolation, product dropping, date trimming, post-audit threshold changes, or substitution of a different venue/product after inspection.

### Frozen DATA gates
Each fixed product must satisfy all of:
1. hourly coverage >= 95% of the frozen TRAIN grid;
2. zero duplicate timestamps after deterministic exact-timestamp canonicalization;
3. timestamps strictly increasing and on the 1-hour grid;
4. OHLC finite and strictly positive; volume finite and nonnegative;
5. no rows outside TRAIN.

Cross-sectional coverage with at least 4/5 products present must be >= 90% of TRAIN hours.

### Firewall / invariants
- `pnl_computed = false`.
- holdout rows used for feature construction = 0.
- holdout rows used for selection = 0.
- V16 Frozen and V99 Frozen must remain untouched.
- A FAIL closes this exact source contract; no rescue by dropping a product or relaxing gates.
- A PASS authorizes only a **new separately preregistered** Phase168 hypothesis. It does not authorize PnL by itself.
