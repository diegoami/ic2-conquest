#!/usr/bin/env python3
"""Minimal WinHelp 3.x reader: internal directory, and internal file extraction. Read only."""
import struct, sys
def u16(d,p): return struct.unpack_from('<H',d,p)[0]
def i32(d,p): return struct.unpack_from('<i',d,p)[0]
def u32(d,p): return struct.unpack_from('<I',d,p)[0]

def internal(d, off):
    res, used = i32(d,off), i32(d,off+4)
    return d[off+9: off+9+used]

def btree_entries(data, fmt_leaf):
    """Parse a WinHelp B+tree held in `data` (FILEHEADER already stripped). fmt_leaf(page, p) -> (entry, newp)"""
    magic, flags, psize = u16(data,0), u16(data,2), u16(data,4)
    assert magic == 0x293b, hex(magic)
    root, total, nlev = u16(data,26), u16(data,30), u16(data,32)
    nentries = u32(data,34)
    pages = data[38:]
    def page(n): return pages[n*psize:(n+1)*psize]
    # descend to first leaf
    n = root
    for _ in range(nlev-1):
        pg = page(n); n = u16(pg,4+0) if False else u16(pg,4)  # PreviousPage of index page = leftmost child
    out = []
    while n != 0xffff:
        pg = page(n); ne = u16(pg,2); nxt = u16(pg,6); p = 8
        for _ in range(ne):
            e, p = fmt_leaf(pg, p); out.append(e)
        n = nxt
    assert len(out) == nentries, (len(out), nentries)
    return out

def dir_entry(pg, p):
    e = pg.index(b'\0', p); name = pg[p:e].decode('latin-1'); return (name, u32(pg, e+1)), e+5

def directory(d):
    ds = i32(d,4)
    return dict(btree_entries(internal(d, ds), dir_entry))

if __name__ == '__main__':
    d = open(sys.argv[1],'rb').read()
    for k,v in sorted(directory(d).items(), key=lambda kv: kv[1]): print(hex(v), k)
