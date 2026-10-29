# V98 Independent LC — permanent source-only rejection (2026-10-29)

**DECISION: REJECT LC PERMANENTLY BEFORE HISTORICAL SYSTEM PNL.** No post-result sign, threshold, window, frequency, gross, budget or quote-policy rescue. No 2025 validation, 2026+ holdout, XRP, V14/V15/V99 internals, Frozen or paper access. No orders.

## Immutable chronology and authenticated evidence

- Seven-slot preregistration commit **4eba8506a4aea36384ced50d3ac0a0f9e51d388d** preceded source implementation **f144bfdf051778430dedeba274071e8993a34072** and any LC historical PnL.
- Source Git blob **7882f9686fc7cc9d979743b6952c709353bbd0f2**, locally executed SHA256 **323777e675e2e53be23937295fb74e86a4207e5bcb78fa7780574b80b7efc116**.
- Original pinned GitHub Actions artifact **12549265452**, produced by run **40064588623**, contains 18,288 hourly Clean-4 observations per asset, Dec-2022 warmup through Dec-2024; native funding bounds file SHA256 matched the authenticated receipt, four OHLC CSV SHA256 pins and sizes matched, UTC calendar matched, 9,144 native 8h signed funding events verified. No 2025+ data.
- Synthetic source future mutation PASS; independent *real pinned* 14,000-hour future-mutation prefix PASS; no hidden gross, component overbudget, silent row rebalance, or invalid quote entry. Maximum intended gross **0.87**.
- Opportunity entries 2023/2024 **8/6**, Relative Value **24/22**, Stress/Recovery **11/10**. Independent implementation of the weekly Opportunity event and expiry accounting, without importing the LC source module, reproduced **8/6** and the exact 14 event timestamps.
- Immutable source hard gate requires **at least eight Opportunity entries in EACH year**. 2024 fails with **six**. **NO LC PNL COMPUTED** and no 30-cell physical economics run.

## Distinct infrastructure finding (NOT a rescue of LC)

The pinned Clean-4 data contain a simultaneous zero-quote-volume flat OHLC hour for all four assets at **2024-10-28 20:00 UTC**. The legacy all-asset 672-hour strictly-positive quote lookback therefore suppresses source decisions for **672 consecutive hours** after this one zero-quote hour. This is not a provenance conflict requiring removal of Clean-4. Any prospective shorter quarantine would require an **independent source-safety preregistration and tests before a genuinely new candidate**, and may never be used to resurrect LC or other rejected experiments.

**Next:** prospective, outcome-blind source-outage policy and genuinely distinct seven-slot economic hypothesis; source gate before PnL, full physical independent audits before freeze. Existing Frozen, holdout and paper remain untouched.
