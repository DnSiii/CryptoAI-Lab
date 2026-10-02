# V98 Independent — Phase210 postmortem

Decision: **REJECT_FAMILY_NO_RESCUE**.

Phase210 tested the preregistered hour-of-week residual reversal family with exactly 8 frozen specifications over chronological training folds 2023/2024/2025. The workflow rebuilt training-only data, passed the `<2026-01-01` firewall, executed twice, and produced identical report SHA256 `2b07fcea363436ac4171a1fbe62d3e98b3a3ee8c23bb8140b7f9590ed9b733c8`. The mechanical gate found zero specifications with base return > 0 and Profit Factor > 1 in all three folds.

Failure mechanism is already decisive in the first frozen specification (`how168d_z2_hold12h`). In 2023 base return is -87.6812%, PF 0.8721, MDD -88.9562%, win rate 43.78%, positive days 43.84%, with all four traded alts negative. Severe return is -96.6705% and supersevere -99.7574%. Bull, bear, and sideways regime returns are all negative. In 2024 base remains -67.3530%, PF 0.9413, MDD -76.4819%, with all four alts negative and all three regimes negative. This is broad economic failure rather than concentration in one asset/regime or a cost-only failure.

Funding contributions are small relative to the losses and cannot explain/rescue the family. Cost escalation materially worsens the already-negative edge. No inversion, threshold rescue, asset exclusion, regime filter, or post-hoc parameter search is permitted.

Validation/final holdout remains unopened. Champion remains unchanged. V16/V99 and V99 paper state are untouched.
