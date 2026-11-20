"""C27 independent two-clock, strictly queued safety governor.

At open t, previously queued trims may fill. The open-t exposure measurement
can only enqueue a trim for open t+1; it cannot trade at open t. Strategic
weekly orders are separate and must be derived from completed closes.
This module intentionally does not assert an unachievable gap-proof hard cap.
"""
import math

ASSET_CAP = 0.40
GROSS_CAP = 0.90
EPS = 1e-12

def validate_weights(weights):
    if not weights or any(not math.isfinite(float(w)) or float(w) < 0 for w in weights.values()):
        raise ValueError("C27_INVALID_WEIGHTS")
    return {a:float(w) for a,w in weights.items()}

def planned_trim(observed, *, asset_cap=ASSET_CAP, gross_cap=GROSS_CAP):
    """Return sell-only target computed from a previous opening observation.

    Per-asset trims precede proportional gross-cap reduction. No shorting,
    buying, or redistributing the freed allocation.
    """
    w=validate_weights(observed)
    if not (0 < asset_cap <= gross_cap <= 1):
        raise ValueError("C27_INVALID_CAPS")
    target={a:min(v,asset_cap) for a,v in w.items()}
    total=sum(target.values())
    if total>gross_cap:
        factor=gross_cap/total
        target={a:v*factor for a,v in target.items()}
    assert all(target[a] <= w[a]+EPS for a in w)
    return target

def queue_sell_fractions(observed):
    """Fractions of *units* to sell at next open, never target weights.

    Units, unlike weights, are stable across the intervening price gap.
    A next-open gap can still cause residual post-fill cap breaches.
    """
    w=validate_weights(observed)
    target=planned_trim(w)
    return {a:0. if w[a]<=EPS else max(0.,min(1.,1-target[a]/w[a])) for a in w}

def execute_queued_units(current_weights, fractions):
    """Apply old sell orders to current marked holdings, no same-open decision.

    The caller must account for fees and funding and then re-normalize the
    post-cost portfolio; this function only supplies pre-cost target weights.
    """
    w=validate_weights(current_weights)
    if set(w)!=set(fractions):
        raise ValueError("C27_ORDER_ASSET_MISMATCH")
    if any(not math.isfinite(float(f)) or not 0<=float(f)<=1 for f in fractions.values()):
        raise ValueError("C27_INVALID_ORDER")
    return {a:w[a]*(1-float(fractions[a])) for a in w}

def breach(weights, *, tolerance=1e-10):
    w=validate_weights(weights)
    return (max(w.values())>ASSET_CAP+tolerance or
            sum(w.values())>GROSS_CAP+tolerance)

def two_clock_step(marked_weights, queued_fractions):
    """Fill prior queue, then prepare next queue from current observation.

    The next queue must NOT be executed until the following open. Return
    pre-cost holdings and an explicit flag when gap exposure persists.
    """
    filled=execute_queued_units(marked_weights,queued_fractions)
    next_queue=queue_sell_fractions(filled)
    return {"post_fill_pre_cost_weights":filled,
            "next_open_sell_fractions":next_queue,
            "post_fill_cap_breach":breach(filled),
            "needs_next_open_trim":any(f>EPS for f in next_queue.values())}
