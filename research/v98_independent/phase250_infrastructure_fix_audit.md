# V98 Independent Phase250 — infrastructure-fix audit

Status: INFRASTRUCTURE FIX ONLY / SCIENTIFIC SPEC UNCHANGED.

The first Phase250 workflow run failed after source rebuild and after entering the evaluator, before any Phase250 result JSON was produced, committed, uploaded, or inspected.

Failure:
- diagnostic code constructed a 2023-2025 boolean series after already slicing the allocator to the training window;
- it then attempted to combine that 26,304-row Series with the original 27,048-row warmup+training mask;
- pandas correctly raised a broadcast/shape ValueError.

Correction:
- slice the allocator once to the frozen 2023-2025 training window;
- compute the active-row mask on that sliced frame;
- select active rows from the same aligned frame.

A regression test was added for this alignment.

No scientific field changed:
- funding lookback remains 168h;
- cheap pair remains 30%/30%;
- expensive pair remains 20%/20%;
- gross remains 1.00;
- decision clock remains 23:00 UTC;
- comparator, costs, funding stresses, folds and all promotion gates remain frozen.

No Phase250 PnL or performance metric was available to the researcher before this correction. Reexecution is therefore an admissible deterministic plumbing repair, not a rescue or retune.
