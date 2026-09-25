# V99 R106 — Frontier audit through Phase134 (2026-09-25)

## Purpose

Stop spending hypothesis budget on repeatedly rejected transforms and make the next V99 work structurally different rather than cosmetically different. This audit uses only already-persisted train-only evidence. No untouched holdout result is used for selection.

## Current incumbent

The incumbent remains the Phase7/Phase9 F7 core. No Phase105–134 result reviewed here justifies promotion or modification of the incumbent. V16 Frozen and V99 Frozen remain untouched.

## Evidence from the recent frontier

### Positioning / crowding family

Phases105–109 all failed the train gate with 0/4 healthy temporal folds.

- Phase105 top-trader divergence: train ROI -26.60%, PF 0.709.
- Phase106 top-trader size divergence: train ROI -19.97%, PF 0.786.
- Phase107 top-trader conviction: train ROI -11.82%, PF 0.859.
- Phase108 global crowding contrarian: train ROI -23.80%, PF 0.850.
- Phase109 top-trader-count crowding contrarian: train ROI -19.31%, PF 0.793.

Decision: direct continuation/contrarian transforms of the same positioning ratios are exhausted unless genuinely new information enters the model. Sign flips, alternate lookbacks, thresholds, and renamed spreads are not new hypotheses.

### Raw flow / aggressor / trade-structure family

Phases120–124 all failed decisively with 0/4 healthy folds.

- Phase120 raw taker imbalance: ROI about -99.38%, PF 0.158.
- Phase121 large-trade pressure: ROI about -99.46%, PF 0.147.
- Phase122 aggressive trade-count imbalance: ROI about -97.68%, PF 0.246.
- Phase123 aggressor-run persistence: ROI about -98.01%, PF 0.234.
- Phase124 trade-size concentration: ROI about -89.87%, PF 0.451.

Decision: this family is not near a viable frontier under the current causal construction/cost contract. No rescue via sign flip, threshold, cadence, gross, or horizon changes.

### Price/volatility/residual family

Phases125–133 also fail to establish a transferable edge.

- Phase125 volatility efficiency: ROI about -70.95%, PF 0.544.
- Phase126 range compression/expansion: ROI about -96.29%, PF 0.443.
- Phase127 market-residual momentum: ROI about -69.76%, PF 0.573.
- Phase128 volatility-normalized momentum: ROI about -70.61%, PF 0.553.
- Phase129 short-horizon reversal: ROI about -95.78%, PF 0.230.
- Phase130 downside asymmetry: ROI about -66.02%, PF 0.598.
- Phase131 idiosyncratic-volatility shock continuation: ROI -70.33%, PF 0.530, 0/4 healthy folds.
- Phase132 volatility-of-volatility reversal: ROI -23.02%, PF 0.868, 0/4 healthy folds.
- Phase133 residual-dispersion continuation: ROI -49.16%, PF 0.707, 0/4 healthy folds.

Decision: another transform of return, residual return, realized volatility, vol-of-vol, compression, reversal, or dispersion is not admissible as a "new" research direction unless it adds a genuinely independent information source.

### Volume family

Phase134 dollar-volume-surprise continuation failed with ROI -38.53%, PF 0.791 and 0/4 healthy folds.

Phase135 return/volume coupling is scientifically more distinct because it tests signed return-volume covariance rather than volume level alone. However its pre-execution audit correctly found that the runner could parse the full canonical dataset before truncating to train. Phase135 must not execute until the holdout-provenance contract is made exactly truthful and auditable.

## Frontier decision

The recent failure streak is now strong enough to change research policy.

1. Do not continue a numerical phase conveyor belt through cosmetic OHLCV/positioning/taker transforms.
2. A new alpha phase must state, before PnL, what *new information* it introduces relative to the exhausted families above.
3. If the new phase uses only the same price/volume/positioning/taker fields, it requires an explicit non-duplication argument stronger than a new formula or horizon.
4. Prefer source-level orthogonality: genuinely new point-in-time information, new market structure, or a demonstrably independent economic mechanism.
5. Data-feasibility/integrity work is preferred over speculative PnL when the source itself is not yet proven causal and reproducible.
6. No holdout opening, no rescue tuning, no sign flip after result, no threshold grid, and no weakening of the F7/F9 comparison gate.

## Immediate next step

Finish the Phase135 provenance/integrity correction *without changing its frozen hypothesis*. If that cannot be proven cleanly, cancel Phase135 pre-PnL.

After Phase135, do not automatically create Phase136. First perform a source-level orthogonal-data inventory and admit a next alpha only if it crosses the independence bar above.

This is an anti-overfit acceleration measure: fewer low-information phases, more evidence per experiment.
