# V99 R106 Phase117 — archive-integrity execution addendum

Recorded after the first Phase117 workflow aborted **before any signal/PnL was produced**.

## Observed infrastructure fact
The official monthly BTCUSDT mark-price and index-price archives for 2022-04 do not have identical timestamp vectors. The original implementation correctly aborted before computing mark/index dislocation.

## Frozen integrity handling
This addendum changes **only archive ingestion**, not the preregistered alpha:
- A monthly mark/index pair is usable only when both archives pass checksum/CRC/row validation **and their timestamp vectors match exactly**.
- If either monthly archive is absent **or the monthly pair fails exact timestamp alignment**, that month is treated as an unusable monthly pair and falls back to the Phase116-admitted **paired daily dates** for that month.
- Every fallback daily mark/index pair must itself pass checksum/CRC/row validation and exact timestamp alignment.
- A daily pair that fails exact alignment is excluded entirely and counted as an integrity rejection; its rows are not intersected, filled, repaired or synthesized.
- No extra date outside the Phase116 paired-date manifest may be introduced by fallback.
- January 2024 remains daily-only through 2024-01-17; no January monthly archive may be requested.

The 24h RMS feature, direction, t-1 lag, gross, severe gate, folds and all other Phase117 scientific choices remain unchanged. No Phase117 PnL existed when this ingestion rule was recorded.
