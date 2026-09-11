# V99 R105 — ALL-REGIME STRUCTURAL FINDINGS

Status: DIAGNOSTIC BASELINE ONLY. No engine promotion. Frozen V16 and V99 Frozen remain untouched.

## Executive verdict

- **R64: REJECTED** under the new all-regime standard.
- **R98: BASELINE ONLY / NOT PROMOTED** under the new all-regime standard.
- R98 is already a very strong growth engine relative to V13/V14/V15/V16, but it does not dominate the benchmark envelope on trade-quality and downside-quality dimensions.
- The rebuild should preserve the growth-producing core behavior while replacing architecture that creates oversized losers, tail damage, global/side-blind risk reactions, and regime-specific weaknesses.

## Common-history global result

The R105 diagnostic replay reports R98:

- ROI: **331.1804x = +33,118.04%**
- terminal multiple: **332.1804x**
- fixed R$10,000 baseline profit: **R$3,311,804.28**
- CAGR: **138.05%**
- max drawdown: **-32.18%**
- worst day: **-11.55%**
- positive-day ratio: **48.73%**
- positive days: **1,191**
- closed trade episodes: **2,437**
- winning trades: **650**
- trade win rate: **26.67%**
- profit factor: **1.695**
- average winning trade: **+2.637%**
- average losing trade: **-0.566%**
- payoff ratio: **4.661**
- max losing-trade streak: **28**
- max negative-day streak: **13**
- rolling 30d positive rate: **59.17%**
- rolling 90d positive rate: **82.38%**
- rolling 90d p10 return: **-8.36%**
- rolling 90d dispersion: **30.32%**

R98 beats the V13/V14/V15/V16 metric-by-metric envelope in **10 of 19** tracked global dimensions.

## Metrics R98 already owns or ties

Against the best raw value among V13/V14/V15/V16:

- ROI: R98 331.1804x vs V14 174.6203x — **PASS**
- absolute profit on R$10k: R98 R$3.312M vs V14 R$1.746M — **PASS**
- CAGR: 138.05% vs V14 116.43% — **PASS**
- trade win rate: 26.67% vs V15 22.51% — **PASS**
- winning trades: 650 vs V15 508 — **PASS**
- positive-day ratio: 48.73% vs V15 48.73% — **TIE/PASS**
- positive days: 1,191 vs V15 1,191 — **TIE/PASS**
- rolling 30d positive rate: 59.17% vs V14 57.64% — **PASS**
- rolling 90d positive rate: 82.38% vs V14 78.22% — **PASS**
- rolling 90d p10 return: -8.36% vs V13 -8.89% — **PASS**

## Metrics that block promotion

- profit factor: R98 **1.695** vs V13 **1.740**
- average winning trade: R98 **+2.637%** vs V13 **+3.976%**
- payoff ratio: R98 **4.661** vs V13 **6.468**
- max drawdown: R98 **32.18%** vs V13 **29.87%**
- worst day: R98 **11.55%** vs V16 **9.47%**
- average losing trade: R98 **0.566%** vs V16 **0.379%**
- max losing-trade streak: R98 **28** vs V13 **22**
- max negative-day streak: R98 **13** vs V13 **12**
- rolling 90d dispersion: R98 **30.32%** vs V13 **19.89%**

This pattern is important: R98 already wins on growth, trade hit rate and rolling positive frequency. The main remaining gap is **distribution quality** — winners are smaller than the best benchmark, losers are materially larger than the best benchmark, tail days are worse, and losing/negative sequences are longer.

## Holdout result

R98 holdout:

- ROI: **10.5385x = +1,053.85%**
- CAGR: **151.90%**
- max drawdown: **-29.73%**
- worst day: **-9.17%**
- positive-day ratio: **49.59%**
- closed trades: **810**
- winning trades: **206**
- trade win rate: **25.43%**
- profit factor: **1.766**
- average winner: **+2.965%**
- average loser: **-0.572%**
- payoff: **5.179**
- rolling 30d positive rate: **57.42%**
- rolling 90d positive rate: **84.26%**

Best holdout benchmarks include:

- ROI: V15 **+804.06%**
- positive-day ratio: V13 **50.31%**
- profit factor: V16 **1.880**
- average winner: V13 **+4.623%**
- payoff: V16 **7.464**
- max drawdown: V13 **28.81%**
- worst day: V16 **8.34%**
- average loser: V16 **0.343%**
- max losing-trade streak: V13 **22**
- rolling 90d dispersion: V16 **17.80%**

R98 wins **9 of 19** global envelope dimensions on holdout. The growth advantage therefore survives holdout, while the quality/downside gap also survives holdout.

## Friction stress

### Severe costs

R98 ROI: **138.1688x = +13,816.88%**
Best V13-V16 ROI: V15 **74.6976x = +7,469.76%**

R98 remains materially ahead on growth but passes only **8 of 19** global envelope dimensions because trade-quality and downside-quality gaps remain.

### Super-severe costs (1.5x severe)

R98 ROI: **38.3874x = +3,838.74%**
Best V13-V16 ROI: V15 **24.0697x = +2,406.97%**

R98 remains growth-superior even under this stress, but again passes only **8 of 19** global envelope dimensions. Rolling 90d p10 also falls behind the best benchmark at this friction level.

## Regime coverage

Causal regime labels use only information available before the attributed outcome.

Directional coverage:

