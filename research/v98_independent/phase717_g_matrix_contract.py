"""V98 Independent Phase717: immutable G 5-path x 3-cost x 2-order matrix."""
from __future__ import annotations
import math
PATHS=frozenset(('B_phase252','G_full','G_minus_opportunity','G_minus_relative_value','G_minus_recovery'))
TIERS={'base':.0007,'severe':.0012,'supersevere':.002}
ORDERS=('carried_before_fill','new_after_fill')

def require_g_matrix(paths,tiers,orders):
    if not isinstance(paths,dict) or set(paths)!=PATHS:raise ValueError('G five-path freeze required')
    if not isinstance(tiers,dict) or set(tiers)!=set(TIERS):raise ValueError('G three costs required')
    for name,fee in TIERS.items():
        v=tiers[name]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v-fee)>1e-15:
            raise ValueError('G frozen cost mismatch: '+name)
    if tuple(orders)!=ORDERS:raise ValueError('G two settlement orders required')
    return 30
