# V98 Independent — Phase228 postmortem

Status: **REJECT_FAMILY_NO_RESCUE**

## Evidence
Phase228 tested the preregistered volatility-compression breakout-continuation family with the frozen 8-spec grid, calendar folds 2023/2024/2025, realized PIT funding, and 7/14/28 bp round-trip cost stresses. Deterministic payload SHA256: `cd3de1520e5905d4edd850e2114b5e89798aded4d39ddd8cae2f8b445689fc81`.

Representative frozen spec `cw24_bw24_h4` fails immediately under base cost: 2023 return -36.2616%, PF 0.7528, max DD -40.0693%, positive days 12.33%; 2024 return -47.9647%, PF 0.7758, max DD -49.8497%, positive days 15.30%. Severe and supersevere costs deteriorate monotonically.

The failure is not a single-regime artifact: in 2023 base, bear/bull/sideways returns are -7.18%/-4.79%/-27.88%; in 2024 base they are -6.78%/-24.86%/-25.71%. Median trade is negative in both years. Asset PnL contribution is broadly negative rather than depending on one removable loser; post-result asset deletion is forbidden.

## Scientific decision
The family does not approach the frozen annual gate (return >0, PF>1, positive days>50%, trades>=30 in each year). No threshold rescue, asset deletion, regime filter, grid extension, tail clipping, or cost relaxation is permitted. Champion remains unchanged. 2026+ remains unopened.

## Implication for next hypothesis
Do not continue tuning volatility-compression breakout parameters. Phase229 must be scientifically distinct and preregistered before any result observation. A justified direction is an **intraday periodicity / time-of-week conditional return** family: crypto trades continuously but liquidity, funding settlement, and global market participation have stable clock structure. The signal must be estimated only from prior observations for the same UTC bucket, with execution at the next open, and must not use Phase228 outcomes to choose profitable hours ex post.