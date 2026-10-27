# V99 I1 — precommitted overlapping-position index mismatch handling (2026-10-27)

**SOURCE_ONLY/HOLD, NO PROMOTION.** This is a deterministic failure-path repair, not a new alpha or economic TRAIN. The already-fixed I1 single-asset same-clock native-index rule remains unchanged; do not relax price/index equality or retune the 90/80 vertical.

## Observed code-level defect and exact remedy

`open_vertical` checks an existing marked position's source index against the new two-leg quote index and raises `POSTENTRY_UNBOUND_UNDERLYING_INDEX` on mismatch. The fixed vertical bridge currently treats this as an unhandled exception rather than a nontrading risk veto. A multi-week portfolio with valid as-of marks can therefore abort when the new quote index differs even slightly, instead of recording a causal CASH decision. Preserve strict same-index accounting: add only this specific exception to the existing fail-closed `RISK_VETO` set, advance the decision clock, leave cash/positions/marks/reserves/settlements untouched, and never fabricate an opening.

Independent oracle must NOT accept the label merely because the primary engine emits it: for this narrow overlap case, independently confirm an existing marked portfolio at the exact decision time, positive fixed-source pair, explicit valid margin, positive cost-floor net premium, enough cash/reserve for the proposed position, and a genuinely different original index from the existing mark. Reject a forged index-mismatch veto if indices match or the portfolio is empty. Other overlapping risk cases remain unverified and must fail closed, not be silently approved.

## Validation and source isolation

Run both severe and supersevere fixtures, including positive mismatch, forged same-index veto and preservation of complete wallet state; trigger GitHub Actions on the research branch and inspect the actual result. Rejoin the original archived 182 causal decisions and 4,000 partial quotes independently in the existing CI; **0 original synchronized pairs / 0 certified lifecycles remains SOURCE_ONLY/HOLD** unless actual source evidence changes. No original 2021–2023 BTC/ETH complete options tape, fee tier, margin, fills, settlement or executable economic TRAIN is claimed. Never open validation >=2023-10-01, holdout, Frozen, paper/results or champion; no orders or ROI.
