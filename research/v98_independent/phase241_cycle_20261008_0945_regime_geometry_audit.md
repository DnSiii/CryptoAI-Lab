# V98 Independent — 2026-10-08 09:45 BRT: funding-regime and geometric-PnL audit

**Scope:** branch `research/v98-independent-zero`, V98-only historical training (2023–2025). No 2026+ holdout opened, no V99 evidence, no changes to V16/V99, no strategy selection, no gate changes. **Phase241 performance remains unobserved; champion unchanged.**

## 1. Observed PIT funding data integrity (not strategy returns)

Read the five committed V98 Phase206 funding CSVs directly at branch head `e91df8721cc9a1cb04e8b03eb0ee35eb123c8be6`. Normalize each timestamp to its nominal UTC 8-hour settlement slot (observed jitter 0–29 ms). Each asset has exactly 3,288 events during 2023–2025 (16,440 asset-events total), with **no duplicate slots, out-of-order rows, UTC/millisecond mismatches, non-8h interval entries or missing cross-asset slots**. Annual counts: 1,095 / 1,098 / 1,095 slots.

Cross-sectional funding spread = max(rate among five assets) − min(rate), in basis points. It is **not** a realized trading return and does not establish an executable funding arbitrage.

| Calendar fold | Median spread (bp) | p99 spread (bp) | Maximum (bp) | Events with spread >7 bp | >14 bp | >28 bp |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 1.3233 | 19.0775 | 93.7078 | 93/1095 | 24 | 5 |
| 2024 | 1.0000 | 11.2880 | 15.2974 | 71/1098 | 1 | 0 |
| 2025 | 1.0000 | 5.9513 | 34.6350 | 8/1095 | 3 | 1 |

2023's largest spread occurred at **2023-01-04 08:00 UTC**, with SOL −92.7078 bp versus XRP +1.0000 bp. 2025's largest occurred at **2025-10-11 00:00 UTC**, SOL −30.2761 bp versus XRP +4.3589 bp. These are funding-rate observations, not positions held by Phase241.

## 2. Independent clustering/tail stress

A deterministic circular moving-block bootstrap resampled **21 consecutive 8-hour settlements (~7 days)** per block, 3,000 replicates, PRNG seed 20261008, separately within 2023 and 2025. Observed probability of >7 bp cross-asset dispersion fell from **8.493% (2023)** to **0.731% (2025)**: difference **7.763 percentage points**. The block-bootstrap 95% percentile interval for the difference was **[3.014, 13.425] percentage points**; no resampled difference was nonpositive (empirical Monte Carlo fraction 0/3000). This is descriptive historical uncertainty conditional on the sampling scheme, not a trading alpha test, nor proof of independent observations.

Extreme events cluster: 2023 had 93 exceedances in 32 runs, longest run 15 consecutive settlements (120 hours); 2024 had 71 in 28 runs, longest 10 (80 hours); 2025 had 8 in 4 runs, longest 5 (40 hours). Top ~1% of events contributed 13.19% / 5.93% / 9.14% of the annual **sum of cross-asset spread**, respectively. Funding regimes and tail risk are nonstationary; no year or asset may be filtered after observing this evidence.

## 3. Independent geometric-return trap in committed Phase239 (not Phase241)

Recomputed Phase239 2024, frozen spec `idsp_beta336_sp168_k1_h8` directly from the committed V98 `phase239_results.json`:

- Base-cost turnover L1 = 444.6190; additive net asset PnL sum = **+0.0224147161** (2.2415% of initial equity); additive gross/turnover break-even = **7.5041 bp** versus the frozen 7 bp base cost.
- Nevertheless **compounded return = −4.07985%**, Profit Factor **1.00227**, max drawdown **−41.9230%**, positive days **47.54%**. Severe compounded return = **−29.7403%**, supersevere = **−62.3073%**.
- Log-compounded return = **−0.04165408** versus additive net +0.02241472; the difference **0.06406879** illustrates geometric/path volatility drag, not missing funding or a numerical contradiction.
- This cell fails the existing mechanical gate (negative compounded return, DD worse than −35%, positive days below 50%, severe negative) even though additive PnL and hourly PF appear marginally favorable. **Never use additive cost break-even alone to promote a strategy.**

Across committed Phases238–240: 72/72 base-cost spec-year cells have negative compounded returns; Phase239 has the one marginal hourly PF>1 cell above. This reinforces the requirement to retain compounded return, DD, daily-positive fraction, severe/supersevere and concentration diagnostics.

## 4. Execution status and next action

The isolated Phase241 workflow creation was **attempted** this cycle and blocked by the integration safety checks; it was not created, no workflow launched, and no Phase241 result harvested. The existing `phase241_eval.py`, `phase241_validate.py`, frozen preregistration and Phase242 preregistration remain untouched. Next: obtain an authorized V98-only workflow execution path; rebuild the exact pre-2026 canonical bars, run Phase241 twice byte-identically, validate cost/funding reconciliation and every frozen gate. If it fails, reject without rescue; do not use V99 or open holdout.

**Evidence provenance:** `research/v98_independent/data/phase206_funding/*_funding.csv`, `research/v98_independent/phase239_results.json`, and Phase241 preregistration/validator on branch `research/v98-independent-zero` at `e91df8721cc9a1cb04e8b03eb0ee35eb123c8be6`.
