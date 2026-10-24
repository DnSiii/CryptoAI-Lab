# V99 — 2026-10-24 authenticated executable options archive dependency (10:47 BRT cycle)

**NO PROMOTION / DATA_ONLY/HOLD.** This is a direct attempt to unlock the sole executable-quote path for the existing I1 structural hypothesis, **not** a new alpha phase, a trading backtest, or evidence of profit. I1 has 4/5 positive gross variance folds but a fragile ETH leave-one-fold-out mean and no tradable execution evidence. Rejected C1/C2/D1/E1/F1/G1/H1 remain rejected.

## Actual GitHub execution

- Added `research_tools/v99_r106_tardis_authenticated_entitlement.py` and `.github/workflows/v99-r106-options-authenticated-entitlement.yml` on **research/v99-r106-native-all-regime-engine** only. Uses documented `Authorization: Bearer` header; secret never printed or put in URL; bounded **at most one byte per request** for three TRAIN-only non-sample dates: 2021-12-10, 2022-06-15, 2023-09-29. No market data downloaded if no credential exists.
- [Actions 40099792210](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40099792210) **SUCCESS** with actual machine-readable status **`BLOCKED_NO_AUTHENTICATED_ARCHIVE_ENTITLEMENT_CONFIGURED`**: `TARDIS_API_KEY` is **not configured for this workflow**. This is an authentication/configuration finding, **not** proof that historical data do not exist or that any authenticated plan would cover them.
- Independent CI guard verified no holdout/validation access, no orders, no native fills, and no full five-fold coverage claim. Git diff from prior branch head `85fbce1` changes only these two research paths; frozen/paper/legacy/public dashboards unchanged.

## Concrete source alternative and its limitations

- **Tardis** official dataset API docs: https://docs.tardis.dev/downloadable-csv-files/api — the full `deribit/quotes/YYYY/MM/DD/OPTIONS.csv.gz` source requires authenticated entitlement on non-first-of-month dates. Previous anonymous probes received 403. Even a working key must be separately tested for **2021-12-09 through 2023-09-30** complete BTC/ETH option-chain coverage; access on three dates alone is insufficient.
- **Amberdata** official Deribit product description: https://www.amberdata.io/deribit-market-data — advertises options historical data from **2021-05-21**, plus historical options order-book events and snapshots endpoints. This is a credible alternative **to request a representative BTC+ETH sample and a dated per-instrument coverage manifest from**; the website does not establish that all option order-book snapshots have continuous 2021–2023 coverage, native arrival timestamps, sufficient depth, or licensed access at acceptable cost. Do not purchase before those checks.
- **CoinDesk Data** official options L2 minute snapshots endpoint: https://developers.coindesk.com/documentation/data-api/options_v1_historical_orderbook_l2_snapshots_minute — documents bid/ask sizes but a `to_ts` limit no older than two years from the current time; **its public REST contract does not cover this 2021–2023 TRAIN in October 2026**. Enterprise archival delivery would require separate confirmation and licensing; not a free workaround.
- **Volar** BTC-only historical archive does not cover ETH 2021–2023 or size/arrival fields for the existing two-asset design. No purchase.

## Exact dependency for a complete economic TRAIN

Authorized historical **BTC and ETH Deribit option bid/ask and displayed sizes**, original exchange timestamps **and local arrival timestamps**, instrument/strike/expiry/contract multipliers, completeness and gap manifest across **[2021-12-09, 2023-10-01)**; historical venue fee and settlement/margin/liquidation rules; separately documented size-aware hedging execution assumptions and an independent accounting oracle. Historical hypothetical orders cannot have authentic account fills; a modeled fill must be labeled as modeled. Account-specific 2021–2023 fee tier remains unverified. A source entitlement alone does **not** prove economic edge or authorize validation.

**Next real action:** if authorized archival credentials become available, run the bounded entitlement check then request complete coverage manifests and independent source samples before any I1 options engine. In their absence, do not invent quotes, optimize rejected engines, unlock [2023-10-01,2024-01-18) validation or >=2024-01-18 holdout, or advertise a finished V99. No orders. **NO PROMOTION.**
