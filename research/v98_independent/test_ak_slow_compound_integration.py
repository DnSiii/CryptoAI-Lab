#!/usr/bin/env python3
"""AK full seven-slot deterministic synthetic end-to-end ledger smoke test.

No historical source or validation data are loaded by this test.
"""
import math
import numpy as np
import ak_slow_compound_90cell as engine
from ak_slow_compound_sources import source_bundle

H = 2400
engine.HOURS = H
engine.FIRST_2024 = 2300
t = np.arange(H, dtype=np.float64)
drift = np.array([.00012, .00017, .00008, .00022])
c = 100. * np.exp(t[:, None] * drift +
                   .004 * np.sin(t[:, None] /
                                np.array([41., 47., 53., 59.])))
o = np.vstack((c[0], c[:-1]))
h = np.maximum(o, c) * 1.003
l = np.minimum(o, c) * .997
q = np.ones_like(c) * 1e9
r = np.zeros_like(c)
e = np.zeros_like(c)
e[::8] = 1.
r[::8] = (.0001, -.0001, .00012, -.00012)
frames = (o, h, l, c, q, r, e, c * .995, c * 1.005)
sources = source_bundle(c, h, l, r, e)
risks = engine.prepare_risk(frames)
for path in engine.PATHS:
    out = engine.cell(path, 'immediate', 'base',
                      'carried_before_fill', frames, sources, risks)
    assert out['passed']
    assert out['executed_hours'] == H - engine.START_EXECUTION
    assert out['rebalances'] > 0
    assert out['initial_nav'] == 10000.
    assert out['final_nav'] > 0
    assert out['validation_2025_read'] is False
    assert out['annual']['2023']['total_utc_days'] > 0
    assert out['annual']['2024']['total_utc_days'] > 0
    assert all(math.isfinite(out[k]) for k in
               ('final_nav','turnover','fees','slippage','funding',
                'max_drawdown','two_year_cagr'))
print('AK_COMPLETE_FIVE_PATH_SYNTHETIC_LEDGER_PASS')
