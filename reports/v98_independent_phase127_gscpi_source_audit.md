# V98 Independent — Phase127 GSCPI source/causality audit

Independent audit performed without inspecting numeric GSCPI observations or crypto PnL.

- The official New York Fed product describes GSCPI as a monthly gauge integrating transportation costs and manufacturing indicators.
- Official publication timing is at or shortly after 10:00 a.m. ET on the fourth business day of each month. Any later alpha phase must therefore use a conservative post-publication lag fixed before PnL inspection; same-month retroactive availability is forbidden.
- The Phase127 DATA_ONLY gate remains limited to 2023-01-01..2025-12-31 and records only acquisition/integrity metadata and hashes.
- No alternate source, proxy, interpolation, fill, parser/source rescue, parameter search, V16, V99, Phase083 selection information, validation, or final holdout is permitted.

Decision discipline: PASS_DATA_ONLY is only permission to preregister a later economic hypothesis; it is not evidence of alpha and cannot create a champion.
