# 2026-11-15 — paper recovery failure and R106 epoch gate (read-only evidence)

## Official paper: actual failure after successful publication

GitHub Actions run 43759311785, job 132950321181, published commit `276e64860` to `paper-results` at 2026-11-15T20:46:40Z and dispatched dashboard run 43759960360. The workflow then failed at `scripts/recover_paper_runtime.py` lines 114–119 while trying to cancel ancient queued run 34748927780 (created 2026-09-13T09:05:49Z). Both cancel and force-cancel API calls exited 1. The existing exception handler only tolerates HTTP 409; the precise HTTP response body was not printed. Consequently the overall workflow's FAILURE does **not** establish failed ledger verification or failed publication. Do not misreport it as successful end-to-end CI either.

Required safe correction: capture the GitHub API status/body for both cancel attempts, distinguish an already-completed/phantom queue entry from permission/rate-limit/server errors, and ensure non-cancellable ancient metadata does not block dispatch. Never blindly swallow all cancellation failures. Test 409/422/403/429/5xx and fresh active runs, then validate in GitHub Actions. Do not touch `paper-results` or rewrite trades.

## R106 forward research: hard immutable-epoch gate

Run 43757454925, job 132944563013, checked commit `244b3aba001a2cc1fdcb3c2c0549b988bb879bbb`. The independent legacy-epoch preflight reported `NEW_VERSIONED_EPOCH_REQUIRED` and `current_epoch_guard_can_pass_any_candidate=false`, with published old-paper SHA256 `f188c4d95761c4ddf4719f4d86bfab0faa54a65f79d576f42ce3cc4f09e17089`. F1 and F3 have operation ledgers at cap; all five variants F1/F12/F3/F7/R98 use a historical reference crossing the paper epoch. Exit code 2 is a correct safety rejection, **not** evidence of a profitable model or a candidate-specific failure.

Next step: preregister a genuinely new versioned forward epoch, source-verify the boundary and accounting, and keep old paper/holdout immutable. Any engine research remains TRAIN-only and NO PROMOTION. No order submission.
