# V99 I1 — 90-week fixed-tenor original-source gate: remote verified (2026-10-27 09:50 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION.** No economic TRAIN, historical option fills, historical native fee/margin certification, validation/holdout, paper or live orders.

## Actual critical-path correction

The existing original-quote intake required **91 Sunday files / 182 BTC+ETH asset-weeks** based on the 21–45d generic source contract. The already preregistered I1 strategy only permits **28–35d** put verticals with expiry strictly before the sealed 2023-10-01 TRAIN end. The 2023-09-04 entry can never satisfy that rule. Requiring its source file for the I1 fixed-tenor economics would make a valid **90-week** licensed source package fail the old intake gate. This is a source procurement and real-run blocker, not an alpha opportunity.

Preregistered separately at commit `aa89af93334c1b1492c037568efb7e62aacabd19` **before** implementation. Implemented opt-in `I1_FIXED_TENOR_TRAIN_SUNDAY_ARCHIVE_V1`: exactly **90 Sundays** (2021-12-12 through 2023-08-27), **180 potentially eligible asset-weeks**, strictly 28–35d option quotes, all original clock/hash/listing/synchronization checks. The legacy 91-Sunday 21–45d manifest remains supported and unchanged. **182 original signal observations** remain intact; no observed trades or profitable folds are inferred. Original exit/mark/delivery lifecycle data remains additionally required.

## Executed and independently checked on GitHub

- [Full archive intake Actions 40506852289](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40506852289): **SUCCESS**, **18/18 synthetic tests**, including three new 90-week source/negative-control tests; original-byte independent oracle recomputed **180/180 synthetic** eligible two-strike asset-weeks and **179/180 synthetic** when a fake native contract was created after its decision.
- [Source-to-engine entry-book Actions 40506852308](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40506852308): **SUCCESS**. The existing legacy 91-week bridge and independent raw-byte audit still pass; new 90-week bridge additionally verified **360 synthetic quote records** and independently rejected invalid original listing.
- [Diff baseline to final head](https://github.com/DnSiii/CryptoAI-Lab/compare/49849ab4a601400c6c36f6e51f711209cb09608a...82fcfbe4d3cf3e6d46f0cd839c029e581a38ceb3): changes limited to research source-intake, source-to-book, independent verification, tests, and prereg/result docs; no Frozen, paper, champion, validation, holdout, dashboard or order paths changed.
- These 180/179/360 figures are **synthetic only**; no new authenticated historical BTC/ETH options tape was obtained. The last independent original-source join still found **0 certified complete historical lifecycles**. The 90-week source contract does **not** convert the existing 4,000-row partial sample into original source coverage.

## Remaining external dependency and next actual run

Obtain lawful, authenticated Deribit BTC+ETH original 2021-12..2023-09 option BBO/size tape with exchange and arrival clocks for all **90 entry Sundays**, plus the complete overlapping **28–35d mark/exit/settlement lifecycle** through 2023-09-30; prove native historical lot/multiplier, account-specific fee/delivery tier, coin collateral/margin/liquidation and delivery indices. The last authenticated Tardis Actions probe found **no configured `TARDIS_API_KEY`**. Tardis full-history written grant or a verified equivalent (e.g. vendor supplying identical original fields) is acceptable. Never buy a generic 2026 subscription without written 2021 entitlement.

After actual licensed bytes, run the independently authenticated source intake and one preregistered five-fold severe/supersevere integrated I1 economic TRAIN, six regimes, tail/DD/benchmark gates and independent portfolio replay. No source, no certified economics, **NO PROMOTION**.
