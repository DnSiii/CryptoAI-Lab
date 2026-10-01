#!/usr/bin/env python3
"""Independent mechanical audit for frozen Phase206 results; no parameter search/rescue."""
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser(); p.add_argument('--input',default='reports/v98_independent_phase206_results.json'); p.add_argument('--out',default='reports/v98_independent_phase206_audit.md'); a=p.parse_args()
 r=json.loads(Path(a.input).read_text()); rows=[]
 for spec,folds in sorted(r['specs'].items()):
  base=[folds[y]['base'] for y in ('2023','2024','2025')]; sev=[folds[y]['severe'] for y in ('2023','2024','2025')]; sup=[folds[y]['supersevere'] for y in ('2023','2024','2025')]
  gate_base=all(x['return']>0 and x['profit_factor']>1 for x in base)
  gate_sev=all(x['return']>0 and x['profit_factor']>1 for x in sev)
  gate_sup=all(x['return']>0 and x['profit_factor']>1 for x in sup)
  rows.append((spec,gate_base,gate_sev,gate_sup,[x['return'] for x in base],[x['profit_factor'] for x in base],max(x['max_asset_concentration'] for x in base),min(x['tail_p01'] for x in base),min(x['max_drawdown'] for x in base),sum(x['trades'] for x in base)))
 passed=[x for x in rows if x[1]]; decision='ADVANCE_FOR_DEEPER_VALIDATION' if passed else 'REJECT_FAMILY_NO_RESCUE'
 lines=['# V98 Independent — Phase206 mechanical audit','',f"Decision: **{decision}**",'',f"Deterministic payload SHA256: `{r['deterministic_payload_sha256']}`",'', 'Mechanical gate: every 2023/2024/2025 base fold must have return > 0 and PF > 1; severe/supersevere are reported independently and are not used to rescue a failed base fold.','', '| spec | base 3/3 | severe 3/3 | super 3/3 | base returns 23/24/25 | base PF 23/24/25 | worst MDD | max conc | worst p01 | trades |','|---|---:|---:|---:|---|---|---:|---:|---:|---:|']
 for s,b,v,u,rets,pfs,conc,p01,mdd,trades in rows:
  lines.append(f"| {s} | {b} | {v} | {u} | {' / '.join(f'{x:.3f}' for x in rets)} | {' / '.join(f'{x:.3f}' for x in pfs)} | {mdd:.3f} | {conc:.3f} | {p01:.3f} | {trades} |")
 lines += ['', '## Integrity / anti-overfit notes','', '- This audit evaluates all eight frozen specs; it does not add thresholds, invert signals, select assets, or gate regimes.', '- Validation/final holdout remains unopened.', '- Regime, concentration and complete-trade tails remain diagnostic only; isolated pockets cannot rescue a failed family.', '- Funding source timestamps are causally restricted to <= t-1 by evaluator invariant.', '', f"Base-fold-stable specs: {len(passed)}/8."]
 Path(a.out).write_text('\n'.join(lines)+'\n')
 print(decision, 'base_stable',len(passed),'of',len(rows))
if __name__=='__main__': main()
