#!/usr/bin/env python3
"""V98 M predeclared five-path ablation registry, no historical economics."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from phase866_k_sevenslot_source import pinned_training_frames
from phase900_m_persistent_growth_source import compose_m

PATHS=('M_core_only','M_full','M_minus_opportunity','M_minus_relative_value','M_minus_recovery')
EXCLUDE={'M_core_only':frozenset(('opportunity','relative_value','recovery')),
         'M_full':frozenset(),
         'M_minus_opportunity':frozenset(('opportunity',)),
         'M_minus_relative_value':frozenset(('relative_value',)),
         'M_minus_recovery':frozenset(('recovery',))}
FULL_PIN='7a8c0210340377b459a568ab00cc5c7e772619a44155f5f7b6f266b8bb55613d'

def freeze_paths(root):
    close,high=pinned_training_frames(Path(root)/'phase243_clean4_canonical')
    out={k:compose_m(close,high,excluded=EXCLUDE[k]) for k in PATHS}
    hashes={k:hashlib.sha256(v.to_csv(float_format='%.12g').encode()).hexdigest() for k,v in out.items()}
    if hashes['M_full']!=FULL_PIN:raise PermissionError('M full frozen hash drift')
    return out,hashes

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    frames,hashes=freeze_paths(root)
    result={'phase':903,'source_only':True,'historical_pnl_computed':False,
            'validation_2025_read':False,'holdout_accessed':False,'external_benchmarks_used':False,
            'promotion_eligible':False,'paths_sha256':hashes}
    (root/'phase903_m_frozen_paths_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))
