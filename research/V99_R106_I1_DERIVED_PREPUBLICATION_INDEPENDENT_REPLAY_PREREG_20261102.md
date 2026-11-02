# V99 I1 — fail-closed independent replay BEFORE derived-source publication (2026-11-02)

## Scope and rationale

The current CoinAPI per-symbol-to-daily adapter runs an independent original-byte replay only in synthetic GitHub CI. A real nonfixture CLI invocation can publish a derived daily file and provenance sidecar without running that independent check. This is an internal data-integrity gap, **not** the external licensed-history blocker and **not** evidence of economic edge.

## Precommitted change

Before the final exclusive publication of any derived daily gzip and sidecar, hard-link both fully written temporary files into a private temporary staging directory with the exact day filenames, invoke the existing separately implemented independent original-to-derived oracle on the staged pair and the original source specification, require its independent row count to match the converter's count and its status to be the exact derived-only result, and only then publish to the requested output directory via exclusive hard links. If the oracle raises, rejects, or returns an inconsistent result, publish **neither** file. Ensure cleanup of all staging files, temporary files and links on every failure. Preserve original provider bytes and hashes, arrival ceil / event floor, source order, sidecar provenance, no overwrite, and bounded streaming. No fallback to synthetic source.

## Adversarial controls and decision

CI must exercise a normal two-asset source conversion with independent replay, and inject an independent-oracle rejection to verify no final artifacts are published. Existing tamper, clock, missing-source, duplicate, and no-overwrite tests must continue to pass. Independent replay may increase import latency; it is mandatory for the nonfixture data path, not a performance or profitability claim. No validation/holdout, Frozen, paper, champion or orders touched. This fix cannot unlock TRAIN without the licensed 661-day original quote archive, dated native fees, lot/margin/settlement terms and independent complete execution provenance. **SOURCE HOLD / NO PROMOTION**.
