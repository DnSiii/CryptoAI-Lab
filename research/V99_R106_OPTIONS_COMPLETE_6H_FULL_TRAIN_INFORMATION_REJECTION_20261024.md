# V99 — complete original 6h options trade-IV TRAIN information contract: FAIL (2026-10-24 BRT)

**DATA_ONLY/HOLD — NO PROMOTION. No economic engine or ROI was tested.** The preregistered *source information* contract is rejected for this exact 6h/15%-moneyness/two-strike/four-group weekly configuration. Do not relax its gates after observing the result.

## Original first-party execution and independent verification
- Fixed 10-slot first-fold-week probe: [Actions 40071608787](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40071608787) **SUCCESS**; 10/10 complete historical 6h original Deribit trade windows, 5/10 four-group near-ATM samples.
- Full 94-week two-asset TRAIN: initial [Actions 40071696260](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40071696260) retrieved 188/188 but the independent oracle **caught overwritten original receipts** because page filenames repeated across weeks. The original-byte SHA-256 check correctly failed. No scientific conclusion was accepted from that failed audit.
- Corrected to a unique per-asset-week receipt namespace at commit [1d517ef](https://github.com/DnSiii/CryptoAI-Lab/commit/1d517efb73cefe3d6a5c94968b8ba3761d0ed4e6), without changing any query, moneyness, fold, age or pass/fail rule.
- [Actions 40071882222](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40071882222) **SUCCESS**: 188/188 complete 6h original Deribit option-trade responses, independent original-byte SHA-256, causal timestamp, overlap pagination, unique trade ID, four-group IV/strike and five-fold reexecution. This proves bounded 6h trade *prints*, not executable option bid/ask snapshots or continuous option surfaces.

## Pre-fixed information-quality result

| TRAIN fold | BTC comparable weeks | ETH comparable weeks | Both >=70%? |
| --- | ---: | ---: | --- |
| 1 | 14/19 | 15/19 | Yes |
| 2 | 12/19 | 13/19 | **No** |
| 3 | 15/19 | 12/19 | **No** |
| 4 | 17/18 | 13/18 | Yes |
| 5 | 17/19 | 15/19 | Yes |
| Total | 75/94 | 68/94 | **3/5 folds; FAIL (<4/5)** |

**143/188** asset-weeks satisfied the unchanged near-ATM four-group trade-IV information diagnostic, but only **3/5 folds** passed for both assets. Missing comparable trades in a six-hour window is a market/source-coverage constraint, not proof that the exchange lacked option quotes. This **rejects this source contract**, not all volatility-informed trading mechanisms. Do not score returns, freeze or promote any candidate using this contract.

**Critical path:** stop trying 100/1000/deeper unstructured trade samples. If pursuing option-derived signals, use an economically interpretable original PIT volatility index or auditable historical quote/chain snapshot rather than tuning the failed trade-IV screen. Before any complete portfolio TRAIN, preregister exactly one distinct mechanism with original OKX spot/perp source, self-financing costs, severe/supersevere stress, five chronological folds, six regimes, tail/DD/benchmark gates and independent oracle. Original account fee-tier, settled funding (if perps), historical fills/lot/margin remain unverified; no fabricated exchange-certified profits. Sealed validation [2023-10-01,2024-01-18), final holdout >=2024-01-18, V16/V99 Frozen, paper/results and legacy champion remain untouched. No orders.
