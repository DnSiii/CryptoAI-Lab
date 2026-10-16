# Phase448 immutable pre-PnL rejection

Original prereg SHA256 `5fa86ae05ccf4c17f204315ee3889be4b639bb9d0ba7b3d4156898acb5ebdb62`; remote prereg commitment `783883ab7623b56e925c9623c0458c4c9996a350`.

Pre-PnL smoke check corrected a prose error: the exact frozen Phase252 warmup target is 0.3125 per asset, not 0.25. Local pre-PnL amendment SHA256 `9442969dfadfafab08ec90feaaf91212f973f7ac2404560462c688b9681e25ac`. No PnL was computed before the correction.

157 weekly decisions, 60 leader and 97 defensive weeks, 26 RV activations, **zero recovery episodes**. Preregistered recovery minimum was two. Decision `REJECT_PHASE448_PRE_PNL_NO_RESCUE`; no candidate PnL calculated. Source hashes and causal checks passed; 51 regression tests passed. No change to any other engine, workflow, validation or holdout. BNB independent funding verification remains unresolved.
