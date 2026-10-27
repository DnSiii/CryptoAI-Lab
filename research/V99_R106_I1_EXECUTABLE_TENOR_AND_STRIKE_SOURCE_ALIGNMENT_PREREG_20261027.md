# V99 I1 — executable maturity clock and distinct-strike source alignment (preregistered 2026-10-27)

**Decision fixed before code:** SOURCE_ONLY/HOLD; this is a necessary original-source eligibility correction, not an alpha selection, fill, ROI, five-fold economic TRAIN or promotion. No new candidate or parameter search.

## Falsifiable discrepancy

The already-fixed I1 engine `research/tools/v99_r106_i1_native_coin_account_replay.py` parses Deribit option expiry at **08:00 UTC**, and `select_fixed_vertical` permits **28d <= (expiry timestamp - Monday 00:00 UTC decision) <= 35d**. The separate 661-day source scanner and independent oracle used calendar dates and admitted options expiring on Monday+35 calendar days, which actually have **35d + 8h** maturity and cannot enter the unchanged engine. Their pair screen also required different symbol strings, not distinct *economic* strikes; aliases such as `30000` and `30000.0` must not count as two legs. These source-only counts must never be interpreted as executable pairs.

## Frozen correction and acceptance criteria

1. Keep the engine and preregistered selection unchanged. For **fixed 28–35d** source eligibility, derive expiry from the instrument at **08:00 UTC** and compare actual elapsed microseconds against Monday 00:00 UTC. Hence allowed calendar expiry offsets are **28..34 days inclusive**, not 35; never open 2023-10-01 onward. Preserve the legacy weak 21d source-only reporting.
2. A source-only two-leg pair requires two **distinct positive numeric strikes**, same asset, same expiry and unchanged independent Sunday predecision/held-contract checks. Normalize strikes with exact decimal arithmetic, reject malformed/nonfinite values. Do not assert that a distinct-strike pair is actually executable, has valid original fee/margin terms, or satisfies the fixed 90%/80% strike targets.
3. Independently reimplement the same checks in the separate source oracle without importing the primary implementation.
4. On 661-day **explicitly synthetic** fixture, demonstrate positive 28-calendar-day (28d8h actual) source pair, **negative 35-calendar-day (35d8h actual)** pair and **negative same-economic-strike aliases**. Both independent and primary results must agree. Assert the original 180/180 weak daily presence still cannot certify any real lifecycle.
5. Run actual push-triggered GitHub Actions and inspect conclusion. Never alter V16/V99 Frozen, paper, champion, validation, final holdout or any order path. Do not infer native historical fees or returns.

**External dependency remains:** licensed complete original 2021–2023 Deribit BTC/ETH options bid/ask+sizes, venue/arrival clocks and source rights, plus dated original settlement, account-specific fee tiers and inverse-coin margin/liquidation terms. No economic promotion without them.
