#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
REQ=("return","max_drawdown","profit_factor","payoff","win_rate","positive_days","trades","tail_p01","tail_p05","tail_p50","tail_p95","tail_p99","asset_pnl_contribution","max_asset_concentration","regimes")
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("path"); a=ap.parse_args(); p=Path(a.path); d=json.loads(p.read_text()); assert d["phase"]==225 and d["cutoff"]=="<2026-01-01" and len(d["specs"])==8
 x=dict(d); sha=x.pop("deterministic_payload_sha256"); raw=json.dumps(x,sort_keys=True,separators=(",",":")); assert hashlib.sha256(raw.encode()).hexdigest()==sha
 survivors=[]
 for spec,folds in d["specs"].items():
  assert set(folds)=={"2023","2024","2025"}; coherent=True
  for yr,z in folds.items():
   assert set(z)=={"base","severe","supersevere"}
   for stress,m in z.items():
    assert all(k in m for k in REQ); assert m["tail_p01"]<=m["tail_p05"]<=m["tail_p50"]<=m["tail_p95"]<=m["tail_p99"]; assert set(m["asset_pnl_contribution"])=={"BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"}; assert set(m["regimes"])=={"bull","bear","sideways"}
   b,s,ss=z["base"],z["severe"],z["supersevere"]; assert s["return"]<=b["return"]+1e-12 and ss["return"]<=s["return"]+1e-12
   coherent &= b["return"]>0 and b["profit_factor"]>1 and b["positive_days"]>.5 and b["trades"]>=30
  if coherent: survivors.append(spec)
 print(json.dumps({"phase":225,"payload_sha256":sha,"survivors":survivors,"survivor_count":len(survivors),"decision":"SURVIVE_TRAINING_DIAGNOSTICS" if survivors else "REJECT_FAMILY_NO_RESCUE"},sort_keys=True))
if __name__=="__main__": main()
