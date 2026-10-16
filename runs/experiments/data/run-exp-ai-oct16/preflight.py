"""Load an unchanged fixture in private Wine and record runtime region tables."""
import struct
from probe_common import *
from harness import decompile

decompile.check()
src = ROOT / 'saves/fleet-port-antium-0734.SAV'
g = PrivateGame(log=lambda line: log('driver', message=line))
try:
    log('preflight', source=str(src), sha256=sha(src), exe=g.exe,
        exe_sha256=sha(drv.G / g.exe), work=str(drv.WORK), display=drv.DISPLAY,
        decompile_sha256=sha(decompile.DUMP))
    g.load(src, seed=12345)
    snap = snapshot(g)
    boxes = struct.unpack('<32h', g.mem(0x4794E8, 64))
    coasts = struct.unpack('<12h', g.mem(0x479528, 24))
    log('runtime_tables', turn=g.turn_number(), save=src.name, region_boxes=[boxes[i:i+4] for i in range(0,32,4)],
        coast_pairs=[coasts[i:i+2] for i in range(0,12,2)], snapshot=snap)
finally:
    g.kill()
