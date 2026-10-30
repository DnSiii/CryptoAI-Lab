#!/usr/bin/env python3
"""V98 Independent Phase126: NFCI DATA_ONLY feasibility. Never emits numeric series values."""
from __future__ import annotations
import csv, hashlib, io, json, math, urllib.request
from datetime import date
from pathlib import Path

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NFCI"
START, END = date(2023,1,1), date(2025,12,31)
OUT = Path("reports/v98_independent_phase126_nfci_data_only.json")
PREREG = Path("reports/v98_independent_phase126_nfci_data_only_prereg.md")

def sha(b: bytes)->str: return hashlib.sha256(b).hexdigest()

def main():
    req=urllib.request.Request(URL, headers={"User-Agent":"CryptoAI-Lab-V98/phase126"})
    status=None; raw=b""; err=None
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status=r.status; raw=r.read()
    except Exception as e: err=type(e).__name__
    required=False; rows=[]; malformed=0; finite=0
    if status==200 and raw:
        try:
            reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            required=bool(reader.fieldnames) and "DATE" in reader.fieldnames and "NFCI" in reader.fieldnames
            if required:
                for x in reader:
                    try: d=date.fromisoformat(x["DATE"])
                    except Exception: malformed+=1; continue
                    if START<=d<=END:
                        v=x.get("NFCI","")
                        try: ok=math.isfinite(float(v))
                        except Exception: ok=False
                        finite += int(ok); rows.append(d)
        except Exception as e: err=type(e).__name__
    dates=sorted(rows); dup=len(dates)-len(set(dates)); n=len(dates)
    increasing=all(a<b for a,b in zip(dates,dates[1:]))
    finite_cov=(finite/n) if n else 0.0
    manifest=("\n".join(d.isoformat() for d in dates)+("\n" if dates else "")).encode()
    gates={"http_200":status==200,"required_columns":required,"rows_gte_150":n>=150,"finite_coverage_gte_95pct":finite_cov>=.95,"zero_duplicate_dates":dup==0,"strictly_increasing":increasing,"zero_malformed_dates":malformed==0}
    passed=all(gates.values())
    out={"engine":"V98 Independent","phase":"126","mode":"DATA_ONLY","family":"Chicago Fed NFCI financial conditions","window":{"start":str(START),"end":str(END)},"source":{"series":"NFCI","http_status":status,"error_type":err,"payload_sha256":sha(raw) if raw else None},"integrity":{"in_window_rows":n,"finite_rows":finite,"finite_coverage":finite_cov,"duplicate_dates":dup,"malformed_dates":malformed,"date_manifest_sha256":sha(manifest)},"gates":gates,"decision":"PASS_DATA_ONLY" if passed else "FAIL_DATA_NO_ALPHA","numeric_values_exposed":False,"alpha_or_pnl_inspected":False,"validation":None,"final_holdout":None,"v16_used":False,"v99_used":False,"phase083_selection_use":False,"parameter_search":False,"rescue_allowed":False,"prereg_sha256":sha(PREREG.read_bytes())}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"phase":"126","decision":out["decision"],"integrity":out["integrity"],"gates":gates},sort_keys=True))
if __name__=="__main__": main()
