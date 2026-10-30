# Frozen paper seed

`paper_seed_v13.zip` contains compact CSV deltas with public Binance USD-M
observations from 2026-08-01 through the first local paper checkpoint. It lets a
clean GitHub runner reconstruct the July research history from official monthly
archives and preserve the frozen forward boundary without committing the full
canonical dataset.

The hourly workflow extends this seed only from checksummed daily archives at
`data.binance.vision`. It does not use credentials, private endpoints, or real
orders.
