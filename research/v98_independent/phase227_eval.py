#!/usr/bin/env python3
"""V98 Independent Phase227 frozen residual-reversal evaluator.
Uses the already-audited Phase226 accounting engine unchanged except for the preregistered trade direction and Phase227 output identity. Fails closed if expected source anchors drift.
"""
from pathlib import Path
src=Path(__file__).with_name("phase226_eval.py").read_text()
anchors={
 'doc':'V98 Independent Phase226 — frozen cross-sectional idiosyncratic momentum. Training only 2023-2025.',
 'long':'if longs: picks.append((max(longs,key=lambda a:resid[a].iloc[i]),.5))',
 'short':'if shorts: picks.append((min(shorts,key=lambda a:resid[a].iloc[i]),-.5))',
 'out':'default="research/v98_independent/phase226_results.json"',
 'meta':'out={"phase":226,"family":"cross_sectional_idiosyncratic_momentum","cutoff":"<2026-01-01","specs":{}}'
}
for name,text in anchors.items():
 if src.count(text)!=1: raise RuntimeError(f"Phase227 fail-closed source anchor drift: {name}")
src=src.replace(anchors['doc'],'V98 Independent Phase227 — frozen cross-sectional idiosyncratic residual reversal. Training only 2023-2025.')
src=src.replace(anchors['long'],'if longs: picks.append((max(longs,key=lambda a:resid[a].iloc[i]),-.5))')
src=src.replace(anchors['short'],'if shorts: picks.append((min(shorts,key=lambda a:resid[a].iloc[i]),.5))')
src=src.replace(anchors['out'],'default="research/v98_independent/phase227_results.json"')
src=src.replace(anchors['meta'],'out={"phase":227,"family":"cross_sectional_idiosyncratic_residual_reversal","cutoff":"<2026-01-01","specs":{}}')
code=compile(src,"phase227_frozen_engine","exec")
exec(code,{"__name__":"__main__","__file__":str(Path(__file__).with_name("phase226_eval.py"))})
