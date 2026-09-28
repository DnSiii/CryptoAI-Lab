# V99 R106 — Phase175 orthogonal-source feasibility audit

Date: 2026-09-28
Scope: DATA/INTEGRITY ONLY; no PnL and no holdout access.

## Work performed

1. Re-audited the R106 frontier policy and Phase169–174 closure. The next admitted alpha must introduce source-level independent information; another OHLCV/positioning/taker/macro transform is prohibited.
2. Searched the repository for liquidation-history and options-implied-volatility implementations. No prior R106 implementation was found for either source family.
3. Audited current research data inventory. The only persisted external research dataset is the Phase168 TRAIN-only daily macro snapshot; no liquidation or options-history snapshot exists.
4. Checked current first-party exchange documentation for historical liquidation feasibility. Binance documents force-order endpoints as USER_DATA/account-specific endpoints; these do not constitute a public historical market-wide liquidation archive suitable for the intended 2021–2024 reproducible TRAIN source. Therefore Candidate A is not admitted from Binance REST.

## Decisions

### Candidate A — market-wide historical liquidation events

Status: NOT ADMITTED YET.

Reason: the first-party Binance endpoints found are user/account force-order history, not a public market-wide historical liquidation archive. Using them would change the economic object and would not provide the required cross-market forced-flow history. Live liquidation streams are also insufficient because they cannot reconstruct the frozen TRAIN period reproducibly.

### Candidate B — historical options IV surface

Status: FEASIBILITY PENDING.

Repository inventory shows no existing dataset or implementation. It remains orthogonal in principle, but no source is admitted until a documented historical archive proves point-in-time TRAIN coverage and deterministic acquisition. No alpha specification is authorized yet.

## Anti-overfit consequence

Phase175 remains a data/integrity phase. No backtest, sign selection, threshold, lookback, asset filter or PnL was run. This is intentional: inventing an alpha before proving the new source would spend hypothesis budget on unavailable/contaminated information.

## Next executable work

Continue source feasibility on the options-volatility candidate and other genuinely new point-in-time archives. Admit exactly one source only after provenance/coverage tests pass; then preregister the alpha in a new commit before observing any PnL. If no source meets the gate, cancel Phase175 pre-PnL rather than fall back to rescue tuning.

V16 Frozen and V99 Frozen remain untouched. Causal t-1, chronological TRAIN-only selection, untouched holdout, temporal folds, severe/supersevere costs, regime matrix, benchmark envelope and reproducibility remain mandatory.
