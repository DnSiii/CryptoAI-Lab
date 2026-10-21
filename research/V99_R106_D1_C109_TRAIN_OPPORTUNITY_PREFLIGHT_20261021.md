# V99 R106 D1 — C109 TRAIN opportunity preflight (2026-10-21)

**DATA_ONLY/HOLD — NO PROMOTION.** This is a preregistered, source-only diagnostic for the existing frozen D1 spot/perp basis-carry architecture, not a new alpha candidate, parameter retune, backtest ROI, live/paper result, or authorization to open validation/holdout.

## Frozen calculation

Use only the exact TRAIN [2021-12-09T00:00:00Z, 2023-10-01T00:00:00Z), 15,864 hourly observations per OKX BTC/ETH spot/perp instrument and 1,983 eight-hour funding fixes per swap, with independent source hash/clock verification. At each UTC midnight from 2021-12-16 through 2023-09-30 (654 decisions), replay the **unchanged** D1 t-1 policy in both cost scenarios: 0.0007 severe and 0.0014 supersevere per leg. Preregistered projected daily funding hurdle is 8 * cost/leg = **0.56% severe** and **1.12% supersevere**. Count eligible BTC/ETH entry-intent days, cash-only days, the five fixed chronological folds and the 3x2 market regime labels. Require identical regime paths across cost scenarios.

The output is a necessary *opportunity-coverage* diagnostic only. No portfolio NAV, realized PnL, fills, account funding settlements, fee-tier authenticity, exchange certification, or performance claims may be inferred from it. No optimization or retuning if opportunities are scarce. Original immutable V16/V99 Frozen, paper-results, champion, sealed validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 remain untouched.

## Execution status

C109 local preflight code and synthetic tests are held separately pending authorized publication of the complete 204-file add-only D1 dependency closure. The remote branch currently lacks that integrated source; GitHub Actions 39128800765 is a synthetic-calendar preflight, not economic CI. Until actual first-party historical market, funding and historically applicable fee/contract records and a reproducible execution model are available, **NO AUTHENTICATED D1 TRAIN ROI** can be reported.
