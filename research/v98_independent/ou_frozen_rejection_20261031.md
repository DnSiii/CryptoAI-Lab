# V98 Independent OU — FROZEN REJECTION (2026-10-31)

**Binding decision: REJECT_OU_TRAINING. OU is not a champion.** Never modify OU signs, windows, funding carry rule, weights, thresholds, cost assumptions, exposure, gate values, 2025 treatment, or execution to rescue this rejected architecture. No external V14/V15/V99 benchmark inspected; no 2026+ or contaminated Phase083 holdout accessed; no paper/live mutation.

## Immutable chronological evidence
- Pre-economic architecture and all seven slots preregistered in commit `52b798b8883f1062c017d60e61d7c5d7cdc79602`; OU runner commit `cb39d2717d7d758ebe0df9cbfe1cbd31468ba983`; independent signal oracle `f57f2889ab07924aecf3fd8c695649df93b0f3ff`.
- Original pinned 2022-25 physical execution: [GitHub Actions 41235673815](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41235673815), from commit `843829edc9c04a34a8687514696ef04771caa4f5`. The workflow exits **failure deliberately because OU fails binding economic gates**; the 30 physical cells themselves all settled. Original complete `OU_RESULT_JSON` log receipt copied verbatim into `ou_full_training_frozen_result_20261031.json` (with commit/run metadata appended).
- Source: authenticated Clean-4 Binance USD-M BTC/ETH/BNB/SOL, Dec-2022 warmup, Jan-2023 through Dec-2025 **exposed exploratory TRAINING**, 27,048 hours, 13,524 native signed-rate funding events, 26,303 physically settled hours, 157 weekly decisions, 3 cost tiers, 2 funding orders, 5 books. **Not an untouched validation/holdout.** Exact native event marks are not yet attested; conservative official hourly mark envelopes used.

## Original physical economics (full book, carried-before-fill)
| Cost tier | CAGR modeled 2023-25 | Max DD | USD gross turnover | Final modeled equity from USD10k | Native-rate conservative funding cash |
|---|---:|---:|---:|---:|---:|
| Base (4bps fee +2bps slip) | **-2.8142%** | -53.4107% | 1,699,906.65 | 9,179.10 | -279.19 |
| Severe (10bps+10bps) | **-9.8712%** | -56.9439% | 1,523,224.51 | 7,320.83 | -246.53 |
| Supersevere (15bps+20bps) | **-16.6609%** | -60.1142% | 1,365,999.81 | 5,787.52 | -214.80 |

Base annual returns: 2023 **+31.4143%**, 2024 **-16.0962%**, 2025 **-16.7517%**. Severe: +21.9573%, -22.4986%, -22.5461%. Base fees USD679.96, slippage USD339.98; 512/1096 positive daily observations; 1% daily CVaR -6.8837%; hourly NAV-increment PF 0.99773 (**not trade-level PF**); maximum single-asset gross concentration 100%.

## Binding failures and independent reconciliation
- **30/30 physical cells settled**; independent OU signal+allocator oracle: 157 weekly decisions across five books, **zero mismatches**; independent cash identity 26,303/26,303 hours, maximum error ~1.82e-12 USD; independent fill/fee/slippage/signed-funding oracle: 26,303 hours, 3,287 funding hours, **345 net fill events**, zero mismatches.
- **24 binding economic failures**, separately recomputed from the frozen 30-cell result: four CAGR failures, four turnover failures, two severe DD failures, two severe annual-year failures, four Opportunity marginal failures, four Stress/Recovery marginal failures, four Relative Value 2025 annual marginal failures. Independent recomputation matched the original list and order exactly.
- Base full-minus-ablation marginal log wealth: Opportunity **-0.015388**, Relative Value **+0.095088**, Stress/Recovery **-0.008880**. Relative Value's aggregate gain cannot override its negative 2025 annual marginal and complete-system failures. Growth Core alone base CAGR -4.933%; OU fails even with an apparently beneficial RV sleeve. No post-result rescue permitted.

## Remaining delivery gates
1. **Exact funding mark source:** 13,524 official Binance USD-M `/fapi/v1/fundingRate` event `markPrice` values with raw responses, per-page HTTP request URL/UTC timestamps/headers, SHA256, and independently verified transport provenance. Counts: 9,144 for Dec-2022–Dec-2024 (4x2,286), 4,380 for 2025 (4x1,095). Existing GitHub network attempts have HTTP 451/202/400 or timeout; authorized exchange export with chain of custody is the alternative. The new `v98_exact_funding_full_history_ingest.py` can enforce the 2022-25 *content* contract once files exist, but cannot prove origin or manufacture marks.
2. **Genuinely distinct viable complete seven-slot V98**, preregistered and passing chronological internal training with severe/supersevere costs and marginal contribution.
3. **Untouched prospective independent validation and later final holdout** after internal freeze; exposed 2025 and contaminated Phase083 are ineligible. Only after those gates may external V14/V15/V99 comparisons be opened. No real/paper trading authorization.

**Next:** abandon OU permanently, preserve frozen original receipt, and pursue a genuinely different economic mechanism; continue authorized exact-mark source acquisition independently.
