"""V98 Phase264 CFTC positioning DATA_ONLY invariants."""
import csv,datetime as dt,importlib.util,io,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p264",ROOT/"research/v98_independent/phase264_cftc_btc_positioning.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def make_zip(rows,year=2023):
    fields=["Market and Exchange Names","As of Date in Form YYMMDD","CFTC Contract Market Code",
      "Open Interest (All)","Noncommercial Positions-Long (All)","Noncommercial Positions-Short (All)",
      "Noncommercial Positions-Spreading (All)","Commercial Positions-Long (All)","Commercial Positions-Short (All)",
      "Nonreportable Positions-Long (All)","Nonreportable Positions-Short (All)"]
    s=io.StringIO(newline="");w=csv.DictWriter(s,fieldnames=fields,lineterminator="\n");w.writeheader()
    for r in rows:w.writerow(r)
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:z.writestr("annual.txt",s.getvalue())
    return b.getvalue()

def btc_row(date="230103",code="133741"):
    return {"Market and Exchange Names":"BITCOIN - CHICAGO MERCANTILE EXCHANGE","As of Date in Form YYMMDD":date,
      "CFTC Contract Market Code":code,"Open Interest (All)":"1000","Noncommercial Positions-Long (All)":"500",
      "Noncommercial Positions-Short (All)":"400","Noncommercial Positions-Spreading (All)":"100",
      "Commercial Positions-Long (All)":"50","Commercial Positions-Short (All)":"500",
      "Nonreportable Positions-Long (All)":"350","Nonreportable Positions-Short (All)":"100"}

def test_urls_and_contract_frozen():
    assert P.CONTRACT_CODE=="133741"
    assert P.URLS[2023].endswith("/deacot2023.zip") and P.URLS[2025].endswith("/deacot2025.zip")

def test_parse_filters_contract():
    rows=[btc_row(),btc_row(code="999999")]
    out,member,member_sha,invalid=P.parse_zip(make_zip(rows),2023)
    assert len(out)==1 and out[0]["contract_code"]=="133741" and member=="annual.txt" and member_sha and invalid==0

def test_wrong_year_bitcoin_row_is_invalid():
    out,_,_,invalid=P.parse_zip(make_zip([btc_row("240103")]),2023)
    assert out==[] and invalid==1

def test_multiple_text_members_rejected():
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("a.txt","x");z.writestr("b.csv","x")
    try:P.parse_zip(b.getvalue(),2023)
    except ValueError:pass
    else:raise AssertionError("multiple members must fail")

def test_csv_deterministic():
    r={**btc_row(),"report_date":"2023-01-03","market_name":"BITCOIN - CHICAGO MERCANTILE EXCHANGE",
       "contract_code":"133741","open_interest":1000,"noncommercial_long":500,"noncommercial_short":400,
       "noncommercial_spreading":100,"commercial_long":50,"commercial_short":500,
       "nonreportable_long":350,"nonreportable_short":100}
    for k in list(r):
        if k not in ["report_date","market_name","contract_code",*P.NUMERIC_FIELDS.keys()]:r.pop(k,None)
    assert P.csv_bytes([r])==P.csv_bytes([r])

def test_data_only_firewall():
    text=(ROOT/"research/v98_independent/phase264_cftc_btc_positioning.py").read_text().lower()
    assert "exact_fast" not in text and "cryptoai_v13" not in text and "phase252" not in text
    assert '"pnl_executed":false' in text.replace(" ","")
    assert "research/v99" not in text and "paper_v99" not in text
