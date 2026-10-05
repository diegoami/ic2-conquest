"""L1 save editor for the Information-window runs: edit a COPY of a fixture save field by field (never a player save).
Offsets are state/sav.py's (docs/sav-layout-notes.md). Every setter writes a little-endian signed 16-bit field unless said."""
import struct
from state import sav

class Save:
    def __init__(self, path):
        self.b = bytearray(open(path, 'rb').read())
        self._offsets()
    def _offsets(self):
        b = self.b
        self.na = struct.unpack_from('<h', b, sav.ARMY_OFF)[0]
        self.army0 = sav.ARMY_OFF + 2
        o = self.army0 + self.na * sav.ARMY_LEN
        self.nf = struct.unpack_from('<h', b, o)[0]
        self.fleet0 = o + 2
        self.nation0 = self.fleet0 + self.nf * sav.FLEET_LEN
        self.merc0 = self.nation0 + 16 * sav.NATION_LEN
    # ---- cities: 34 bytes; +14 x, +16 y, +18 owner, +20 allegiance, +22 loyalty, +24 supply, +26 fort, +28 pop, +30 max_pop, +32 tribute
    def city(self, i, **kw):
        names = dict(x=14, y=16, owner=18, allegiance=20, loyalty=22, supplies=24, fort=26, pop=28, max_pop=30, tribute=32)
        for k, v in kw.items(): self.put(sav.CITY_OFF + i * sav.CITY_LEN + names[k], v, 'H' if (k == 'tribute' and v >= 0x8000) else 'h')
    # ---- armies: 656 bytes; +0 x, +2 y, +4 owner, +6 moves, +8 cell, +10 supply, +12 money, +14 morale; unit k at +16+32k: label, type, troops, quality, name[24]
    def army(self, i, **kw):
        names = dict(x=0, y=2, owner=4, moves=6, cell=8, supplies=10, money=12, morale=14)
        for k, v in kw.items(): self.put(self.army0 + i * sav.ARMY_LEN + names[k], v)
    def unit(self, i, k, label=None, type=None, troops=None, quality=None, name=None):
        o = self.army0 + i * sav.ARMY_LEN + 16 + 32 * k
        for off, v in ((0, label), (2, type), (4, troops), (6, quality)):
            if v is not None: self.put(o + off, v)
        if name is not None: self.b[o + 8:o + 32] = name.encode('latin1')[:23].ljust(24, b'\0')
    # ---- fleets: 26 bytes; x, y, ?, ?, owner(+8), countdown(+10), moves(+12), supplies(+14), money(+16), ships(+18), condition(+20), army(+22), +24 (sea word field)
    def fleet(self, i, **kw):
        names = dict(x=0, y=2, owner=8, countdown=10, moves=12, supplies=14, money=16, ships=18, condition=20, army=22, sea=24)
        for k, v in kw.items(): self.put(self.fleet0 + i * sav.FLEET_LEN + names[k], v)
    # ---- nations: 1172 bytes; +0x26 relations[16], +0x2e4 recruit slots 40 x (state, type, troops, city), +0x430 wealth(i32) +0x438 treasury(i32), +0x440 unity, +0x442 mobilization, +0x444 capital, +0x446 cities, +0x44a tax, +0x44e conquered_by
    def nation(self, n, **kw):
        names = dict(unity=0x440, mobilization=0x442, capital=0x444, ncities=0x446, tax=0x44a, conquered_by=0x44e)
        for k, v in kw.items():
            if k == 'treasury': struct.pack_into('<i', self.b, self.nation0 + n * sav.NATION_LEN + 0x438, v)
            elif k == 'wealth': struct.pack_into('<i', self.b, self.nation0 + n * sav.NATION_LEN + 0x430, v)
            else: self.put(self.nation0 + n * sav.NATION_LEN + names[k], v)
    def relation(self, n, m, v): self.put(self.nation0 + n * sav.NATION_LEN + 0x26 + 2 * m, v)
    def slot(self, n, k, state, type, troops, city):
        o = self.nation0 + n * sav.NATION_LEN + 0x2E4 + 8 * k
        for j, v in enumerate((state, type, troops, city)): self.put(o + 2 * j, v)
    def put(self, o, v, fmt='h'): struct.pack_into('<' + fmt, self.b, o, v)
    def write(self, path):
        open(path, 'xb').write(bytes(self.b))
