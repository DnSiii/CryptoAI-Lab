"""Phase195-T synthetic append-only classifier controls."""
import importlib.util
from pathlib import Path
sp=importlib.util.spec_from_file_location("t",Path(__file__).resolve().parents[1]/"tools"/"v99_phase195t_paper_replay_forensics.py")
t=importlib.util.module_from_spec(sp);sp.loader.exec_module(t)
def row(time,value):return {"timestamp":time,"capital_brl":value}
def ledger(values):
 return {"mode":"PAPER_ONLY","candidate":"frozen","base_capital_brl":10000,"paper_start_after_timestamp":"t0","latest_data_timestamp":"t1","equity_curve":[row("t0",values[0]),row("t1",values[1])],"decisions":[]}
def main():
 old=ledger([100,110]);new=ledger([100,110]);new["equity_curve"].append(row("t2",115))
 assert t.compare(old,new,"x")["decision"]=="APPEND_ONLY_PREFIX_MATCH"
 new=ledger([100,111]);new["equity_curve"].append(row("t2",115))
 r=t.compare(old,new,"x");assert r["decision"]=="HOLD_LAST_PUBLISHED_HOUR_MUTATED" and not r["publication_authorized"]
 new=ledger([99,110]);assert t.compare(old,new,"x")["decision"]=="HOLD_EARLIER_PUBLISHED_HISTORY_MUTATED"
 new=ledger([100,110]);new["equity_curve"].pop()
 assert t.compare(old,new,"x")["decision"]=="HOLD_EARLIER_PUBLISHED_HISTORY_MUTATED"
 new=ledger([100,110]);new["candidate"]="changed"
 assert t.compare(old,new,"x")["decision"]=="HOLD_BOUNDARY_CHANGED"
 new=ledger([100,110]);new["decisions"]=[row("t1",12)]
 assert t.compare(old,new,"x")["decision"]=="APPEND_ONLY_PREFIX_MATCH"
 new=ledger([100,110]);new["equity_curve"][1]["timestamp"]="t1b"
 assert t.compare(old,new,"x")["decision"]=="HOLD_EARLIER_PUBLISHED_HISTORY_MUTATED"
 print("PASS Phase195-T 7 adversarial controls")
if __name__=="__main__":main()
