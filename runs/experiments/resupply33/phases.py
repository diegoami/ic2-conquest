"""Unmodified original-x86 phase control on immutable loaded-save records.

The supplied seed is an explicit control input, not a recovered legacy runtime
seed. No Wine/native phase observation is implied. No instructions are patched
or stubbed. Every attempt, including a blocked one, writes a fresh JSON file.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from unicorn import Uc, UcError, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_EIP, UC_X86_REG_ESP

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / 'patches')]
from state import sav
from battle_hook import sections

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--loaded', type=Path, required=True)
p.add_argument('--post', type=Path, required=True)
p.add_argument('--seed', type=int, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--all-phases', action='store_true')
p.add_argument('--runtime', type=Path)
a = p.parse_args()
base = ROOT.parent.parent / 'resupply31/wine-aboard/prefix/drive_c/IC2'
exe, dat = [(base / n).read_bytes() for n in
            ('Imperial Conquest 2 fast rollingsave seed.exe', 'Imperial Conquest 2.dat')]
assert hashlib.sha256(exe).hexdigest() == '354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
assert hashlib.sha256(dat).hexdigest() == '94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd'
b = a.loaded.read_bytes()
s = sav.parse(b)
assert s['turn_order'][s['seat_index'] + 1] == 0
assert s['current_nation'] == 13
u = Uc(UC_ARCH_X86, UC_MODE_32)
u.mem_map(0x400000, 0x300000)
u.mem_map(0x800000, 0x10000)
for _, va, vs, rp, rs, _ in sections(exe):
    if rs:
        u.mem_write(va, exe[rp:rp + rs])


def word(at, value):
    u.mem_write(at, struct.pack('<h', value))


def i16(at):
    return struct.unpack('<h', u.mem_read(at, 2))[0]


def i32(at):
    return struct.unpack('<i', u.mem_read(at, 4))[0]


u.mem_write(0x45e870, b[:sav.CITY_OFF])
u.mem_write(0x479590, b[sav.CITY_OFF:sav.ARMY_OFF])
na = sav.i16(b, sav.ARMY_OFF)
offset = sav.ARMY_OFF + 2
u.mem_write(0x47c1ec, b[offset:offset + na * 656])
offset += na * 656
nf = sav.i16(b, offset)
offset += 2
u.mem_write(0x49c26c, b[offset:offset + nf * 26])
offset += nf * 26
u.mem_write(0x474670, b[offset:offset + 16 * 1172])
offset += 16 * 1172
u.mem_write(0x49da10, b[offset:offset + 600])
offset += 600
news = sav.i16(b, offset)
offset += 2
u.mem_write(0x49f994, b[offset:offset + (news + 1) * 61])
word(0x4a031e, news)
word(0x4a0324, na)
word(0x4a0326, nf)
u.mem_write(0x49efe8, b[s['tail_off']:s['tail_off'] + 32])
u.mem_write(0x49f008, b[s['tail_off'] + 32:s['tail_off'] + 36])
word(0x4a0320, 0)  # The intervening Roman AI seat, not the loaded human seat.
word(0x4a0322, s['seat_index'] + 1)
word(0x4a0330, s['week'])
word(0x4a0332, s['year_bc'])
word(0x4a032e, s['season'])
u.mem_write(0x478fb0, dat[0x1f2f0:0x1f2f0 + 200])
u.mem_write(0x45e030, struct.pack('<I', a.seed & 0xffffffff))
if a.runtime:
    runtime = json.loads(a.runtime.read_text())
    assert runtime['seed'] == a.seed and runtime['current_nation'] == 13
    assert bytes.fromhex(runtime['runtime_tables'][0]['hex']) == dat[0x1f2f0:0x1f2f0 + 200]
    for row in runtime['runtime_tables']:
        u.mem_write(int(row['address'], 16), bytes.fromhex(row['hex']))


def state():
    return dict(treasuries=[i32(0x474aa8 + i * 1172) for i in range(16)],
                queues=[list(struct.unpack('<4h', u.mem_read(0x474954 + i * 8, 8))) for i in range(40)],
                mobilization=i16(0x474ab2),
                cities_sha256=hashlib.sha256(u.mem_read(0x479590, 334 * 34)).hexdigest(),
                armies=[dict(id=i, record=bytes(u.mem_read(0x47c1ec + i * 656, 656)).hex())
                        for i in range(na) if i16(0x47c1f0 + i * 656) >= 0],
                fleets=[dict(id=i, record=bytes(u.mem_read(0x49c26c + i * 26, 26)).hex())
                        for i in range(nf) if i16(0x49c274 + i * 26) >= 0],
                seed=struct.unpack('<I', u.mem_read(0x45e030, 4))[0])


events, writes, frames = [], [], []
names = {0x44fb7c: 'diplomacy', 0x44ffbc: 'recruitment',
         0x44f31c: 'army', 0x44f608: 'fleet', 0x4504f4: 'budget_recruit',
         0x4501f4: 'create_queue', 0x450768: 'fleet_build',
         0x450858: 'consolidate', 0x4509f0: 'army_merge', 0x450b30: 'fleet_merge'}


def code(uc, address, size, _):
    while frames and address == frames[-1]['return']:
        frame = frames.pop()
        events.append(dict(event='return', function=frame['function'], address=hex(address), state=state()))
    if address in names:
        frame = dict(function=names[address],
                     return_address=struct.unpack('<I', uc.mem_read(uc.reg_read(UC_X86_REG_ESP), 4))[0])
        frames.append(dict(function=frame['function'], **{'return': frame['return_address']}))
        events.append(dict(event='entry', function=frame['function'], address=hex(address),
                           eax=uc.reg_read(UC_X86_REG_EAX), edx=uc.reg_read(UC_X86_REG_EDX), state=state()))


def write(uc, access, address, size, value, _):
    if address in (0x474aa8 + i * 1172 for i in range(16)):
        assert size == 4
        value = (value + 2**31) % 2**32 - 2**31
        writes.append(dict(ip=hex(uc.reg_read(UC_X86_REG_EIP)), nation=(address - 0x474aa8) // 1172,
                           before=i32(address), after=value, debit=i32(address) - value,
                           frames=[x['function'] for x in frames], queues=state()['queues']))


u.hook_add(UC_HOOK_CODE, code)
u.hook_add(UC_HOOK_MEM_WRITE, write)
initial = state()
phases = [0x44fb7c, 0x44ffbc, 0x44f31c, 0x44f608] if a.all_phases else [0x44ffbc]
results, error = [], None
for phase in phases:
    before = state()
    try:
        u.mem_write(0x80f000, struct.pack('<I', 0x600000))
        u.reg_write(UC_X86_REG_ESP, 0x80f000)
        u.emu_start(phase, 0x600000, count=2000000)
        assert u.reg_read(UC_X86_REG_EIP) == 0x600000
        assert u.reg_read(UC_X86_REG_ESP) == 0x80f004
        assert len(frames) == 1 and frames[0]['function'] == names[phase]
        frames.pop()
        results.append(dict(phase=names[phase], before=before, after=state()))
    except Exception as exc:
        error = dict(phase=names[phase], exception=repr(exc), ip=hex(u.reg_read(UC_X86_REG_EIP)))
        break
post_bytes = a.post.read_bytes()
post_state = sav.parse(post_bytes)
actual = post_state['nations'][0]
post_na = sav.i16(post_bytes, sav.ARMY_OFF)
post_army_start = sav.ARMY_OFF + 2
post_fleet_count = post_army_start + post_na * 656
post_nf = sav.i16(post_bytes, post_fleet_count)
post_fleet_start = post_fleet_count + 2
post_nation_start = post_fleet_start + post_nf * 26
post_live_armies = [post_bytes[post_army_start+i*656:post_army_start+(i+1)*656].hex() for i in range(post_na) if sav.i16(post_bytes,post_army_start+i*656+4)>=0]
post_live_fleets = [post_bytes[post_fleet_start+i*26:post_fleet_start+(i+1)*26].hex() for i in range(post_nf) if sav.i16(post_bytes,post_fleet_start+i*26+8)>=0]
final = state()
actual_queues = [[x['state'], sav.UNIT_TYPES.index(x['type']), x['troops'], x['city']]
                 for x in actual['recruit_slots']]
live = [x for x in final['queues'] if x[2] > 0]
record = dict(provenance='Original-x86 phase control, not observed legacy runtime seed or Wine phase trace.',
              supplied_seed=a.seed, runtime=str(a.runtime) if a.runtime else None,
              runtime_sha256=hashlib.sha256(a.runtime.read_bytes()).hexdigest() if a.runtime else None,
              loaded=a.loaded.name, loaded_sha256=hashlib.sha256(b).hexdigest(),
              runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              initial=initial, final=final, phases=results, events=events, writes=writes, error=error,
              post_comparison=dict(queues_match=live == actual_queues,
                                   treasury_match=final['treasuries'][0] == actual['treasury'],
                                   mobilization_match=final['mobilization'] == actual['mobilization'],
                                   all_nation_bytes_match=bytes(u.mem_read(0x474670,16*1172)) == post_bytes[post_nation_start:post_nation_start+16*1172],
                                   nation_byte_differences=[dict(nation=i//1172,offset=hex(i%1172),x86=x,wine=y) for i,(x,y) in enumerate(zip(bytes(u.mem_read(0x474670,16*1172)),post_bytes[post_nation_start:post_nation_start+16*1172])) if x!=y],
                                   all_city_bytes_match=bytes(u.mem_read(0x479590,334*34)) == post_bytes[sav.CITY_OFF:sav.ARMY_OFF],
                                   all_live_army_bytes_match=[x['record'] for x in final['armies']] == post_live_armies,
                                   all_live_fleet_bytes_match=[x['record'] for x in final['fleets']] == post_live_fleets))
with a.output.open('x') as out:
    json.dump(record, out, indent=2)
    out.write('\n')
print(json.dumps(dict(error=error, comparison=record['post_comparison'], writes=len(writes))))
