"""The Information window's panels as the decompile writes them: an executable model of TInformation_Show* (0x0043ba7c..0x0043cf0c).

Every function cites the decompile line range in /mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt
(`F:<line>`; TInformation_ShowNationStatus starts at line 40802). The word tables are NOT in the exe: they are BSS filled from
`Imperial Conquest 2.DAT` by FUN_004481a0 (ReTools/scratch/datload.txt), sequentially; `MEM` rebuilds that memory image from the DAT (the
read order and sizes are those of the loader, so DAT offsets are derived, not searched: DAT_0047938c <- 0x1F6CA is the cumulative sum).
Unfilled bytes are zero (BSS), which is what the game reads when an index runs past a table.

Panel text is returned as (caption, value) pairs: TInformation_PaintForm splits every line at its FIRST '-' (F:40... see PAINT note) and draws
the left part at x and the right part at x+100; a line without '-' is one left-hand string."""
import os, struct, math
from state import sav

DAT = os.environ.get('IC2_DAT', '/home/diego/ic2-work/prefix/drive_c/IC2/Imperial Conquest 2.dat')
# FUN_004481a0: (memory address, byte count) in read order after the map (0x15e00), cities (0x2c5c), 15 armies (0x290), 2 fleets (0x1a), 16 nations
LOADER = [(0x478fb0, 200), (0x479078, 0x28), (0x4790a0, 10), (0x4790ac, 0xe8), (0x479194, 0x150), (0x4792e4, 0xa8), (0x47938c, 0x6e),
          (0x4793fc, 0x6e), (0x47946c, 0x32), (0x4794a0, 0x28), (0x4794c8, 0x1e), (0x4794e8, 0x40), (0x479528, 0x18), (0x479540, 0x50),
          (0x49cc94, 0x410), (0x49d0a4, 0xbc4), (0x49dc68, 0x1380), (0x49f994, 0x988)]
NATION_READS = 0xb + 0x20 + 2 + 0x29c + 0x140 + 4 + 4 + 2 * 7
DAT_START = 0x15e00 + 0x2c5c + 15 * 0x290 + 2 * 0x1a + 16 * NATION_READS      # = 0x1F2F0

def build_mem(path=DAT):
    d = open(path, 'rb').read()
    mem, off = {}, DAT_START
    tables = {}
    for addr, n in LOADER:
        tables[addr] = (off, n)
        for k in range(n): mem[addr + k] = d[off + k]
        off += n
    return mem, tables
MEM, TABLES = build_mem()
def cstr(addr, limit=60):
    out = bytearray()
    for k in range(limit):
        b = MEM.get(addr + k, 0)
        if b == 0: break
        out.append(b)
    return out.decode('latin1')
def i16m(addr):
    return struct.unpack('<h', bytes(MEM.get(addr + k, 0) for k in range(2)))[0]
def cdiv(a, b):             # C / Delphi div: truncate toward zero
    q = abs(a) // abs(b); return q if (a < 0) == (b < 0) else -q
def sar(a, n): return a >> n    # Python's >> on negative ints is arithmetic, like SAR
def i16(v): v &= 0xffff; return v - 0x10000 if v >= 0x8000 else v
def i32(v): v &= 0xffffffff; return v - (1 << 32) if v >= (1 << 31) else v

# ---- word bands (the tables are 11-byte strings; the index expression is the code's) -------------------------------------------------
def quality_word(q): return cstr(0x47938c + q * 11)                 # F:41257, 41302: DAT_0047938c + q*0xb
def unity_word(u): return cstr(0x4793fc + cdiv(u, 100) * 11)        # F:40830: DAT_004793fc + ((int)(short)unity / 100) * 0xb
def loyalty_word(l): return cstr(0x4793fc + cdiv(l, 10) * 11)       # F:40926: same table, loyalty / 10
def morale_word(m):                                                  # F:41052-41058
    i = m - 0x33
    if i < 0: i = m - 0x30
    return cstr(0x479428 + sar(i, 2) * 11)
def relation_word(v): return cstr(0x4794c8 + v * 6) if v > 0 else ''  # F:40871 (guarded by 0 < value)
def tribute_word(u):                                                 # F:40961-40977; u is the unsigned 16-bit field; None = no branch taken
    u &= 0xffff
    if u < 0xb: return 'poor'
    if (u - 0xb) & 0xffff < 0x14: return 'moderate'
    if (u - 0x1f) & 0xffff < 0x46: return 'rich'
    if (u - 0x65) & 0xffff < 0x26ac: return 'very rich'
    return None
