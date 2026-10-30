# V98 Independent CT — pre-economic physical-source transport correction (2026-10-24)

CT preregistration and all signal/threshold/weight rules remain unchanged. No CT PnL has been observed or used for these corrections.

1. [Initial workflow](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40144062704) failed **before loading source** because automated `CS -> CT` code generation accidentally changed literal file extension `.csv` to `.ctv` in the CT workflow staging command. Corrected all six occurrences back to `.csv`; pinned artifact and source hashes unchanged.
2. Generic `ak_slow_compound_execution.risk_history` hard-rejects t<2016 even though its actual risk bounds use only 336 prior hours for OHLC/quote and 672 prior hours for signed funding. CT's preregistered 744h warmup would otherwise hit `AK_WARMUP` at the first executable hour, preventing a real run. CT-local `ct_prior_only_risk_history` implements **identical numeric formulas and same conservative constants**, but correctly requires t>=672; all slices end at t-1. No price/funding future leakage, no relaxation of governor, no signal changes, no window/threshold rescue.
3. The corrected CT workflow is allowed to rerun the source gate and, only if that gate passes, native physical economic cells. Source inactivity still requires immediate permanent rejection.

These are operational repairs before CT PnL, not evidence of profitability or validation. 2025 holdout, 2026+ and V14/V15/V99 remain unopened; no V16/V99 Frozen or paper modifications.
