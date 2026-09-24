# V99 R106 Phase134 — technical incident record

Date: 2026-09-24

The first Phase134 workflow attempt (run 36021323027) failed before any PnL result was produced. The preregistered runner attempted `data.volume`, but the immutable `FuturesData` interface exposes market fields through `data.frames`; canonical volume is `data.frames["volume"]`.

Scientific disposition: **not a rejection and not a pass**. This was an implementation/interface failure only.

The repair in commit `affa26dba33beae197eb0e9e754602a6bac2f100` changes only the accessor from `data.volume` to `data.frames["volume"]`. It does not change the preregistered feature, direction, 24h smoothing window, 168h baseline, robust cross-sectional normalization, t-1 shift, gross 0.20, train cutoff, costs, folds, or any downstream gate.

Frozen V16/V99 assets were SHA-checked unchanged by the failed attempt. The untouched holdout was not parsed. The corrected workflow must therefore be interpreted as the first scientifically evaluable Phase134 attempt; no parameter retuning or sign flip is permitted.
