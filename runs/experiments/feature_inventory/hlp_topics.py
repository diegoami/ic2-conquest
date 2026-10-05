#!/usr/bin/env python3
"""Decode the WinHelp topics (Win95-style PhrIndex/PhrImage phrase compression, LZ77 topic blocks).
Writes a TSV of topics (index, record type, text). Read only on the .hlp."""
import struct, sys, json
from hlp_dir import *

def lz77(src, limit=1<<30):
    out = bytearray(); p = 0
    while p < len(src):
        mask = src[p]; p += 1
        for _ in range(8):
            if p >= len(src): break
            if mask & 1:
                if p+1 >= len(src): p = len(src); break
                w = src[p] | (src[p+1] << 8); p += 2
                ln = ((w >> 12) & 0xF) + 3; pos = (w & 0xFFF) + 1
                for _ in range(ln):
                    out.append(out[-pos] if len(out) >= pos else 0)
            else:
                out.append(src[p]); p += 1
            mask >>= 1
    return bytes(out)

def phrases(d, dr):
    idx = internal(d, dr['|PhrIndex']); img = internal(d, dr['|PhrImage'])
    magic, n, csize, isize, icsize, z = struct.unpack_from('<6I', idx, 0)
    bits = u16(idx, 24)
    nb = bits & 15
    stream = idx[28:]
    pos = [0]; bp = 0
    def getbit():
        nonlocal bp
        v = (stream[bp >> 3] >> (bp & 7)) & 1; bp += 1; return v
    cur = 0
    for i in range(n):
        v = 1
        while getbit(): v += 1 << nb
        for k in range(nb): v += getbit() << k
        cur += v; pos.append(cur)
    # PhrImage: compressed if icsize < isize
    image = lz77(img) if icsize != isize else img
    meta = dict(magic=magic, n=n, csize=csize, isize=isize, icsize=icsize, nb=nb, bits=bits, image_len=len(image), last=pos[-1])
    return [image[pos[i]:pos[i+1]] for i in range(n)], meta

def topic_stream(d, dr):
    sysd = internal(d, dr['|SYSTEM'])
    minor, flags = u16(sysd, 2), u16(sysd, 10)
    t = internal(d, dr['|TOPIC'])
    bs = 0x1000 if not (flags == 8) else 0x800
    if minor <= 16: bs = 0x800
    out = bytearray()
    for b in range(0, len(t), bs):
        blk = t[b+12:b+bs]
        dec = lz77(blk) if minor > 16 and flags in (4, 8) else blk
        out += dec
    return bytes(out), dict(minor=minor, flags=flags, bs=bs)

def expand(b2, ph):
    """Empirical phrase decoder (the Win95 PhrIndex scheme as recovered here, not from a spec).
    Rules, each checked against the records' declared decompressed length (DataLen2):
      byte 07            : a space; the byte after it is then read as below
      byte c in 1,5,9 followed by b : bank code, phrase 128+256*((c-1)//4)+b
      07 x, x odd and not 1/5/9     : a space only (x is dropped)
      07 x or a lone byte x >= 0x80 : phrase x>>1, plus a trailing space if x is odd
      other bytes 1..15, 0x13, 0x17, 0x1b, 0x1f : controls, dropped (2 -> line break)
    Output is a readable approximation, not byte-exact; see help_decode_check.txt."""
    out = bytearray(); i = 0; n = len(b2)
    def P(x):
        k = x >> 1
        return (ph[k] if k < len(ph) else b'<?%d>' % k) + (b' ' if x & 1 else b'')
    while i < n:
        c = b2[i]
        if c == 7 and i+1 < n:
            x = b2[i+1]
            if x in (1, 5, 9) and i+2 < n:
                out += b' '; i += 1; continue
            if x & 1:
                out += b' '; i += 2; continue
            if x >= 0x10 or x == 0:
                out += b' ' + P(x); i += 2; continue
            out += b' ' + P(x); i += 2; continue
        if c in (1, 5, 9) and i+1 < n:
            k = 128 + 256*((c-1)//4) + b2[i+1]
            out += ph[k] if k < len(ph) else b'<?%d>' % k; i += 2; continue
        if c == 2: out += b'\n'; i += 1; continue
        if c <= 15 or c in (0x13, 0x17, 0x1b, 0x1f): i += 1; continue
        if c >= 0x80: out += P(c); i += 1; continue
        out.append(c); i += 1
    return bytes(out)

def topics(d):
    dr = directory(d); ph, pm = phrases(d, dr); st, sm = topic_stream(d, dr)
    recs = []; p = 0
    while p + 21 <= len(st):
        bsz, dl2, prv, nxt, dl1 = struct.unpack_from('<5i', st, p); rt = st[p+20]
        if st[p] == 0:
            p += 1; continue   # zero padding at the end of a topic block
        if bsz < 21 or bsz > 0x10000 or dl1 < 21 or dl1 > bsz:
            print('PARSE STOP at', hex(p), 'of', hex(len(st)), file=sys.stderr); break
        l1 = st[p+21:p+dl1]; l2 = st[p+dl1:p+bsz]
        raw_len = len(l2)
        if dl2 > len(l2): l2 = expand(l2, ph)
        recs.append((p, rt, l1, l2, dl2, raw_len)); p += bsz
    return recs, pm, sm

if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    recs, pm, sm = topics(d)
    print(pm, sm, len(recs), file=sys.stderr)
    for p, rt, l1, l2, dl2, rl in recs:
        print('%06x\t%02x\t%s' % (p, rt, l2.decode('latin-1').replace('\0', '|').replace('\n', '\\n')[:300]))
