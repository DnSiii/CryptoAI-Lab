# V99 I1 — signed MARK native exit-fee veto: verified result (2026-11-01)

## Scope and preregistration
Preregistered before implementation at `research/V99_R106_I1_SIGNED_MARK_EXIT_NATIVE_FEE_PREREG_20261101.md`, commit `19dbd6a6881344af6ec34e2e93045c9722640cca`. TRAIN-only software accounting repair. No alpha selection or change of strategy rules; sealed validation/holdout, Frozen, paper and champion untouched. No orders.

## Defect closed
Previously `costed_mark` checked the modeled severe/supersevere floor and signed event identity, but did not check the independently signed historical native account-tier fee schedule. The modeled exit liability could therefore understate a historical account fee and overstate NAV / maintenance headroom.

Nonfixture MARK now invokes the same independently signed dated-fee preflight used for OPEN and SETTLE_BATCH, using the original close-side **short ask / long bid** premiums, exact signed MARK digest, scenario, original archive manifest, quantity and clock. The independent per-leg Decimal oracle checks the primary fee calculator. An undercharge is vetoed before `mark_to_exit` mutates marks. MARK remains a hypothetical exit-cost liability, never an executed trade or a native fill receipt.

## GitHub execution evidence (final code SHA `3b4b45cb30963cb144771c6b368b07ce03785c50`)
- [Cost-bound source gate Actions 41327955652](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41327955652): **SUCCESS**, 70/70 synthetic/adversarial tests across 7 groups (8 + 16 + 7 + 13 + 8 + 6 + 12). The original signal/option join and independent original-byte oracle were actually reexecuted; source gate still reports **0/182** source-ready intersections.
- [Dated native fee preflight Actions 41327955668](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41327955668): **SUCCESS**, 58/58 synthetic/integration tests across 6 groups (16 + 7 + 8 + 8 + 13 + 6). Signed 661d mock adapter ran, but is NOT venue economics; the job explicitly reports **0/180** certified.
- New adversarial checks: dated MARK fee per-leg parity, signed MARK undercharge, nonfixture wallet MARK mutation veto, primary fee tampering vetoed by independent oracle.

## Decision and exact remaining blocker
**SOURCE HOLD — NO PROMOTION.** 658/661 days of the original Deribit BTC/ETH option tape are absent. No authenticated full 661d quote/mark/settlement lifecycle, original venue account tier and fee schedule, original execution-depth/fill evidence, margin/liquidation terms or independent original-byte economic replay. Consequently there is **no valid historical options TRAIN**, no fold-level economic gates, no certified ROI, no authorization to freeze or open validation/holdout. Software CI success cannot replace this evidence.

Next critical-path action: acquire or access the complete, licensed, independently hashed original 661d source bundle with all lifecycle events and historical account terms, then run the unchanged signed original-source bridge and independent economic oracle. Do not infer the missing data or retune I1 to synthetic outcomes. Continue parallel distinct-architecture research only on isolated TRAIN if justified.
