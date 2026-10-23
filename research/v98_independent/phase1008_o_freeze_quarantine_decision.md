# V98 Independent Phase1008 — O frozen-target verification QUARANTINE

Run 39923749483 (2026-10-23) verified the exact Phase1006 O source Git blob, reauthenticated all 100 official Clean-4 OHLC archives, then **failed closed** at `FROZEN_O_TARGET_HASH_DRIFT`. No O historical PnL was executed. This conflicts with the successful Phase1006 two-process same-run hashes (run 39923404760), and resembles the earlier M_full source-only pin discrepancy from Phase1004.

**Decision:** the five O target hashes recorded in Phase1008 remain immutable *provisional reference hashes*, but cross-run reproducibility has NOT passed. O is not an economic champion, not cleared for Phase1009 historical execution and cannot be repinned from a convenient runner. No parameter or code changes to Phase1006. N_full remains REJECTED from Phase1001, and M_full remains under reproducibility quarantine.

**Evidence and next gate:** Phase1010 is a preregistered independent-runner float64 array comparison (not PnL) to distinguish true target drift from output serialization or CPU-dependent numerical rounding. Only a documented, independent reproducibility solution before economic results may release O for the already preregistered Phase1009 90-cell historical gate. V16/V99 and all future validation/holdout remain untouched.
