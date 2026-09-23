# V99 R106 Phase123 — aggressor run imbalance — preregistration

Status: **PREREGISTERED BEFORE ANY PHASE123 PNL. DO NOT RUN UNTIL PHASE121 IS HARVESTED/DECIDED.**

## Scientific motivation
Phase120 tested signed aggressive notional/quantity imbalance, Phase121 isolates causally-defined large-trade pressure, and Phase122 tested buyer-vs-seller aggressive print counts and was permanently rejected. Phase123 changes the microstructure object: instead of how much or how often each side trades, it measures **directional clustering/persistence of consecutive aggressor prints**. The hypothesis is that order splitting and persistent execution programs may leave information in same-side run structure that marginal count or volume imbalance does not contain.

## Frozen hypothesis
For each symbol and UTC hour t, consume official Binance USD-M `aggTrades` in strict exchange/file order and map buyer-initiated aggressive trades as +1 (`isBuyerMaker=false`) and seller-initiated aggressive trades as -1 (`isBuyerMaker=true`). Within each UTC hour:

- partition the aggressor-sign sequence into maximal consecutive same-sign runs;
- `buy_run_mass_t` = sum of squared lengths of all +1 runs;
- `sell_run_mass_t` = sum of squared lengths of all -1 runs;
- `run_imbalance_t = (buy_run_mass_t - sell_run_mass_t) / max(buy_run_mass_t + sell_run_mass_t, 1)`.

Squaring run lengths deliberately emphasizes persistent same-side sequences while remaining independent of trade quantity/notional. No run may cross a UTC-hour boundary. At each hour, robust-standardize `run_imbalance` cross-sectionally using the existing deterministic median/MAD convention with at least 8 assets, squash with `tanh`, then shift the complete signal exactly one hourly bar (`t-1`) before execution.

Direction is frozen as **continuation**: positive buy-run persistence => positive alpha; negative sell-run persistence => negative alpha. No sign flip after PnL.

## Universe / data discipline
Use only the Phase119-integrity-qualified official Binance USD-M daily `aggTrades` archives and the same deterministic pre-PnL universe rule as Phases120–122: select the 12 Phase118 symbols with smallest `listed_compressed_bytes`, then intersect with the canonical executable V15 universe. Universe membership is fixed before return/PnL evaluation. Minimum executable universe: 8 assets. Missing raw files remain missing; no future backfill or synthetic imputation.

Every consumed archive must pass its official SHA256 `.CHECKSUM` and ZIP CRC/member invariant. Any trade timestamp >= **2024-01-18 00:00:00 UTC** is a hard abort. Holdout market values must not be downloaded, parsed, summarized, or used for selection.

## Portfolio / evaluation discipline
- Cross-sectional L1 normalization.
- Gross alpha budget: 0.20.
- Canonical R106 execution/guardrails and severe cost per side.
- Single hypothesis only: no grid over run exponent, horizon, transform, sign, universe, gross, thresholds, or minimum run length.
- No asset-by-asset tuning and no post-result repair.

Mandatory gate order:
1. causality/data-integrity/executable-universe invariants;
2. severe-cost chronological train gate plus four temporal folds;
3. supersevere-cost stress;
4. regime matrix plus tail/concentration/pathology audit;
5. benchmark-envelope comparison;
6. deterministic reproducibility/invariant rerun;
7. only after every preceding gate passes, freeze the exact candidate before any untouched holdout access.

A failure at any mandatory scientific gate permanently rejects this exact Phase123 hypothesis. Infrastructure-only failures may be repaired only when the frozen scientific definition above is unchanged.

## Frozen assets
V16 Frozen and V99 Frozen are read-only and must be hash-snapshotted/verified before and after execution.
