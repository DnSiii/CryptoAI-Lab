"""V98 B0 preregistered causal overlay; no PnL or approval claim."""
import math
import statistics

WINDOW = 168
REFERENCE_WINDOWS = 12

def regime_multiplier(completed_closes):
    """Only completed closes through decision bar t; return 0 if insufficient."""
    p = list(completed_closes)
    required = (REFERENCE_WINDOWS + 1) * WINDOW + 1
    if len(p) < required:
        return 0.0
    p = p[-required:]
    if any(not math.isfinite(float(x)) or x <= 0 for x in p):
        raise ValueError("INVALID_COMPLETED_CLOSE")
    r = [math.log(p[i] / p[i-1]) for i in range(1, len(p))]
    windows = [math.sqrt(sum(x*x for x in r[i:i+WINDOW]) / WINDOW)
               for i in range(0, len(r), WINDOW)]
    reference = statistics.median(windows[:-1])
    if reference <= 0:
        return 0.0
    return 0.5 if windows[-1] > 2.0 * reference else 1.0

def governor_multiplier(completed_equity, completed_peak):
    """Both values known at completed decision bar t; no future bar input."""
    if not all(math.isfinite(float(v)) for v in (completed_equity, completed_peak)):
        raise ValueError("NONFINITE_EQUITY")
    if completed_equity <= 0 or completed_peak < completed_equity:
        raise ValueError("INVALID_COMPLETED_EQUITY")
    drawdown = 1.0 - completed_equity / completed_peak
    return 1.0 if drawdown <= 0.10 else (0.5 if drawdown <= 0.20 else 0.25)

def compose_weights(sleeve_weights, routers, governor, *, gross_cap=0.75, asset_cap=0.40):
    """Deterministic cap projection; nonnegative sleeve weights only."""
    assets = tuple(sorted(sleeve_weights))
    if not assets or set(assets) != set(routers):
        raise ValueError("ASSET_GRID_MISMATCH")
    if not 0 <= governor <= 1 or not 0 < gross_cap <= 1 or not 0 < asset_cap <= 1:
        raise ValueError("INVALID_CAP")
    raw = {}
    for a in assets:
        components = tuple(sleeve_weights[a])
        if len(components) != 4 or any(not math.isfinite(float(v)) or v < 0 for v in components):
            raise ValueError("INVALID_SLEEVE")
        if not math.isfinite(float(routers[a])) or not 0 <= routers[a] <= 1:
            raise ValueError("INVALID_ROUTER")
        raw[a] = min(asset_cap, sum(components) * routers[a] * governor)
    total = sum(raw.values())
    factor = min(1.0, gross_cap / total) if total else 1.0
    return {a: raw[a] * factor for a in assets}
