# V99 I1 — independently signed 661-day journal binding: implementation and result (2026-10-31 22:51 BRT)

## Problem and change
Signed OPEN/MARK/SETTLE_BATCH receipts were previously verified, but `replay_signed` accepted unsigned daily BTC/ETH index values, fold-edge indices, regime assignments, initial collateral and 180 scenario decision rows. A caller could alter USD NAV/benchmark or fold classification while preserving valid per-event signatures. This is a real economic-input integrity defect, not an alpha result.

The preregistration was committed **before code** at [49c50f0](https://github.com/DnSiii/CryptoAI-Lab/commit/49c50f069cd34854b96eb632a97ccf943f8aa3bd), `research/V99_R106_I1_SIGNED_WHOLE_JOURNAL_BINDING_PREREG_20261031.md`. The signed nonfixture replay now requires a separate external-auditor Ed25519 attestation of a canonical digest over the **entire** 661-day journal, excluding only the attestation path itself. This binds all economic input values in both scenarios. Existing individual event signatures remain mandatory; the auditor public key and SHA256 pin remain external to the repository. Absent/mismatched signature fails before processing events or producing output.

## Executed CI and independent source gate
- [GitHub Actions 41262703903](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41262703903), head `bacdafccaf508d5954c356934c72f81121dc1ffb`: **SUCCESS** (completed 2026-11-01 01:51 UTC). 8 Decimal cost tests + 12 signed-evidence/adversarial tests + 8 signed 661-day adapter tests + 6 signed CLI tests = **34/34 PASS**.
- The 12 signed-evidence tests include a real ephemeral Ed25519 fixture signature over the JOURNAL digest, verifying that changes to daily BTC index, regime or decisions are rejected. Test keys and source bytes are **synthetic**, not venue-issued.
- The original-source gate and independent original-byte oracle ran again and confirmed **182 archived causal signal observations; 0/182 original signal/source intersections; 0 certified complete option lifecycles**. These are provenance checks, **not** economic TRAIN.
- Intermediate commits had CI failures while the implementation and test harness were being aligned; the final head run above passed. Other 661-day synthetic-only CI on earlier head passed. No signed historical economic return was computed.

## Decision and critical path
**SOURCE HOLD — NO PROMOTION.** The signed-input manipulation route is closed for the tested code path. Historical source is still absent: **658/661** licensed original Deribit option tape days missing, including complete BTC/ETH BBO/size clocks and entry/mark/settlement lifecycle; no account-specific historical fee tier, contract lots, margin/liquidation, settlement/fill evidence or independently controlled real auditor signature and entitlement. No **0/180** lifecycles can be economically certified.

Acceptable external alternative: licensed Tardis/CoinAPI/Amberdata or exchange-authorized equivalent with exact historical originals, lawful research rights, dated native account terms and independent source/ledger oracle. Without this, full TRAIN severe/supersevere economics and five-fold certification cannot be honestly performed. Do not unlock sealed validation [2023-10-01, 2024-01-18) or final holdout >=2024-01-18. Frozen V16/V99, paper, legacy champion, dashboard historical claims unchanged; **NO ORDERS, NO ROI CLAIMS, NO PROMOTION**.

Next technical work must be source acquisition/intake and independently verified real-run closure, not new parameter grids or synthetic phase counting.
