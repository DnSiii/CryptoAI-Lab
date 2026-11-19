# V98 C23 — immutable rejection after authenticated Clean-4 replay (2026-11-19)

Status: **REJECTED — risk-governor invariant violated; no promotion, no holdout, no benchmark**.

Evidence: GitHub Actions run 44631695381, commit 22234bc053b9e45b7aa8e59ce25f77e601ddb475, artifact 14582331842 (SHA-256 5dcfc49f7cbc171849728f69eba3005a9a76019172f462a783014e726d0ea6c9). Training universe: BTC/ETH/BNB/SOL USD-M hourly Clean-4, 27,048 hours, native funding. The complete replay succeeded; the independent ledger audit raised EXPOSURE_CAP_VIOLATION and the job failed.

Ledger inspection of all three scenarios: 1x 1,346 hourly rows above the gross 90% or asset 40% hard caps; 2x 1,346; 4x 1,297. First violation at index 3013, gross 0.90008, turnover 0. Gross exposure peaked near 0.90792; individual asset weight peaked near 0.52245. These are **post-fill drift** violations between weekly rebalances, not a harmless report-format mismatch. Weekly rebalance-only execution and continuous hard caps are incompatible without explicit risk-triggered trades; retroactively adding exceptions would change the preregistered hypothesis.

Unvalidated replay-only ending equity from initial USD 10,000: 1x USD 18,185.58; 2x USD 18,258.82; 4x USD 17,940.33. These numbers are **not approved performance**, and cannot justify changing the C23 rules. No complete independent audit, annual economic gate, chronological validation, or promotion was achieved.

Decision: reject C23 without retuning. Next independent architectural hypothesis must preregister risk-governor enforcement under position drift before inspecting its own economic outcomes, and independently audit chronological folds and 1x/2x/4x costs. Do not access the future holdout or V14/V15/V99 benchmarks. V16/V99 Frozen and paper remain untouched.
