from __future__ import annotations
import subprocess,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
CFG='v98_independent_phase076_validation_data.json'
def run(*args:str)->None: subprocess.run([sys.executable,*args],cwd=PROJECT,check=True)
def main()->None:
 run('scripts/download_futures_archive.py','--config',CFG,'--workers','40')
 run('scripts/build_canonical.py','--config',CFG)
if __name__=='__main__': main()