def terrain_name(c): return cstr(0x4792e4 + c * 14)
def unit_name(t): return cstr(0x478fb0 + t * 0x28)
def quarterly_price(t): return i16m(0x478fd4 + t * 0x28)             # DAT_00478fd4 + type*0x28 (record +0x24 of the unit-type table)

# ---- number formatters ----------------------------------------------------------------------------------------------------------------
def f_plain(v): return str(v)                  # FUN_004028c4 + FUN_00402978: Str(v) as written, no separators
def f_commas(v): return ('- ' if v < 0 else '') + '{:,}'.format(abs(v))   # FUN_00448f3c copies from index 1 for a negative: the '-' (index 1), a blank (index 2), then the digits: '- 1,500'
def f_pop(v): return '{:,}'.format(abs(v)).ljust(12)   # FUN_00448f9c: copies from index 3, so a negative's sign is dropped; 12-char field (trailing blanks)

NAMES = sav.NATIONS
def nation_panel(s, n, cur):
    nt = s['nations'][n]
    L = [('Nation ', nt['name']), ('Leader ', nt['leader']), ('Capital ', s['cities'][nt['capital']]['name']),
         ('Cities ', f_plain(nt['cities_count'])), ('Population ', f_pop(nt['wealth'])), ('Unity ', unity_word(nt['unity'])),
         ('Tax rate ', f_plain(nt['tax']) + '%')]
    if n == cur:
        L += [('Mobilized ', f_plain(nt['mobilization']) + '%'), ('Treasury ', f_commas(nt['treasury']) + ' talents')]
    L += [('', ''), ('', '      INTERNATIONAL RELATIONS')]
    for m, mt in enumerate(s['nations']):
        if mt['unity'] == 0:
            L.append(('', '   ( %s conquerred by %s )' % (mt['name'], s['nations'][mt['conquered_by']]['name'])))
        elif m == n: L.append(('', ''))
        else:
            rel = list(nt['relations'].values()); rel = [nt['relations'].get(NAMES[j], 0) for j in range(16)]
            L.append((mt['name'] + '  ', relation_word(rel[m])))
    return L
def city_panel(s, cid, cur):
    c = s['cities'][cid]; own = c['owner']
    capital = any(nt['capital'] == cid for nt in s['nations'])
    L = [('City ', c['name'] + ('  (capital of %s)' % NAMES[own] if capital else '')), ('Controlled by ', NAMES[own]),
         ('Allegiance to ', NAMES[c['allegiance']]),
         ('Population ', f_pop(c['pop'] * 1000) + '(%d%%)' % cdiv(c['pop'] * 100, c['max_pop'])), ('Loyalty ', loyalty_word(c['loyalty']))]
    fv = c['fort'] if c['fort_pending'] == 0 else c['fort_pending'] * 100 + c['fort']      # sav.py splits the raw field; F:40940 branches on the raw field
    v = ('%d%%' % fv) if fv < 0x65 else ('%d%%  (under construction)' % (fv % 100))
    br = sum(sl['troops'] for sl in s['nations'][own]['recruit_slots'] if sl['city'] == cid)
    if br > 0: v += '   (%s)' % f_commas(br)
    L.append(('Fortification ', v))
    tr = cdiv(c['tribute'] * c['pop'], c['max_pop']); tr = i16(tr)
    if own == cur: L.append(('Tribute ', '%d  talents' % tr))
    else:
        w = tribute_word(c['tribute'])
        L.append(('Tribute ', w if w is not None else f_plain(tr)))
    L.append(('Supply ', '%d  tons' % c['supplies']) if own == cur else ('', ' '))
    return L

def raw_army(b, i):
    """The 20 unit slots of army i from the save bytes: (label, type, troops, quality, name), troops <= 0 kept (the panel's sums read all 20)."""
    from stage import Save
    return None
class Raw:
    """Raw save access for the model (the parsed dicts drop empty slots)."""
    def __init__(self, path):
        from stage import Save
        self.s = Save(path); self.b = self.s.b; self.p = sav.parse(bytes(self.b))
    def army_hdr(self, i):
        return struct.unpack_from('<8h', self.b, self.s.army0 + i * sav.ARMY_LEN)
    def slots(self, i):
        o = self.s.army0 + i * sav.ARMY_LEN + 16
        return [struct.unpack_from('<4h', self.b, o + 32 * k) + (sav.cstr(self.b[o + 32 * k + 8:o + 32 * k + 32]),) for k in range(20)]
    def merc_rows(self):
        return [struct.unpack_from('<6h', self.b, self.s.merc0 + 12 * k) for k in range(50)]
    def merc_names(self):
        return None

