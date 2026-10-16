# V99 R106 — prospective source and scheduling audit (2026-10-16 04:49–04:53 BRT)

Research branch only. DATA_ONLY/HOLD; **no new R106 economic experiment, promotion, champion, holdout access, or frozen modification**.

## New durable evidence

Durable source branch `research/v99-r106-live-receipts` head `3e73fd04df7c7e904af5fbd8b40fbeb634f30a6b` (07:30:09 UTC). Source folders contain **12 market buckets and 12 native-terms buckets, but only 8 paired UTC buckets** in 36 hourly slots (2026-10-14 20 UTC through 2026-10-16 07 UTC); 28 slots have no pair. Paired UTC buckets: 2026-10-14 20,23; 2026-10-15 01,07,13,20,23; 2026-10-16 04. No adjacent paired UTC buckets. The newest 07 UTC market-only capture was from successful scheduled run `38867574958`; there is no matching 07 UTC terms folder. This is **not** an atomic acquisition.

Latest market manifest received 07:30:08 UTC; all five latest confirmed closes 07:00 UTC; earliest conservative t−1 decision 09:00 UTC. Durable proof claims run 38867574958, and GitHub reports the run completed successfully and archived `v99-r106-hourly-okx-38867574958` (artifact 12032160779). This is GitHub provenance, **not exchange-signed first-seen authentication**.

The latest paired 04 UTC capture claims one atomic run 38850472892 for both market and terms. The next observed market at 07 UTC cannot close the missing 05–06 UTC gap. **No backfill.** The separate source/terms workflows run at different schedule minutes and cannot substitute for the single-run atomic source requirement.

## Scheduling evidence and limits

The repository-wide schedule-run query (first 100 results, oldest 2026-10-13 04:00 UTC) contains only two atomic-pair schedule runs since the workflow activation: `38824907813` (2026-10-15 23:39 UTC) and `38850472892` (2026-10-16 04:24 UTC). They both concluded successfully, but neither forms a consecutive pair with the other. This count is not proof of why any other cron slot was missed: scheduler delay, missing dispatch, concurrency, or API coverage cannot be distinguished without additional logs. The configured atomic schedule is `12 * * * *` and the three receipt workflows share the same append-only persistence concurrency group. Avoid inventing specific failed runs.

## Source-selection defect (still unresolved)

Research workflow `.github/workflows/v99-r106-okx-asof-receipts.yml` searches only the first 100 repository artifacts and falls back to fixed run `38630788811` when no prior source appears. Rapid main paper-refresh artifacts can crowd out the actual most recent source. A locally tested fail-closed prior-source selector now checks immutable durable receipts, strict hashes, source semantics, original capture times and t−1, and never claims paired continuity. Its 17 synthetic adversarial tests passed; 80 self-contained local tests passed in each of three Python hash seeds. **The selector has not been integrated:** an attempted workflow update was blocked, and the original workflow must not be described as fixed. Integration should read the durable receipt branch, verify proof and raw bytes, choose only a strictly prior capture, and fail closed without a hard-coded ancient baseline.

## Economic and dashboard firewall

V99 Frozen paper and the R98/R106 forward comparison are different ledgers. `paper-results:reports/paper_v99_research_snapshot.json` still reports `latest_data_timestamp=2026-10-10T05:00:00Z` (R98 3.877701%; R106 F1 12.339133%; F3 16.410636% *in that archived comparable period*), not current forward leadership. Do not refresh those figures with retrospective fills, or promote a DATA_ONLY source result. The main V99 Frozen paper refresh run `38869219441` completed successfully at 07:51:10 UTC; this does not constitute R106 native PnL.

## Preregistered next evidence gate

Before any R106 PnL: (1) observe two consecutive UTC hours with both original market and native terms from independently attested **same GitHub run per hour**, raw SHA and causal availability; (2) independently verify overlapping confirmed candles without revision; (3) authenticate actual venue-specific fee tier and settled funding cashflows, not merely forecast notices; (4) preserve chronological train-only selection, untouched holdout, temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, and reproducibility. Missing or late hours remain missing. No champion update until comparable validated PnL and all gates pass.
