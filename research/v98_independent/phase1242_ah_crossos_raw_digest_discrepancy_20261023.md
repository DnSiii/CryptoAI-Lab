# V98 Independent Phase1242 dual-OS reproducibility audit — 2026-10-23

Official [AH three-slot run 40013844735](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40013844735) passed **20/20 unit tests on each** of Ubuntu 22.04 and Ubuntu 24.04. However the combined raw float64 SHA256 receipts were **NOT identical**:
- Ubuntu 22.04: `29a33ae6b164d7f79ee00f5165d1a4afffec599008700b1d74520d8834aaf3d9`
- Ubuntu 24.04: `1775381aca1e7602369c904ad61e2784a9b93105a71948cc613584e17f09d1d7`
- Both reported 200 observations and governor feasible fraction `0.17264270782470703`.

**Decision: DO NOT FREEZE AH as a complete candidate; two-OS bitwise reproducibility gate has not passed.** The combined digest includes a 32-step floating-point exponentiated-gradient covariance optimizer, for which platform BLAS/math microdifferences are plausible, but this is not yet established. Before any synthetic or historical PnL, isolate component hashes, check max absolute numeric deltas and enforce deterministic canonical float64 outputs only if economically negligible. Preserve both original raw digests as evidence; never claim the failed raw hash gate passed. No signs, windows, growth objective, costs, stress fixtures or economic parameters may be changed to rescue outcomes.

This is an infrastructure reproducibility repair *before* any AH complete-system structural result. If canonical outputs or full-system deterministic receipts still differ, reject AH rather than silently waiving the gate. V16/V99 and rejected AG untouched.