def army_lines(raw, i, cur, fleet_shift=False):
    """ShowArmyDetails F:41000-41134. Returns the list of (caption, value) lines 0.. (line index = position)."""
    x, y, owner, moves, cell, sup, money, morale = raw.army_hdr(i)
    sl = raw.slots(i)
    own = owner == cur
    counts = [0] * 5
    reg = merc = 0
    for lab, typ, tr, q, nm in sl:
        counts[typ] += tr
        sv = i16(cdiv(tr, 200) * quarterly_price(typ))        # sVar4 is a 16-bit short
        if lab == 0: reg += sv
        else: merc += cdiv(sv * q, 5)
    total = sum(t for _, _, t, _, _ in sl) or 1
    nunits = 0
    for k, (_, _, tr, _, _) in enumerate(sl):
        if tr > 0: nunits = k + 1
    L = [('Army of ', NAMES[owner]),
         ('Moves ', f_plain(moves) if own else ''),
         ('Supply ', ('%s tons  (%s%%)' % (f_plain(sup), f_plain(cdiv(sup * 10000, total)))) if own else ''),
         ('Morale ', morale_word(morale) if own else ''),
         ('Money ', ('%s talents' % f_plain(money)) if own else '')]
    if cell >= 0: L.append(('Terrain ', terrain_name(cell)))
    L.append(('', '  '))
    for t in range(5): L.append((unit_name(t), f_pop(counts[t])))
    L.append(('Total troops ', f_pop(total)))
    if own:
        L += [('No. of units', f_plain(nunits)), ('', '  '), ('Regulars cost', '%s  talents per quarter' % f_plain(reg)),
              ('Mercenary pay', '%s  talents per quarter' % f_plain(merc))]
    return L
def army_units_list(raw, i, cur):
    """ShowArmyUnits F:41276-41312: only for the current nation's army; stops at the first slot with troops <= 0."""
    owner = raw.army_hdr(i)[2]
    if owner != cur: return None
    L = [('Army of ', NAMES[owner])]
    for lab, typ, tr, q, nm in raw.slots(i):
        if tr <= 0: break
        L.append((nm + '   ' + unit_name(typ), f_commas(tr) + '   ' + quality_word(q)))
    return L
def fleet_lines(raw, i, cur):
    """ShowFleetDetails F:41134-41231 (the lines of the fleet itself; an embarked army adds 'Army' + the army lines, shifted by 8)."""
    o = raw.s.fleet0 + i * sav.FLEET_LEN
    x, y, _, _, owner, cd, moves, sup, money, ships, cond, army, sea = struct.unpack_from('<13h', raw.b, o)
    own = owner == cur
    L = [('Fleet of ', NAMES[owner]), ('Moves ', f_plain(moves) if own else ''), ('Ships ', f_plain(ships)),
         ('Repair ', (f_plain(cond) + '%') if own else ''),
         ('Supply ', ('%s tons  (%s%%)' % (f_plain(sup), f_plain(cdiv(sup * 100, ships << 3)))) if own else ''),
         ('Money ', ('%s talents' % f_plain(money)) if own else ''),
         ('Capacity ', f_commas(ships * 500) + ' troops'), ('Sea', 'calm' if sea == 0 else 'rough')]
    return L, army

def fleet_full(raw, i, cur):
    L, army = fleet_lines(raw, i, cur)
    if army >= 0:
        x, y = struct.unpack_from('<2h', raw.b, raw.s.fleet0 + i * sav.FLEET_LEN)
        for a in range(raw.s.na):
            h = raw.army_hdr(a)
            if h[0] == x and h[1] == y and h[2] >= 0:
                L += [('', '  '), ('', 'Army')] + army_lines(raw, a, cur)[2:]
                break
    return L
def merc_list(raw, cx, cy):
    """ShowCityUnits F:41231-41276: mercenary rows at the clicked tile (troops >= 0), name table DAT_0049cc94 (20-byte entries)."""
    rows = []
    for k, (x, y, lab, typ, tr, q) in enumerate(raw.merc_rows()):
        if tr >= 0 and x == cx and y == cy:
            rows.append((cstr(0x49cc94 + lab * 0x14) + '    ' + unit_name(typ), f_commas_raw(tr) + quality_word(q)))
    return rows
def f_commas_raw(v):
    """FUN_00448e74: 3 leading blanks (sign in the 2nd) + digits with commas, padded to 13 chars; the caller appends the quality word right after."""
    t = ('-' if v < 0 else ' ') ; return ('  ' + t + '{:,}'.format(abs(v))).ljust(13)
