# V99 I1 — preregistered atomic target-day source-gate publication repair (2026-10-31 09:xx BRT)

**SOURCE-TRANSFER INTEGRITY ONLY; NO ECONOMICS, RETUNE, PROMOTION OR ORDERS.**

## Existing deterministic defect (identified before code change)
In `research/tools/v99_r106_i1_tardis_licensed_transfer.py`, the opt-in authenticated transfer validates gzip, SHA256 and 24/24 arrival hours, then **publishes the new 2022-01-23.csv.gz into the canonical licensed root using os.link**. Only *after* that publication, the fixed target-day `inspect()` independently replays the original source and verifies the fixed synchronized 28–35d put-book gate. If that later independent source replay raises, the canonical day remains published despite the transfer failing. This is an atomicity and downstream source-state defect, not an observed trading loss or a reason to change I1 rules.

## Fixed repair, before implementation
For the **one preselected 2022-01-23 target only**, run the independent target-day source feasibility oracle on a same-filesystem **private temporary staging directory** containing a hard link named exactly `2022-01-23.csv.gz` to the newly downloaded, gzip/SHA/hour-verified temporary file. Reject any exception or unrecognized source status **before** the canonical `os.link`. Remove staging links/directories in `finally`; never delete an already existing user-provided licensed original. On success, publish exactly once atomically without overwriting. Keep existing-file resume behavior, native source day, entitlement, external digest, 24/24 hour gate, fixed Monday/tenor, cost assumptions and all strategy gates unchanged. Preserve the report's source-only classification and independent check result; no claim of vendor completeness or economics.

## Adversarial controls
Use existing offline synthetic vendor fixtures and add an independent-oracle-failure injection (via narrow patch of the existing `inspect` function) asserting: (1) canonical target day is absent after a failed new download; (2) no `.part` or staging directory remains; (3) previously published valid days are never deleted/overwritten on later failure; (4) successful target-day synthetic source passes and publishes with the same 0 certified lifecycles and no promotion. Run the actual push-triggered GitHub fixture CI and verify the result and changed-file list. No paid data/keys, sealed validation, final holdout, Frozen, paper or legacy champion accessed.

## Decision rule
CI success is **software integrity only**, not native executable source or profitable V99. Missing 658/661 original Deribit quote days, historical account fee/margin/delivery provenance and 0/180 certified I1 lifecycles remain unchanged until lawful original market delivery. **SOURCE HOLD / NO PROMOTION / NO ORDERS.**