- BEAR: **39.07%**
- SIDEWAYS: **30.47%**
- BULL: **26.78%**
- UNKNOWN warmup: **3.68%**

Volatility coverage:

- LOW_VOLATILITY: **64.22%**
- HIGH_VOLATILITY: **34.55%**
- UNKNOWN warmup: **1.23%**

## R98 by directional regime

### BULL

- ROI: **+453.52%**
- trade win rate: **27.99%**
- positive days: **52.40%**
- profit factor: **1.731**
- max DD: **40.95%**
- worst day: **11.55%**

R98 beats benchmark-envelope ROI and win rate, but loses on PF, winner size, loss size, payoff, DD, worst day and losing-trade streak.

### BEAR

- ROI: **+115.96%**
- trade win rate: **29.65%**
- positive days: **44.45%**
- profit factor: **1.404**
- max DD: **34.70%**
- worst day: **11.38%**

R98 again beats benchmark ROI and trade win rate, but quality/tail metrics remain materially weaker.

### SIDEWAYS

- ROI: **+1,555.79%**
- trade win rate: **21.82%**
- positive days: **52.44%**
- profit factor: **1.865**
- max DD: **23.08%**
- worst day: **8.93%**

This is R98's strongest directional regime in compounded return. It beats the benchmark envelope on ROI, win rate and positive-day ratio, but not on PF, winner size, loser size, payoff or downside tails.

## R98 by volatility regime

### HIGH VOLATILITY

- ROI: **+704.86%**
- trade win rate: **29.02%**
- positive days: **48.43%**
- profit factor: **1.429**
- max DD: **35.50%**
- worst day: **11.38%**

R98 beats envelope ROI, trade win rate and PF here, but loses on winner size, loser size, payoff and downside quality.

### LOW VOLATILITY

- ROI: **+4,027.17%**
- trade win rate: **25.32%**
- positive days: **49.52%**
- profit factor: **1.840**
- max DD: **33.72%**
- worst day: **11.55%**

R98 beats envelope ROI, trade win rate and positive-day ratio, but loses on PF, payoff, winner/loser size and downside metrics.

## Critical interaction regimes

The independent BULL/BEAR/SIDEWAYS and HIGH/LOW summaries hide an important interaction.

### BEAR + HIGH VOLATILITY

Full-history R98 ROI: **-7.31%**.

This is the key regime that violates the new mission. Even though aggregate BEAR and aggregate HIGH_VOL are positive, their intersection is negative. All V13-V16 benchmarks are also negative in this full-history cell, but that is not acceptable for the new V99 goal.

R98 still has the best ROI among the compared engines in this cell (-7.31% vs best benchmark V14 -10.71%), and it has strong trade win rate/PF relative to the benchmarks. The failure is therefore not simply “more losing trades”; it is the damage distribution and path behavior inside violent bear episodes.

### BULL + LOW VOLATILITY

R98 ROI: **+55.62%** vs V14 **+81.28%**.

This is a second important growth gap. R98 loses the benchmark envelope on ROI and most quality/downside metrics. The rebuild needs a cleaner low-vol trend sleeve instead of relying only on the current hedge/expansion router.

### SIDEWAYS + HIGH VOLATILITY

R98 ROI: **+116.64%** vs V15 **+138.59%**.

R98 is positive but loses the ROI envelope and most quality metrics. This points to a need for a dedicated high-vol relative-value / fast-reversion or breakout-failure sleeve rather than one global behavior.

### SIDEWAYS + LOW VOLATILITY

R98 ROI: **+664.32%** vs V15 **+499.21%**.

R98 is very strong here, but still trails V13/V16 on PF, winner/loser quality and downside tails. The rebuild should preserve this compounding behavior while improving trade distribution.

## Architectural implications

1. **Do not solve the remaining gaps by shrinking R98 globally.** Growth is already the strongest part of the system.
2. **Recover the side-aware R3/R4 principle.** A crash must reduce the losing/misaligned long side without automatically neutralizing profitable shorts; a squeeze must do the inverse.
3. **Replace R37/R55-style `-sign(net)` hedge routing.** Portfolio net direction is not a sufficient proxy for which side is wrong.
4. **Separate alpha from risk.** The existing R73/R98 lineage is primarily hedge/risk/exposure routing over a V15-derived target stream.
5. **Build native sleeves and measure them independently:** trend, high-vol breakout/impulse, sideways relative-value/reversion, and carry/positioning.
6. **Target the actual weak interactions:** BEAR+HIGH_VOL first; then BULL+LOW_VOL and SIDEWAYS+HIGH_VOL.
7. **Keep the catastrophic global breaker only for solvency/liquidity emergencies.** Normal risk control becomes side-aware and sleeve-aware.
8. **The new promotion gate must preserve growth while improving trade distribution:** smaller average loser, larger average winner, higher PF/payoff, shorter losing streaks, smaller worst day/DD and lower rolling dispersion.

## Next development boundary

The next structural candidate should be built as one coherent R106 research program, not dozens of micro parameter revisions. Its internal phases are:

- native sleeve attribution;
- train-only sleeve/regime eligibility;
- causal router;
- side-aware/P&L-aware risk controller;
- integrated portfolio replay;
- holdout + severe/super-severe + regime matrix + chronological folds + random windows + tail-dependency tests.

No component is promoted because it improves one metric in-sample. The final target is a candidate that materially exceeds R98 growth while closing as many benchmark-envelope quality gaps as possible and eliminating the negative BEAR+HIGH_VOL cell.
