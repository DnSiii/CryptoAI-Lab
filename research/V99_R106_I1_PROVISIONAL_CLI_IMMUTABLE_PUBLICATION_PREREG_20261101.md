# V99 I1 original-to-provisional runner: immutable output contract — preregistration (2026-11-01)

TRAIN-only safety repair. No strategy, parameter, PnL, model promotion, sealed validation/holdout, paper, Frozen, champion or order changes.

**Observed defect:** `research.tools.v99_r106_i1_original_to_provisional_numeric.main` currently calls `Path(output_path).write_text(...)` after a 661-day source/NAV replay. A caller can overwrite an existing source, journal, Frozen/paper artifact, prior report or symlink destination, and a failed disk write may leave a partial report. The higher-level signed bridge has an exclusive atomic output contract, but this independently callable lower-level CLI does not.

**Precommitted correction:** reject existing output paths including dangling symlinks **before** starting expensive source checks; preserve all existing bytes. After successful nonfixture source/oracle checks, serialize with `allow_nan=False`, create output parent if necessary, write/fsync a temporary file in the target directory, and publish with exclusive hard link; clean temporary files on failure. No overwrite and no silent fixture fallback. Do not set any certification flag or call economic result a TRAIN pass.

**Adversarial tests before market interpretation:** occupied output, symlink to absent path, JSON serialization failure, fsync failure, racing competing writer, and success with explicitly provisional flags. The 661-day synthetic fixture and the original archived 182-signal missing-license source veto must still run in remote GitHub CI. These tests are software safety checks, not historical native execution proof.

**External critical path unchanged:** 658/661 original licensed Deribit BTC/ETH options days absent; historical dated native fee tier/lot/margin/liquidation/expiry delivery evidence and independently verified size-aware simulated fills still missing; 0/180 economically certified lifecycles. No TRAIN economic result or promotion until original sources and independent formal gates pass.
