# V99 R106 D1 — C111 native CSV ambiguity rejection (2026-10-21)

Status: **DATA_ONLY/HOLD — NO PROMOTION**. C1 and C2 remain permanently rejected. The new D1 architecture is still pre-economic and its integrated source closure has not been published. This note does not assert historical ROI, actual fills, settled account funding, or first-party authentication.

## Reproducible local finding

The previous D1 source reader used `csv.DictReader` without enforcing unique headers or row width. Duplicate `open` or `rate` headers silently overwrite one field; a recomputed SHA-256 binds the ambiguous bytes but does not make the parsed economic data trustworthy. Ragged CSV records also passed the header-presence check.

C111 local patch (not remotely published): strict unique, nonempty header validation, no duplicate keys, no extra/missing/empty row fields for spot/perp/funding CSV. Four adversarial regression tests were added. **25 native-source tests passed**, and **59 focused source/fee/partition tests passed**. All tests use synthetic fixtures; no authenticated historical economic result was generated.

## Remote release boundary

The target branch was verified at `5e98a636721b0e94bc7af782957f8b59d2fc63c3`; neither `research/tools/v99_r106_d1_native_source_gate.py` nor its corresponding test file exists on that remote branch. Do not treat this documentation-only commit as deployment of the fix. Publish the complete add-only reviewed source closure without overwriting divergent remote files, then run integrated CI and acquire real historical OKX native fee/funding/execution provenance before any TRAIN economic evaluation. Keep validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 sealed.

No orders, no paper/result modifications, no frozen model modifications, no promotion.
