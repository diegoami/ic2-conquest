"""Read-only local gates at retained phase inputs; no invented RNG alignment."""
from original_support import *
rows=json.loads((DATA/'phase-replay-v1.json').read_text())
for row in rows:
 index=row['index'];raw=(BASE/'live/ST-rom-hook-v1/snapshots'/f'{index:03}.ram').read_bytes()
 if row['phase']=='diplomacy':row['original_facts']=diplomacy_facts(raw)
 if row['phase']=='economy':
  u,after,trace=execute(raw,0x44ffbc,stop=(0x45011e,));assert after==raw;row['power']=trace['power']
write(DATA/'phase-facts-v1.json',rows);print('Preserved original diplomacy local gates and economy own/threat at all captured phase entries')
