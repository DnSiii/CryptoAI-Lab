# V98 Independent BZ — pre-result liquidity-confirmed trend-continuation source preregistration (2026-10-24)

**Purpose:** Test one distinct source-level *economic* mechanism before committing to another seven-slot full engine. BZ is a **volume-confirmed closing-high continuation** hypothesis, not BY's signed-funding-dislocation, not a recycled rejected engine, and not itself a tradable portfolio. No V14/V15/V99 signals/parameters/results, no 2025 future holdout, no 2026+, no XRP, no Phase083.

## Immutable signal and evaluation contract — before economic observations

Read only original SHA-pinned Dec2022–Dec2024 Clean-4 Binance USD-M 1h BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT and 9,144 native signed funding events via `phase1260_aj_authenticated_source_digest.load_official`. Fix hourly integer t = 2160, 2328, 2496, ... with 168h steps. For each asset at completed t close, compute:
- 72h log price return `log(close[t]/close[t-72])`;
- 336h log price return `log(close[t]/close[t-336])`;
- trailing 24h quote volume sum over hours `[t-23,t]`;
- median of all completed contiguous 24h quote-volume sums in `[t-335,t-24]`, i.e. windows ending at or before t-24 (strictly prior to current 24h block);
- prior 168h maximum *close* from `[t-168,t-1]`.

Eligible **LONG ONLY** if 72h log return > 0.02, 336h log return > 0, `close[t] > max(close[t-168:t])`, and latest 24h quote volume / prior median 24h volume > 1.10. If the prior median is zero, ineligible. Choose at most one asset with maximum `72h log return * min(volume_ratio,3)`, ties by fixed BTC,ETH,BNB,SOL order. If none, stay flat. Enter at **actual open t+1**, exit at **actual open t+169**, no overlapping positions. Skip epochs whose exit is outside 2024; do not access 2025 for exit. The closing-high/volume criterion seeks demand confirmation rather than carry receipt; no post-result modification or window/sign/threshold rescue.

Compute actual-open long price PnL per entry USD, conservative **native funding** at each scheduled event in [entry,exit), marked HIGH when the long pays funding and LOW when it receives, and three original fee/slippage tiers BASE 0.001, SEVERE 0.005, SUPERSEVERE 0.015 per side applied to entry+exit notional. Compute prior-only authorized notional using existing ENTRY_FRACTION, PARTICIPATION, STRESSED_QUOTE_FRACTION, EXIT_FRICTION_MULTIPLIER and prior 336h minimum 24h quote-volume window. Report all events, adverse intrahold low excursion, years, counts, per-asset, capacity, gross price, signed funding, friction and net. Unit episode sums are **not** CAGR, compounded NAV, execution fill proof or system PnL.

## Gate, no hindsight rescue

Advance BZ to a **new separately preregistered full seven-slot engine** only if each 2023 and 2024 has >=4 selected episodes AND positive **severe net sum of per-entry USD episode returns** in both years. Always report base, severe and supersevere. Reject permanently if either year fails; do not alter thresholds, selection, holding window, direction, costs or sign. A source pass is not an engine pass: full seven-slot physical inventory, costs, 90-cell historical matrix, marginal ablations, reproducibility, independent native-event replay and separate untouched future validation remain mandatory before any benchmark comparison. No live orders or forward PnL claims.

## Reproducibility

Run on Ubuntu 22.04 and 24.04 with pinned original Clean4 artifact from run 40064588623, exact canonical receipts, independent auditor separately recomputing each signal, native event, cashflow, fee and capacity without importing BZ source code. Reject discrepancies; numeric diagnostics may be rounded **only after** raw signal selection, with raw decision and cashflows unchanged. All repository changes must remain inside `research/v98_independent/` and V98-only `.github/workflows/v98-independent-*`.