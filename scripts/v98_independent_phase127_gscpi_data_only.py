#!/usr/bin/env python3
"""V98 Independent Phase127: GSCPI DATA_ONLY feasibility. Never emits numeric series values."""
from __future__ import annotations
import csv, hashlib, io, json, math, urllib.request
from datetime import date
from pathlib import Path

URL = "https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.csv"
START, END = date(2023,1,1), date(2025,12,31)
OUT = Path("reports/v98_independent_phase127_gscpi_data_only.json")
PREREG = Path("reports/v98_independent_phase127_gscpi_data_only_prereg.md")

def sha(b: bytes)->str: return hashlib.sha256(b).hexdigest()

def main():
    req=urllib.request.Request(URL, headers={"User-Agent":"CryptoAI-Lab-V98/phase127"})
    status=None; raw=b""; err=None
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status=r.status; raw=r.read()
    except Exception as e: err=type(e).__name__
    required=False; rows=[]; malformed=0; finite=0
    if status==200 and raw:
        try:
            reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            fields=reader.fieldnames or []
            date_col=next((c for c in fields if c.strip().lower() in {"date","month"}),None)
            value_col=next((c for c in fields if "gscpi" in c.strip().lower()),None)
            required=bool(date_col and value_col)
            if required:
                for x in reader:
                    try:
                        s=x[date_col].strip(); d=None
                        for fmt in ("%Y-%m-%d","%m/%d/%Y","%Y-%m","%b-%y","%b %Y"):
                            try:
                                from datetime import datetime
                                d=datetime.strptime(s,fmt).date(); break
                            except ValueError: pass
                        if d is None: raise ValueError
                    except Exception: malformed+=1; continue
                    if START<=d<=END:
                        try: ok=math.isfinite(float(x.get(value_col,"")))
                        except Exception: ok=False
                        finite += int(ok); rows.append(d)
        except Exception as e: err=type(e).__name__
    dates=sorted(rows); dup=len(dates)-len(set(dates)); n=len(dates)
    increasing=all(a<b for a,b in zip(dates,dates[1:])); finite_cov=(finite/n) if n else 0.0
    manifest=("\n".join(d.isoformat() for d in dates)+("\n" if dates else "")).encode()
    gates={"http_200":status==200,"required_columns":required,"rows_gte_34":n>=34,"finite_coverage_gte_95pct":finite_cov>=.95,"zero_duplicate_dates":dup==0,"strictly_increasing":increasing,"zero_malformed_dates":malformed==0}
    passed=all(gates.values())
    out={"engine":"V98 Independent","phase":"127","mode":"DATA_ONLY","family":"NY Fed Global Supply Chain Pressure Index","window":{"start":str(START),"end":str(END)},"source":{"official_url":URL,"http_status":status,"error_type":err,"payload_sha256":sha(raw) if raw else None},"integrity":{"in_window_rows":n,"finite_rows":finite,"finite_coverage":finite_cov,"duplicate_dates":dup,"malformed_dates":malformed,"date_manifest_sha256":sha(manifest)},"gates":gates,"decision":"PASS_DATA_ONLY" if passed else "FAIL_DATA_NO_ALPHA","numeric_values_exposed":False,"alpha_or_pnl_inspected":False,"validation":None,"final_holdout":None,"v16_used":False,"v99_used":False,"phase083_selection_use":False,"parameter_search":False,"rescue_allowed":False,"prereg_sha256":sha(PREREG.read_bytes())}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"phase":"127","decision":out["decision"],"integrity":out["integrity"],"gates":gates},sort_keys=True))
if __name__=="__main__": main()
