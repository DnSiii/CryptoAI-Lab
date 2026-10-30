# V98 Independent Phase1013 — direct failing-run O hash and CPU triage

Phase1008 failed the O frozen target hash gate in two independent attempts despite official Clean-4 source and O code blob passing. Phase1010 two AMD EPYC 9V74 runners exactly reproduced all five O target float64 arrays and frozen 12g hashes. Do not choose a favorable runner or bypass Phase1008.

Change only the V98 Phase1008 **source-only workflow** to print, before the unchanged fail-closed freeze step, the current runner CPU model, exact observed five 12g target hashes and per-path equality against immutable Phase1008 references, using the same already authenticated canonical CSVs. The existing `phase1008_o_frozen_paths.py` must remain unchanged and still fail if hashes differ. No O economic PnL, retuning, refreeze, 2025+, holdout, external benchmarks, V16/V99 changes. Purpose: identify which hash drifts and whether host CPU differs.
