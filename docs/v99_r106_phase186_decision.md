# V99 R106 Phase186 — TRAIN decision

## Decision

**PERMANENT REJECT — no retuning.**

Phase186 tested volatility-shock conditional ETH/BTC relative continuation using only the chronological TRAIN region. The preregistered construction was: BTC standardized shock with 168h volatility history, fixed shock threshold 2.0, direction `sign(ETH-BTC return t-1)`, gross 0.20 market-neutral sleeve, and severe/supersevere execution costs.

## Evidence harvested from the immutable TRAIN artifact

- TRAIN end exclusive: `2024-01-18T00:00:00+00:00`.
- Holdout market values parsed: `false`.
- V16 Frozen untouched: `true`.
- V99 Frozen untouched: `true`.
- Active hours: 1007.
- Severe return: **-23.5403%**; max drawdown **-23.6486%**; healthy folds **0/5**.
- Severe fold returns: -5.4175%, -4.8138%, -5.7427%, -4.3815%, -5.7696%.
- Severe remove-best-hour return: **-23.7186%**.
- Supersevere return: **-41.1553%**; max drawdown **-41.1576%**; healthy folds **0/5**.
- Supersevere fold returns: -10.6698%, -9.7465%, -10.5772%, -8.7507%, -10.5527%.
- Supersevere remove-best-hour return: **-41.2843%**.

## Independent failure audit

This is not a single-tail or single-period failure. Every chronological fold is negative under both cost schedules, and removing the best hour makes the already negative aggregate slightly worse. The loss also expands materially when costs double, which is consistent with an economically weak/high-turnover event sleeve rather than a robust latent edge hidden by one anomalous observation.

The result therefore fails before regime-matrix or benchmark-envelope promotion. Those later gates must not be used to rescue or retune a TRAIN-alpha failure.

## Anti-overfit disposition

Do not invert the signal after seeing this result, do not alter 168h, 2.0, gross 0.20, event definition, or costs, and do not inspect holdout for this family. Phase186 is closed as specified.

## Next research direction

The next hypothesis must be scientifically distinct rather than a parameter variant of Phase182–186. Prefer an orthogonal observable with a plausible causal mechanism and independently available historical data; preregister its transformation, lag, thresholds, costs, folds and kill criteria before PnL.
