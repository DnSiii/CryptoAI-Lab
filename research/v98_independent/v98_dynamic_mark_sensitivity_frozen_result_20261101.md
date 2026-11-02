# V98 Independent — frozen dynamic funding-mark sensitivity on rejected PU (2026-11-01)

**Decision: PASS_DYNAMIC_MARK_SENSITIVITY_NOT_ENGINE. NO V98 CANDIDATE APPROVED.** This is an actual historical *physical portfolio replay* to quantify the importance of unavailable exact exchange settlement marks, not an alpha, validation, candidate selection, strategy rescue, live/paper authorization, or rigorous bound on achievable CAGR. The PU engine was **permanently rejected before this experiment** and remains rejected.

## Immutable execution / provenance
- Precommitted scope, method, and anti-promotion rules: `v98_dynamic_mark_sensitivity_prereg_20261101.md`, committed at `aee3a10e49edb0a53fa0041ce49c04db28c3c166` before implementation or historical run.
- Final [GitHub Actions historical physical execution](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41369534665), commit `2f08c590e50b3b51f25b1e5282e33ba35a343b32`: **SUCCESS**. Immutable 30-day artifact `v98-trade-lot-historical-six-cell-receipt`, ID **13108711435**, ZIP digest `sha256:7b17f4786e7f6e17a89d6a8144a88542d6a00c1353d33ecbe352f6383041e320`.
- SHA-pinned official Clean-4 BTC/ETH/BNB/SOL Binance USD-M 1h exposed training Dec-2022–Dec-2025, 27,048 source hours, 13,524 funding asset events. The physical book starts after 744-hour warmup: **26,303 ledger hours and 13,148 funding asset events per paired path**. No 2026+, XRP, contaminated Phase083, external V14/V15/V99 benchmarks, Frozen or paper.
- Existing PU full-book 157 weekly target decisions, unchanged across 3 cost tiers and 2 funding orders. Six original conservative paths and six *new* favorable-side counterfactual paths independently reconstructed hourly, with stateful NAV, net fills, forced safety rebalancing, fees, slippage and funding. No post-result strategy parameter or threshold change.

## Historical physical result — paired funding mark sensitivity

Conservative path charges funding payers at the upper official hourly mark envelope and credits receivers at the lower. Favorable counterfactual reverses those sides, re-running the entire stateful physical portfolio. **Favorable marks are not executable prices and are not a rigorous dynamic terminal-NAV upper bound.** The following figures are measured on the **rejected PU fixture**, not returns for a deliverable engine.

| Costs / funding order | Worst-side terminal NAV (USD) | Favorable terminal NAV (USD) | Paired terminal NAV difference (USD) | Paired CAGR difference (percentage points) |
| --- | ---: | ---: | ---: | ---: |
| Base / carried-before-fill | 14,896.97 | 14,965.21 | +68.24 | +0.17409 |
| Base / new-after-fill | 14,897.57 | 14,965.78 | +68.20 | +0.17397 |
| Severe / carried-before-fill | 12,823.25 | 12,882.09 | +58.84 | +0.16588 |
| Severe / new-after-fill | 12,823.75 | 12,882.56 | +58.81 | +0.16578 |
| Supersevere / carried-before-fill | 10,989.98 | 11,040.49 | +50.51 | +0.15782 |
| Supersevere / new-after-fill | 10,990.41 | 11,040.89 | +50.48 | +0.15772 |

Under severe costs with carried-before-fill, 2024 remains negative (**-20.87% worst / -20.76% favorable**) and 2025 remains negative (**-7.29% worst / -7.23% favorable**). Severe maximum drawdown remains about **54.4%**. The optimistic counterfactual therefore **does not repair PU's binding economic failures**. Neither this observed small difference nor the favorable path may be used to claim that exact event marks are immaterial for an as-yet untested V98 architecture.

## Independent checks
- Each of six favorable paths completed all **26,303** hourly cash ledger rows, including all **13,148** modeled funding asset events after warmup. Independent per-hour fee/slippage/signed-funding reconstruction and independent cash identity reported **zero mismatches** in all six paths.
- The new receipt-only oracle, which does not import the strategy or production physical engine, independently verified **12 annual NAV identities**, six paired NAV/CAGR/turnover identities and detected **4/4 deliberate receipt tamper categories** (terminal NAV delta, funding event count, CAGR, unauthorized promotion). This oracle checks arithmetic, **not independent exchange-origin source custody**.
- Signed long/short synthetic tests exercise both funding orderings, positive/negative rates, zero-rate and no-event masks, modified mark bounds, inverted intervals and altered funding ordering. A separate local randomized signed-envelope identity check passed 40,000 cases; it is *not* historical performance evidence.
- All altered repository files are restricted to `research/v98_independent/`. Existing V16 Frozen, V99 branch/workflows/reports/paper and future holdout untouched.

## Binding decision / next critical work
**No V98 champion.** Do not reopen PU or promote the favorable counterfactual. The difference between two envelope-side physical paths is small for this rejected fixture, so missing exact marks should **not prevent research on a genuinely distinct preregistered growth mechanism**; it still prevents exact native-settlement attestation for any final candidate. Do not launch cosmetic variations of rejected momentum, residual, reversal or gross-cap allocators without an executable economic counterparty/source.

**External evidence still required:** all 13,524 exchange-origin `/fapi/v1/fundingRate` historical settlement `markPrice` values with raw request URLs, HTTP Date headers, UTC capture times, response bytes, SHA256 and independently verifiable chain of custody (or equivalent authorized Binance-origin export). Historical API previously returned HTTP 451. Independently, account-specific historical fee tiers, executable bid/ask and depth/impact, collateral/borrow constraints and a genuinely distinct seven-slot V98 with positive severe-cost net growth and marginal sleeve contributions must be established. Only after a new complete V98 candidate is internally frozen and passes chronological training plus separate validation may external V14/V15/V99 benchmarks be opened. Untouched future holdout, independent execution checks and prospective paper remain additional delivery gates. No promise of returns or real trading.
