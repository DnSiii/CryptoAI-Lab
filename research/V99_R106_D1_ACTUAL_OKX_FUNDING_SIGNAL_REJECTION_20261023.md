# V99 R106 D1 — decisive actual-OKX TRAIN signal falsification (2026-10-23)

**Decision: D1 BASIS-CARRY ARCHITECTURE PERMANENTLY REJECTED FOR THE FROZEN RULES. NO RETUNE. DATA_ONLY/HOLD — NO PROMOTION.**

This is an **original-first-party historical funding / causal signal** result, **not** an economic backtest, ROI, actual account PnL, fill verification, or exchange-certified profit. Do not count this as passing the economic gates. The rejection is based on a stronger prerequisite failure: the preregistered entry rule cannot activate in four later chronological TRAIN folds, even under a deliberately optimistic funding-only upper envelope that ignores the restrictive basis/cadence filters.

## What was actually executed

- GitHub Actions [40029490278](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40029490278) re-downloaded the original 2021-12-09..2023-10-01 TRAIN price/funding artifacts, independently verified the 636 original four-leg hourly price pages and 38 original OKX monthly funding ZIPs, then evaluated **actual frozen D1 daily entry decisions** for both preregistered cost scenarios. All tests completed. No orders or PnL.
- GitHub Actions [40029568809](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40029568809) repeated the full source replay and **independently recomputed all three-funding-fix rolling maxima and threshold crossings directly from original OKX ZIP bytes**, without using the strategy probe parser. Independent source and decision checks passed.
- The frozen D1 projected 24-hour funding signal is exactly **sum of the last three published funding rates**. The frozen fee-responsive entry criterion requires projected funding strictly **greater than 0.0056 (0.56%) under severe**, or **greater than 0.0112 (1.12%) under supersevere**. It also requires all three rates positive and absolute spot/perp basis below 1%; the independent optimistic upper bound ignores those extra vetoes and therefore cannot be more restrictive than D1.

## Actual original-source result (no modeled returns)

| TRAIN fold | BTC optimistic maximum 24h funding | ETH optimistic maximum 24h funding | BTC/ETH triples crossing severe threshold |
| --- | ---: | ---: | ---: |
| 1 (partial funding source) | 0.0004600114136138 | 0.0003469105721127 | 0 / 0 |
| 2 | 0.0007199016458341 | 0.0006799065291671 | 0 / 0 |
| 3 | 0.0005044424985986 | 0.0010649220050214 | 0 / 0 |
| 4 | 0.0013886789934726 | 0.0019702790311950 | 0 / 0 |
| 5 | 0.0005082932335083 | 0.0006869226874356 | 0 / 0 |

All **1,735** consecutive original published three-settlement windows **per instrument** (within original TRAIN, across the five folds) fell below the **0.0056 severe threshold**; naturally none exceeded the higher supersevere threshold. The largest ETH 24h projected value in any observed fold was **0.0019702790311950**, still only ~35.2% of the frozen severe entry threshold. This upper-bound proof does not depend on spot/perp price, execution assumptions, or fitting model parameters.

The strict original D1 causal 00:00 UTC decision replay found **0 qualifying entry days** for either asset under either cost scenario, including **428 daily timestamps where both assets' last three original fixes passed the exact 8h cadence/staleness check**. The original D1 `decide()` implementation was separately called and cross-checked for **856 scenario-specific paired decisions**; no discrepancies. Missing/off-grid funding caused additional vetoes and was **never treated as zero**.

## Scientific interpretation and caveats

- Official OKX downloadable funding history begins in **March 2022** (see [OKX historical-data page](https://www.okx.com/en-br/historical-data)); the 2021-12 to 2022-02 portion of fold 1 is genuinely **UNKNOWN**, not an observed zero. The original five TRAIN folds and 2023-10-01 cutoff were **not changed**.
- Folds **2, 3, 4 and 5** lie entirely inside the archived funding source period. Their **optimistic** three-fix funding upper bounds are all below the original entry threshold for both assets. Thus the frozen D1 architecture cannot generate entry opportunities in those four folds **conditional on the archived post-March-2022 funding source being complete**. No historical execution or native-fee evidence could rescue the fixed entry rule; it can only further constrain profitability.
- Consequently D1 cannot meet a positive multi-fold growth requirement on the archived source, and there is no rational justification to invest further in D1's missing-fee/fill integration, optimize its entry threshold, shorten its TRAIN after seeing the result, or open sealed validation. **Reject the candidate; do not mutate its rules or recycle it as a winner.**
- This does **not** establish that every alternative complete architecture fails. It does **not** certify a historical account, synthetic ROI, 2021-12 funding, or exchange fills. No ROI was calculated. C1 and other previously rejected architectures remain rejected.
- The public V99 Research status stays **DATA_ONLY/HOLD — NO PROMOTION**. V16 Frozen, V99 Frozen, paper/results, legacy champion, sealed validation [2023-10-01, 2024-01-18), and final holdout >=2024-01-18 were not accessed or modified.

## Next shortest justified path

**Stop spending research cycles repairing D1 to produce an unachievable growth outcome.** Preregister **one genuinely distinct complete architecture** with a real executable path and source-feasible historical requirements **before** inspecting its returns. Prefer an architecture whose signal does not depend on the unavailable pre-March-2022 OKX funding, or explicitly obtain an independent primary/secondary source that covers that era without contaminating validation. Use the already verified four-leg hourly OKX TRAIN price data. Build full self-financing severe/supersevere accounting and independent risk/fold gates for that *new* architecture, with native-fee provenance or clearly labeled conservative modeled execution; do not claim certified fills for hypothetical historical orders. Preserve the same sealed validation and final holdout.
