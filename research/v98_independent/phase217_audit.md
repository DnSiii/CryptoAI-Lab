# V98 Independent — Phase217 audit

## Decision
REJECT_FAMILY_NO_RESCUE.

The frozen mechanical gate produced zero coherent specs across independent 2023/2024/2025 training folds. Deterministic workflow reproduction was byte-identical (workflow SHA256 `0d6848145cbb0bec4e95848ec4e774a3d9496691426f3aa16e8d263b214fbb3a`). Validation/final holdout remains unopened.

## Failure mechanism audit
Representative frozen spec `sign_L12_B50_hold3`, 2023 base: return -73.13%, PF 0.8442, MDD -78.20%, payoff 1.4722, win rate 14.39%, positive days 33.42%, 1287 trades. All four alt asset returns were negative. All three causal BTC regimes were negative: bear -29.73% (PF 0.766), bull -21.21% (PF 0.919), sideways -51.47% (PF 0.825). Severe deteriorated to -91.66%, PF 0.7277 and MDD -92.31%.

The positive payoff with very low win rate and PF<1 indicates occasional large winners do not compensate for the high frequency of losing continuation attempts plus implementation drag. This is not a single-asset or single-regime pathology, so asset/regime rescue would be post-hoc and is prohibited.

## Integrity
Workflow firewall confirmed canonical/funding timestamps <2026-01-01 and monotonic/unique. Static invariants confirmed `pct_change(fill_method=None)`, lagging via `.shift(1)`, and exactly 8 preregistered specs. Stress monotonicity and required metric schema passed for all folds/specs. No V16/V99 files or paper state were touched.

## Next scientific step
Do not invert Phase217. Move to a genuinely distinct hypothesis family preregistered before observing its results.