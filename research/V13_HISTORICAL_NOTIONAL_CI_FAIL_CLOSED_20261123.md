# V13 historical notional CI: verified fail-closed evidence (2026-11-23)

Scope: read-only investigation, NOT an approval to rewrite published paper or adjust historical trades. Source workflow: [45221308738](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/45221308738), research commit `f0149ff6294de9add1c9ca5cf04ff82adbcb0eb2`.

## Reproducible evidence

- Run completed **failure** on 2026-11-23 16:52 UTC, at the intended `Fail closed on unresolved historical movements` step; both repository checkouts, audit execution and evidence upload succeeded.
- Published `paper-results` commit checked out: `2a89332f5ff7e5ccfac80c27a91e0b970bb3cccd`.
- Published `reports/paper_v13_ledger.json` SHA-256: `e7c0b99498173bb5d94fd4a86ac6be17a9468531503c8d742f5187b2e44793cc`.
- Auditor stderr: `FAIL CLOSED: 314 inconsistent movements; 1425 missing original raw amounts; historical paper unchanged`.
- Preserved evidence artifact: [14839304464](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/45221308738/artifacts/14839304464), ZIP digest `sha256:2b77d2fcefbda6d6b3a1afb9fac1c0f1734dc3ed97182bb28246f6d177483d51`, expires 2027-02-21.

## Interpretation and remaining block

The 314 count is **all non-accepted categories** according to `scripts/audit_paper_v13_raw_notional_readonly.py`, not necessarily 314 positive raw/display mismatches. The earlier reported 310 positive discrepancies cannot be equated to the 314 total without reading `historical-notional-audit.json` in the artifact and comparing classification counts and example indices. Separately, 1,425 displayed-positive movements have no recorded original raw amount; **absence of precision is not proof of an invalid trade**, but prevents complete raw/display certification. Do not infer missing amounts, synthesize trades, or blanket-exempt these cases.

The paper verifier currently checks raw/display consistency when raw is available, and allows zero displayed value only for strictly positive raw below R$0.005 that rounds to zero. Preserve these bounds and fail-closed behavior. Passing the regular paper dashboard CI does not certify historical provenance.

## Next critical path

1. Read the preserved artifact JSON to enumerate exact categories and indices, reconcile the 310 versus 314 counts, and correlate discrepancies to the original generator and its timestamped version.
2. Compare published raw/display fields with original execution inputs and conversion factors using immutable source commits; classify genuinely legitimate subcent orders separately from inconsistencies.
3. Fix only demonstrably erroneous future generation/verification logic in the research branch, run adversarial tests and independent GitHub Actions; never mutate `paper-results`, V16/V99 Frozen, sealed validation or holdout.
4. Keep the public dashboard visibly marked research-only/stale until independently reconciled; no engine promotion, profit claim or real orders.

**Decision: NO PROMOTION.**
