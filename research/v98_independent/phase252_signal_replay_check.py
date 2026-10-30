"""V98-only compatibility entrypoint for immutable Phase252 target, Phase671."""
from phase671_phase252_signal_replay_check import reconstruct,native_hourly,INDEX,ASSETS,FROZEN_SHA

def __getattr__(name):
    if name=='target':return reconstruct(native_hourly())
    raise AttributeError(name)
