"""G1 reconstruct 1H historical expired futures from original OKX trade tapes.

No signals, no strategy, no PnL. Source: read-only archived original daily
FUTURES-chain trades from Actions 40047386032. This bypasses the proven
2022-03 candle-archive contract-label mismatch without fabricating prices.
"""
from __future__ import annotations
import csv,hashlib,io,json,sys,zipfile
from collections import defaultdict
from decimal import Decimal,InvalidOperation
from pathlib import Path

DAY_START=1647705600000  # 2022-03-19 16:00 UTC, venue UTC+8 daily boundary
DAY_END=DAY_START+86400000
HOUR=3600000

def main(source,outdir):
    source,out=Path(source),Path(outdir)
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((source/"trade_tape_probe.json").read_text())
    summaries=[]
    for rec in manifest["records"]:
        if rec["status"]!="TARGET_TRADE_ROWS_PRESENT":raise ValueError("MISSING_ORIGINAL_FUTURES_TRADE_SOURCE")
        archive=(source/rec["archive_file"]).read_bytes()
        if hashlib.sha256(archive).hexdigest()!=rec["archive_sha256"]:
            raise ValueError("ORIGINAL_TRADE_TAPE_HASH_MISMATCH")
        trades=[]
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            for member in z.infolist():
                if not member.filename.lower().endswith(".csv"):continue
                with z.open(member) as f:
                    reader=csv.DictReader(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""))
                    if not {"instrument_name","trade_id","price","size","created_time"}<=set(reader.fieldnames or []):
                        raise ValueError("ORIGINAL_TRADE_SCHEMA_MISMATCH")
                    for row in reader:
                        if row["instrument_name"]!=rec["target"]:continue
                        ts=int(row["created_time"])
                        if not DAY_START<=ts<DAY_END:raise ValueError("ORIGINAL_TRADE_OUTSIDE_FIXED_DAY")
                        price=Decimal(row["price"]);size=Decimal(row["size"])
                        if not price.is_finite() or price<=0 or not size.is_finite() or size<=0:
                            raise ValueError("NONPOSITIVE_ORIGINAL_TRADE")
                        trades.append((ts,int(row["trade_id"]),price,size))
        if len(trades)!=rec["target_line_count"]:raise ValueError("TRADE_TAPE_COUNT_MISMATCH")
        trades.sort(key=lambda x:(x[0],x[1]))
        ids=set();by_hour=defaultdict(list)
        for ts,trade_id,price,size in trades:
            if trade_id in ids:raise ValueError("DUPLICATE_ORIGINAL_TRADE_ID")
            ids.add(trade_id);by_hour[(ts//HOUR)*HOUR].append((price,size))
        bars=[]
        for t in range(DAY_START,DAY_END,HOUR):
            rows=by_hour.get(t,[])
            if not rows:raise ValueError("MISSING_HOUR_IN_ORIGINAL_TRADE_TAPE")
            px=[p for p,s in rows]
            bars.append({"hour_ms":t,"open":str(px[0]),"high":str(max(px)),
                         "low":str(min(px)),"close":str(px[-1]),
                         "trade_count":len(rows),"volume_contracts":str(sum((s for p,s in rows),Decimal(0)))})
        path=out/(rec["target"]+"_1h.json")
        path.write_text(json.dumps(bars,sort_keys=True,separators=(",",":"))+"\n")
        summaries.append({"instrument":rec["target"],"hours":len(bars),
                          "original_trades":len(trades),
                          "derived_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    result={"schema":"G1_ORIGINAL_2022_TRADE_TO_HOURLY_RECONSTRUCTION_V1",
            "status":"SOURCE_ONLY_HOURLY_RECONSTRUCTION_NOT_ECONOMICS",
            "sources":summaries,"full_train_verified":False,
            "economic_train_executed":False,"roi_computed":False,
            "validation_opened":False,"holdout_opened":False,
            "orders_enabled":False,"promotion_authorized":False}
    (out/"reconstruction.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: python -m research.tools.v99_r106_g1_trade_to_hourly ORIGINAL_TAPES OUT")
    main(sys.argv[1],sys.argv[2])
