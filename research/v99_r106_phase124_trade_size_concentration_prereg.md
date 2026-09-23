# V99 R106 Phase124 — trade-size participation concentration — preregistration

Status: **PREREGISTERED BEFORE ANY PHASE124 PNL.**

## Scientific motivation
Phases121–123 rejected three standalone aggressor-direction objects under severe costs. Phase124 deliberately removes buyer/seller direction and asks a different microstructure question: whether hourly participation concentrated in a few unusually large prints contains cross-sectional continuation information that marginal signed flow does not.

## Frozen hypothesis
For each symbol and UTC hour t, consume official Binance USD-M `aggTrades` in strict exchange/file order. For each aggregate trade i define `notional_i = price_i * quantity_i` and hourly participation share `w_i = notional_i / sum_j(notional_j)` using only finite positive notionals in that hour. Define:

`trade_size_hhi_t = sum_i(w_i^2)`.

Hours with no positive finite notional are missing. No buyer/seller maker flag enters the feature. At each hour, robust-standardize `trade_size_hhi` cross-sectionally using the existing deterministic median/MAD convention with at least 8 assets, squash with `tanh`, then shift the complete signal exactly one hourly bar (`t-1`) before execution.

Direction is frozen as **continuation**: relatively concentrated participation => positive alpha; relatively diffuse participation => negative alpha. No sign flip after PnL.

## Universe / data discipline
Use only the Phase119-integrity-qualified official Binance USD-M daily `aggTrades` archives and the same deterministic pre-PnL universe rule as Phases120–123: select the 12 Phase118 symbols with smallest `listed_compressed_bytes`, then intersect with the canonical executable V15 universe. Universe membership is fixed before return/PnL evaluation. Minimum executable universe: 8 assets. Missing raw files remain missing; no future backfill or synthetic imputation.

Every consumed archive must pass its official SHA256 `.CHECKSUM` and ZIP CRC/member invariant. Any trade timestamp >= **2024-01-18 00:00:00 UTC** is a hard abort. Holdout market values must not be downloaded, parsed, summarized, or used for selection.

## Portfolio / evaluation discipline
- Cross-sectional L1 normalization.
- Gross alpha budget: 0.20.
- Canonical R106 execution/guardrails and severe cost per side.
- Single hypothesis only: no grid over HHI transform, horizon, sign, universe, gross, thresholds, trade-size buckets, or minimum trade size.
- No asset-by-asset tuning and no post-result repair.

Mandatory gate order:
1. causality/data-integrity/executable-universe invariants;
2. severe-cost chronological train gate plus four temporal folds;
3. supersevere-cost stress;
4. regime matrix plus tail/concentration/pathology audit;
5. benchmark-envelope comparison;
6. deterministic reproducibility/invariant rerun;
7. only after every preceding gate passes, freeze the exact candidate before any untouched holdout access.

A failure at any mandatory scientific gate permanently rejects this exact Phase124 hypothesis. Infrastructure-only failures may be repaired only when the frozen scientific definition above is unchanged.

## Frozen assets
V16 Frozen and V99 Frozen are read-only and must be hash-snapshotted/verified before and after execution.
