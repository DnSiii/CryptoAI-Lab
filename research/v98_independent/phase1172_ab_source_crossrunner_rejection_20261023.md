# V98 Independent Phase1172 — AB cross-runner provenance decision (2026-10-23)

## Evidence and non-negotiable decision
- Official Phase1168 GitHub Actions run **39995890636** finished **FAILURE** at the four-runner equality gate. Four independent fresh source-only executions (Ubuntu 22.04 a/b; Ubuntu 24.04 a/b) each individually reported `PASS_AB_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN`, but the cross-runner assertion raised `AB_CROSSRUNNER_DRIFT_canonical_sha256`.
- Four archived receipts independently inspected; native signed mark CSV SHA256 was **f706812b7989666c3efd0b24045a5c31f4d9c79b46d61da7b5e6cde6c6e73f5e** in all four. Each had **18,288** hours, **9,144** native funding events, identical diagnostic regime counts (0: 1,728; 1: 10,628; 2: 5,932), and identical sleeve active-hour counts (growth 14,093; opportunity 5,290; relative-value 7,771; stress 982).
- Exactly **3 of the 15** canonical strategy-intent hashes disagreed by OS (the a/b runs within each OS agreed): `AB_full__immediate`, `AB_minus_opportunity__immediate`, and `AB_minus_stress__immediate`. The other 12/15 hashes agreed. The three drifted series include multiple nonzero sleeve contributions at $10k; source-vendor hashes and active-hour counts remained identical. A cross-platform floating-point serialization/rounding difference is a **hypothesis, not a verified root cause**; no row-level intent delta has yet been authenticated.
- Distinct values for `AB_full__immediate`: Ubuntu 22.04 `867e34c8e19e6805a7e275121d9be21e1d1dede2c033a39dda0d26d4f2cac317`; Ubuntu 24.04 `b4bd911c3930b2d4f333012eb985f2407258cafa9e49a63477758289603ca09c`.
- `AB_minus_opportunity__immediate`: Ubuntu 22.04 `f9194465e9689343b98739216243f2a1b02a54f9a01645d138ec9171a170c4c1`; Ubuntu 24.04 `09174e630a69c65467272ae188ac4c1ee1d87739ce1c2cb29c2d7ef0d3ca0aa1`.
- `AB_minus_stress__immediate`: Ubuntu 22.04 `3a4c932f5051a0aadca371e482155b1937394c0279ec0089557da665a487d476`; Ubuntu 24.04 `5476d76d163ae462302112f0b2bb9143721ec3a85520eda2ed5eab6512cd3963`.

## Decision
**AB is REJECTED at the preregistered 15/15 reproducibility gate.** Do not replace one hash, lower decimal precision, relax the four-runner comparison, alter source weights, cherry-pick an OS, or compute historical AB system PnL. The previously passed synthetic 90-cell integration, 1,000 adverse cases, growth-metric tests and FIFO tests establish only synthetic readiness; they do **not** override the failed authenticated freeze. AB is not an economic champion and has no validated CAGR.

## Continuity and isolation
Keep the AB implementation and receipts immutable as rejected evidence. Continue with a genuinely distinct, preregistered full seven-slot portfolio hypothesis, using Clean-4 2022-12 warmup/2023-2024 training, native V98 mark/funding, 2025 untouched validation, and no 2026+ training. No V16/V99 files, workflows, reports or paper state are touched. No V14/V15/V99 parameters, architecture or performance are inspected.

Official evidence: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/39995890636
