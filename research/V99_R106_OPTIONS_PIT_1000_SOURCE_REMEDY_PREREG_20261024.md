# V99 — single fixed-depth options source-completeness remedy (2026-10-24 BRT)

**DATA_ONLY/HOLD; source remedy, not alpha tuning.** The previously preregistered 100-latest-trade source contract failed 0/5 folds despite 188/188 valid responses; all 188 were `has_more=true`. This proves the bounded sample was truncated, not that long-dated option instruments did not trade.

**One justified source remedy only:** keep exactly the same 94 Monday 00:00 UTC TRAIN decisions, BTC/ETH, prior 24h query, strict t-1, <=6h trade age, 7–45d and 46–120d expiry bands, >=2 distinct strikes per call/put band, >=70% weekly coverage per asset per fold and >=4/5 folds. Change **only** the API request depth from 100 to **1000 most recent trades** per currency/decision. Preserve raw receipts and hashes and rerun a separate independent oracle. Do not open validation/holdout, score PnL, choose a strategy, or alter eligibility after results.

This remains a lower-bound trade-information sample, not a full chain or executable bid/ask surface. If 1000 samples remain truncated or the 4/5 information coverage gate fails, do not keep serially increasing depth without a separate, externally justified full-chain retrieval method. A pass would justify designing one *new* preregistered integrated economic engine, not promotion. Historical OKX account fee/funding/execution provenance remains a separate deployment blocker.

**No ROI. No promotion. No orders. No paper or Frozen mutations.**
