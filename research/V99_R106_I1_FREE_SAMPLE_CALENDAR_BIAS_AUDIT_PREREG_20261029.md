# V99 R106 I1 — source-only audit of free-sample calendar selection (2026-10-29)

**NO STRATEGY CHANGE / NO ECONOMIC TRIAL / NO PROMOTION.** This audit is not a new candidate, a retune, or a reactivation of the de-prioritized I1. It corrects how strongly two original source-negative dates can be interpreted.

## Fixed inputs before implementation

- Use the **unchanged** `eligible(True)` 90 Monday UTC-midnight I1 decision grid in `research.tools.v99_r106_i1_full_archive_intake`, strictly before 2023-10-01. No sealed market values.
- Original free Tardis quotes were observed for Sundays 2022-05-01 and 2023-01-01, whose fixed next-day I1 decisions are Mondays 2022-05-02 and 2023-01-02. The third free sample 2022-06-01 is **not** the Sunday immediately before an I1 Monday.
- For a **calendar-only necessary possibility**, enumerate the final Friday of each calendar month at 08:00 UTC; compute exact remaining days at each fixed Monday 00:00 UTC; check the unchanged I1 inclusive 28–35-day tenor. This is not proof that a contract existed or was quoted historically. Monthly/quarterly expiries follow Deribit's published contract-introduction policy; the present policy is not retroactive evidence of 2022 listings. The historical first-party registry remains a separate, incomplete retrospective source.
- An independent test implementation must use a different month-end construction from the production audit. Test both known sampled Mondays, at least one positive-control Monday with calendar tenor in range, and the fixed 90-decision grid.

## Precommitted interpretation

If **both** negative public sample Mondays have *no* monthly/quarterly last-Friday expiry in the 28–35-day band, the pair of 0-book observations does **not** constitute two independent empirical liquidity failures. It is consistent with a deterministic calendar selection bias induced by the first-day-of-month free-data rule. **Do not** infer missing liquidity on other Mondays or reopen I1 economic evaluation; keep I1 de-prioritized until a lawful, time-aligned original quote archive and native fee/margin/settlement evidence are provided.

If either sample Monday has a qualifying monthly/quarterly expiry, flag the discrepancy for independent source review; do not invent contracts or PnL. Count calendar-possible Mondays only as an upper bound **within the monthly/quarterly family**, never as a complete bound on all listed expiries or executable books.

Preserve all previous C1/C2/D1/E1/F1/G1/H1 rejections; I1 rules, Frozen, champion, paper/results, sealed validation and final holdout unchanged. No orders. This audit cannot authorize promotion, change source readiness or certify any of the 180 original asset-week lifecycles.

Official reference: https://support.deribit.com/hc/en-us/articles/25944688876957-Contract-Introduction-Policy
