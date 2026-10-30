# V98 Independent Phase1251a — RV source cross-OS raw hash mismatch (2026-10-23)

During the first complete AI 180-cell evaluation, the **independent source-only** [run 40016321388](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40016321388) revealed a critical source reproducibility discrepancy before final two-OS complete-system reconciliation. Growth, Opportunity, Stress and Router raw hashes match, but the 240h BTC-beta-neutral **Relative Value source** does not:

- Ubuntu 22.04: benign `bbace9517f582a28e27c5950db8559fde4a78f957a947fb428e1fce6bbb8efbf`; crisis `44204ae9b82d3021d68fcabbd233bcc2766bfcd9e19f65225d01125da76b621f`.
- Ubuntu 24.04: benign `f7ff5ba908a34fa14756b32f859d315a289b43ce0ef05de4aa8f6bebd8dd324e`; crisis `3cc6956f46b8d95d5078bbc8ef60a4b16eea4f6ffd1dd872df0d544d17b3bede`.

Both OS independently agree on source activation: benign Growth/Opportunity/RV/Stress hours [180,87,180,0], crisis [180,78,180,65], and crisis regimes TREND 110, DISPERSION 30, HAZARD 40. **Hash mismatch is NOT a passing exact source gate.** The first full [run 40016172237](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40016172237) is **ineligible for final freeze/promotion** regardless of its survival result until this discrepancy is resolved, and all 180 cells are rerun on a newly frozen source revision.

Next preregistered action: inspect per-cell RV numeric deltas across OS on fixed benign/crisis fixtures, without changing signs, windows, leverage, fees or other economic choices. Only if differences are numerically negligible may deterministic canonicalization be applied and a fresh exact-hash source gate and 180-cell structural gate run. If materially different, reject AI as irreproducible. No historical PnL, 2025 validation, 2026+, XRP, Phase083 or external benchmarks.
