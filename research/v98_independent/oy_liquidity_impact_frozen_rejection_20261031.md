# V98 Independent OY — FROZEN ECONOMIC REJECTION (2026-10-31)

**Binding decision: REJECT_OY_TRAINING. No complete V98 champion.** OY's liquidity-conditioned signed price-impact seven-slot portfolio was preregistered before economic results and failed 22 binding gates. Never change OY signs, lookbacks, volume thresholds, gross limits, costs, execution order, or sleeve weights to rescue it. The result is an exposed historical simulation, not forward performance, paper or real PnL.

## Immutable evidence
- Preregistration commit `dcf0cb6be612c9bdf46635d6c4749c229ba81591`: `oy_liquidity_impact_prereg_20261031.md`.
- First real full-history physical engine run: [GitHub Actions 41253871357](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41253871357), pinned trigger commit `e8b48120139fa3365212b792b91e357ccfb5306c`. The job's final failure is **the deliberate binding economic rejection**, not a crashed 30-cell computation.
- Original stdout `OY_RESULT_JSON` payload frozen unmodified in `oy_full_training_frozen_result_20261031.json`, receipt commit `7f7efc1cd0db3ab8e2cec71d18515ec41b8bb4c2`; original run artifact ID `13062621751`.
- Separate [GitHub Actions independent frozen receipt audit 41253963691](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41253963691): **PASS_INDEPENDENT_OY_RECEIPT_RECONCILIATION_NOT_ENGINE**; all 30 cells, 60/60 arithmetic checks, all 22 economic failures rederived, max arithmetic error 0.

## Modeled 2023–2025 full-portfolio results
Initial hypothetical USD10,000; native funding rates and official worst-side 1h mark envelopes (not exact exchange settlement marks), carried-before-fill:

| Cost tier | CAGR | Max DD | USD turnover | Final hypothetical USD | Annual 2023 / 2024 / 2025 |
|---|---:|---:|---:|---:|---|
| Base 4bps fee + 2bps slippage | **-3.39297%** | -54.35945% | 1,050,503.95 | 9,016.04 | +31.8744% / -13.6323% / -20.8403% |
| Severe 10+10bps | **-7.34404%** | -56.96540% | 991,855.40 | 7,954.22 | +26.9314% / -17.5150% / -24.0281% |
| Supersevere 15+20bps | **-11.40741%** | -60.39547% | 933,757.37 | 6,952.74 | +21.8295% / -21.4912% / -27.3083% |

Base 389/1,096 positive days; hourly NAV-increment PF 0.99686, payoff 1.00411, hourly win rate 49.81886% (**not trade-level PF**). Base full-minus-ablation net log growth: Opportunity **-0.00210246**, Relative Value **0**, Stress/Recovery **+0.00123188**; severe: **-0.00522173**, **0**, **+0.00076528**. All three fail the binding +0.02 marginal gate, and the complete base CAGR underperformed its core-only ablation (-3.393% vs -3.185%).

## Independent execution and decisive failures
- Five books x three cost tiers x two funding orders: **30/30 physical cells completed**.
- Causal independent loop-based price-impact/allocator oracle: **157 weekly decisions**, 5 books, zero mismatches; synthetic future mutation test passed.
- Independent hourly cash identity: **26,303 hours**, zero discrepancies (max numerical error 1.82e-12 USD).
- Independent fill/fee/slippage/signed-funding oracle: **151 net fill events**, **3,287 funding hours**, zero discrepancies (max 1.78e-15 USD).
- Independent frozen economic audit: **22 binding failures**, including base/severe CAGR, base turnover, severe DD, severe negative calendar years and all optional sleeve marginals, rederived without strategy imports.
- OY is **permanently rejected**. Neither mechanically correct accounting nor economic rejection makes 2025 an independent validation sample.

## Critical path, preserved firewalls
The repeated failure mode is economically weak or harmful optional sleeves, inadequate compound growth and unstable annual returns, **not** a lack of synthetic unit tests. Next V98 candidate must use a genuinely distinct causal economic mechanism with independently positive full-system sleeve marginal contribution, not OY parameter rescue.

Exact settlement funding still lacks **13,524** exchange-origin `markPrice` objects from Binance USD-M `/fapi/v1/fundingRate` (BTC/ETH/BNB/SOL, 2022-12 through 2025-12; 9,144 through 2024 plus 4,380 in 2025), raw original HTTP pages, timestamps, pagination, SHA256 and independently auditable transport/exchange origin. GitHub hosted Linux/macOS returned HTTP451 or other failures; the authorized-network exchange-origin export with chain of custody is the alternative. Existing V98 capture, independent chain audit and strict importer cannot certify absent real data. Separate **untouched prospective chronological validation and final holdout** remain required after a viable internal freeze; 2025 already exposed. No 2026+ training, XRP, Phase083, V14/V15/V99 benchmarks/internals, V16/V99 Frozen, V99 workflows/reports/paper or real operation was touched or authorized.
