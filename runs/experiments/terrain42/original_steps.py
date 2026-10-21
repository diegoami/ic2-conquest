#!/usr/bin/env python3
"""Bounded original-instruction controls, never launches the game or writes inputs.

Two presentation calls are intercepted: map redraw and sound. No movement,
terrain, distance, or selection helper is replaced. Synthetic controls are
not original gameplay; full walks replay existing save records in memory only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_EIP


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe', type=Path, required=True)
    ap.add_argument('--dat', type=Path, required=True)
    ap.add_argument('--save', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise SystemExit('output already exists; choose a new name')
    exe, dat, save = (p.read_bytes() for p in (a.exe, a.dat, a.save))
    assert sha(exe) == '9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31'
    pe = struct.unpack_from('<I', exe, 0x3c)[0]
    n, opt = struct.unpack_from('<H', exe, pe + 6)[0], struct.unpack_from('<H', exe, pe + 20)[0]
    ib = struct.unpack_from('<I', exe, pe + 24 + 28)[0]
    secs = []
    for k in range(n):
        off = pe + 24 + opt + 40 * k
        vs, va, rs, rp = struct.unpack_from('<4I', exe, off + 8)
        secs.append((ib + va, rp, rs))
    terrain = dat[0x1f622:0x1f622 + 12 * 14]
    costs = [struct.unpack_from('<h', terrain, 14 * k + 12)[0] for k in range(12)]
    assert costs == [1, 3, 1, 1, 2, 4, 4, 4, 4, 4, 4, 4], costs
    out = {'exe_sha256': sha(exe), 'dat_sha256': sha(dat), 'save_sha256': sha(save),
           'runner_sha256': sha(Path(__file__).read_bytes()), 'terrain_costs': costs,
           'evidence': 'Unicorn original instructions; presentation redraw/sound intercepted; no native/Wine run',
           'controls': [], 'walks': []}

    def run(fleet=False, walk=False, human=False, start=(10, 10), cursor=(10, 9),
            goal=(10, 5), moves=8, sx=0, sy=-1, ymajor=1, cells=None, expected=None):
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(0x400000, 0x300000)
        u.mem_map(0x800000, 0x10000)
        for va, rp, rs in secs:
            if rs:
                u.mem_write(va, exe[rp:rp + rs])
        u.mem_write(0x4792e4, terrain)
        # An isolated all-land/all-sea map for single-step controls only.
        u.mem_write(0x45e870, struct.pack('<h', 0 if fleet else 2) * (320 * 140))
        u.mem_write(0x4a0320, struct.pack('<h', 0))
        u.mem_write(0x474b00, bytes([int(human)]))
        unit = 0x49c26c if fleet else 0x47c1ec
        mo, co = (12, 24) if fleet else (6, 8)
        if walk:
            # Exact source save map and army0 record, not a derived terrain map.
            u.mem_write(0x45e870, save[:89600])
            u.mem_write(unit, save[100958:100958 + 656])
            start = struct.unpack_from('<2h', save, 100958)
        else:
            u.mem_write(unit, bytes(26 if fleet else 656))
            u.mem_write(unit, struct.pack('<2h', *start))
            u.mem_write(unit + co, struct.pack('<h', 0 if fleet else 2))
            if fleet:
                u.mem_write(unit + 22, struct.pack('<h', -1))
        u.mem_write(unit + mo, struct.pack('<h', moves))
        if not walk:
            u.mem_write(0x45e870 + 2 * (start[0] * 140 + start[1]), struct.pack('<h', 300 if fleet else 200))
        for (x, y), code in (cells or {}).items():
            u.mem_write(0x45e870 + 2 * (x * 140 + y), struct.pack('<h', code))
        events, ui = [], []
        def i16(addr):
            return struct.unpack('<h', u.mem_read(addr, 2))[0]
        def state():
            return [i16(unit), i16(unit + 2), i16(unit + mo)]
        def hook(uc, addr, size, data):
            if addr in (0x445b38, 0x45bf28):
                ui.append(hex(addr))
                esp = uc.reg_read(UC_X86_REG_ESP)
                ret = struct.unpack('<I', uc.mem_read(esp, 4))[0]
                uc.reg_write(UC_X86_REG_ESP, esp + 4)
                uc.reg_write(UC_X86_REG_EIP, ret)
            if addr == (0x44dd70 if fleet else 0x44d420):
                events.append({'before': state()})
        u.hook_add(UC_HOOK_CODE, hook)
        # Observe actual coordinate stores; a path is not inferred from endpoint totals.
        stores = []
        def write(uc, access, addr, size, value, data):
            if addr in (unit, unit + 2):
                stores.append({'instruction': hex(uc.reg_read(UC_X86_REG_EIP)),
                               'field': 'x' if addr == unit else 'y', 'value': value & 65535})
        u.hook_add(UC_HOOK_MEM_WRITE, write)
        esp, frame = 0x80f000, 0x80e000
        u.mem_write(esp, struct.pack('<2I', 0x600000, frame))
        if not walk:
            for off, v in [(-2, cursor[0]), (-4, cursor[1]), (-6, 0), (-10, goal[0]),
                           (-8, goal[1]), (-12, sx), (-14, sy), (-16, ymajor), (-18, 0), (-20, 1)]:
                u.mem_write(frame + off, struct.pack('<h', v))
        u.reg_write(UC_X86_REG_ESP, esp)
        u.reg_write(UC_X86_REG_EAX, 0)
        u.reg_write(UC_X86_REG_EDX, goal[0] | (goal[1] << 16))
        entry = 0x44d734 if walk else (0x44dd70 if fleet else 0x44d420)
        before = state()
        u.emu_start(entry, 0x600000, count=300000)
        assert u.reg_read(UC_X86_REG_EIP) == 0x600000, hex(u.reg_read(UC_X86_REG_EIP))
        after = state()
        if expected is not None:
            assert after == list(expected), (before, after, expected)
        return {'before': before, 'after': after, 'coordinate_stores': stores,
                'step_entries': events, 'presentation_calls': ui,
                'human': human, 'fleet': fleet, 'goal': list(goal)}

    cases = [
        ('equal_laterals_first_east', {'cells': {(10, 9): 4}, 'expected': (11, 9, 7)}),
        ('all_equal_keep_line', {'expected': (10, 9, 7)}),
        ('west_strictly_cheaper', {'cells': {(10, 9): 5, (11, 9): 4}, 'expected': (9, 9, 7)}),
        ('east_marker_blocked', {'cells': {(10, 9): 4, (11, 9): 206}, 'expected': (9, 9, 7)}),
        ('terminal_no_detour', {'goal': (10, 9), 'cells': {(10, 9): 4}, 'expected': (10, 9, 6)}),
        ('human_unaffordable_preserves', {'human': True, 'moves': 3, 'cells': {(10, 9): 5, (11, 9): 5, (9, 9): 5}, 'expected': (10, 10, 3)}),
        ('ai_unaffordable_zeroes', {'moves': 3, 'cells': {(10, 9): 5, (11, 9): 5, (9, 9): 5}, 'expected': (10, 10, 0)}),
        ('diagonal_xmajor_first_x', {'cursor': (11, 11), 'goal': (15, 13), 'sx': 1, 'sy': 1, 'ymajor': 0, 'cells': {(11, 11): 4}, 'expected': (11, 10, 7)}),
        ('diagonal_ymajor_first_y', {'cursor': (11, 11), 'goal': (13, 15), 'sx': 1, 'sy': 1, 'ymajor': 1, 'cells': {(11, 11): 4}, 'expected': (10, 11, 7)}),
        ('fleet_rough_to_calm_lateral', {'fleet': True, 'cells': {(10, 9): 1}, 'expected': (11, 9, 7)}),
        ('fleet_terminal_rough_cost3', {'fleet': True, 'goal': (10, 9), 'cells': {(10, 9): 1}, 'expected': (10, 9, 5)}),
    ]
    for name, kwargs in cases:
        out['controls'].append({'name': name, **run(**kwargs)})
    for name, goal, expected in [('far12', (100, 25), (100, 29, 0)),
                                 ('near5', (100, 32), (100, 32, 3))]:
        out['walks'].append({'name': name, **run(walk=True, human=True, moves=8, goal=goal, expected=expected)})
    with a.output.open('x') as f:
        json.dump(out, f, indent=2)
        f.write('\n')
    print(f'{len(out["controls"])} step controls, {len(out["walks"])} source-save walks passed; {a.output}')


if __name__ == '__main__':
    main()
