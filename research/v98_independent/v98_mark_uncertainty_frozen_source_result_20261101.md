# V98 Independent — frozen 13,524-event funding-mark envelope uncertainty finding (2026-11-01)

**Decision: PASS_SOURCE_UNCERTAINTY_QUANTIFICATION_ONLY. NO V98 ENGINE APPROVAL.** Precommitted definition: `v98_mark_uncertainty_prereg_20261101.md` at commit `eb80a1a919bd7d62b17f70c7e0c40b2f9440483a`, before computation. The authenticated-source GitHub Actions run [41338522204](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41338522204) completed successfully. Immutable 30-day artifact `v98-independent-mark-uncertainty-source-only-no-pnl` ID **13095859349**, canonical 13,524-event CSV SHA256 `5a95e6abb9bd24d4f225b66c4549c9a0af7f16c8104d3e97c1f624c634d52041`.

## Measured source-only uncertainty

Clean-4 BTC/ETH/BNB/SOL Binance USD-M exposed training December 2022–December 2025. All **13,524 funding asset events** / **3,381 8-hour slots** reconciled against authenticated native rates and official hourly mark envelopes. No interpolation, 2026+, XRP, Phase083, benchmark, holdout or system PnL.

| Diagnostic | Median | P95 | P99 | Maximum |
|---|---:|---:|---:|---:|
| Per-event mark-envelope relative width (bps of mark) | 103.8221 | 335.2266 | 539.1332 | 2,793.7748 |
| Per-slot **hypothetical** funding-cash uncertainty (bps of equity) | 0.01325 | 0.10850 | 0.28639 | **8.97830** |

Second row is the maximum over the four assets per funding slot under a **hypothetical** 0.84 pre-event gross/equity exposure cap, concentrating all exposure in the asset with greatest `abs(funding_rate)*(mark_upper-mark_lower)/mark_lower`. This is a *single-event local bound only* under the stated exposure assumption. It is **NOT** a bound on dynamic portfolio CAGR, future funding, realized PnL, or exact event mark prices. **6/3,381** slots exceed 1 bp of hypothetical equity; **1** exceeds 5 bps; **0** exceed 10 bps. The largest raw mark-width event is SOLUSDT 2025-03-02 16:00 UTC. No candidate selected using these values.

Independent scalar **Decimal** oracle reconstructed all 13,524 events and 3,381 slots with zero receipt mismatches, rejected **4/4** receipt/data tamper controls (interval inversion, rate perturbation, duplicate event, missing event), and the separate local-bound synthetic proof passed **1,000** signed-position cases. Source run, canonical receipt and independent oracle were all executed physically in GitHub Actions, not inferred from unit tests alone.

## Critical-path decision

**Do not wait idle for exact event marks before developing a genuinely distinct seven-slot candidate.** The authenticated conservative worst-side mark envelope supports causal *exploratory training* with explicit mark uncertainty, and any candidate must still pass its preregistered complete-system economic gates, including independent physical cash and severe/supersevere costs. The small typical local funding uncertainty does **not** erase the origin requirement or prove small cumulative strategy impact; a future passing candidate needs separate mark-sensitivity testing with its actual quantities and all funding events.

**Still blocked for exact settlement/final delivery:** 13,524 exchange-origin `/fapi/v1/fundingRate` `markPrice` values with raw response bodies, request URLs, original HTTP Date/headers, UTC capture times, SHA256 and independently attested chain of custody. Direct historical API previously returned HTTP 451. The only acceptable alternative is an **authorized exchange-origin export** with equivalent evidence and independent origin verification, not Binance Vision rate-only CSV, a third-party mirror, or synthetic/hourly mark values. Historical account-specific fees, spread/depth/impact, and untouched future validation also remain independent gates.

**No champion:** All previously rejected V98 architectures remain rejected. No V14/V15/V99 benchmark opened, no V16/V99 Frozen or paper touched, no 2026+ training data, no paper/live trading authorized. This source audit does not complete the seven-slot V98 engine.
