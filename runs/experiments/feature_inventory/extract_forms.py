#!/usr/bin/env python3
"""Extract every TPF0 form resource from the original exe into a JSON tree and a flat TSV.
Read-only on the exe. Usage: extract_forms.py <exe> <outdir>"""
import sys, re, struct, json, os

def rd(d, p):
    return d[p], p + 1

class P:
    def __init__(s, d, p): s.d, s.p = d, p
    def u8(s): v = s.d[s.p]; s.p += 1; return v
    def pstr(s):
        n = s.u8(); v = s.d[s.p:s.p+n].decode('latin-1'); s.p += n; return v
    def i(s, n, fmt):
        v = struct.unpack_from(fmt, s.d, s.p)[0]; s.p += n; return v

def value(r):
    t = r.u8()
    if t == 0: return None
    if t == 1:
        out = []
        while r.d[r.p] != 0: out.append(value(r))
        r.p += 1; return out
    if t == 2: return r.i(1, '<b')
    if t == 3: return r.i(2, '<h')
    if t == 4: return r.i(4, '<i')
    if t == 5: r.p += 10; return '<extended>'
    if t == 6: return r.pstr()
    if t == 7: return {'ident': r.pstr()}
    if t == 8: return False
    if t == 9: return True
    if t == 10:
        n = r.i(4, '<I'); v = r.d[r.p:r.p+n]; r.p += n; return {'binary': n}
    if t == 11:
        out = []
        while True:
            s = r.pstr()
            if not s: break
            out.append(s)
        return {'set': out}
    if t == 12: r.p += 4; return '<single>'
    if t == 13: r.p += 8; return '<currency>'
    if t == 14: r.p += 8; return '<date>'
    if t == 15:
        n = r.i(4, '<I'); v = r.d[r.p:r.p+2*n].decode('utf-16le'); r.p += 2*n; return v
    if t == 16: return r.i(8, '<q')
    if t == 17:
        n = r.i(4, '<I'); v = r.d[r.p:r.p+n].decode('utf-8', 'replace'); r.p += n; return v
    raise ValueError('value type %d at %x' % (t, r.p))

def obj(r):
    if r.d[r.p] & 0xF0 == 0xF0:
        fl = r.u8()
        if fl & 2: r.i(2, '<h') if False else None
    cls = r.pstr(); name = r.pstr()
    o = {'class': cls, 'name': name, 'props': {}, 'children': []}
    while r.d[r.p] != 0:
        k = r.pstr(); o['props'][k] = value(r)
    r.p += 1
    while r.d[r.p] != 0:
        o['children'].append(obj(r))
    r.p += 1
    return o

def main(exe, out):
    d = open(exe, 'rb').read()
    forms = []
    for m in re.finditer(rb'TPF0', d):
        s = m.start()
        # a form resource: TPF0 followed by pstring class starting with 'T'
        n = d[s+4]
        if n == 0 or d[s+5:s+6] != b'T': continue
        try:
            r = P(d, s+4); o = obj(r)
        except Exception as e:
            print('FAIL', hex(s), e, file=sys.stderr); continue
        o['offset'] = hex(s); o['end'] = hex(r.p)
        forms.append(o)
    json.dump(forms, open(os.path.join(out, 'forms.json'), 'w'), indent=1)
    rows = []
    def walk(o, form, path, depth):
        cap = o['props'].get('Caption')
        hint = o['props'].get('Hint')
        ev = {k: v['ident'] for k, v in o['props'].items() if isinstance(v, dict) and 'ident' in v and k.startswith('On')}
        sc = o['props'].get('ShortCut')
        scs = ''
        if isinstance(sc, int) and sc:
            scs = ('Ctrl+' if sc & 0x4000 else '') + ('Shift+' if sc & 0x2000 else '') + ('Alt+' if sc & 0x8000 else '') + chr(sc & 0xff)
        rows.append((form, path, o['class'], o['name'], cap if isinstance(cap, str) else '', hint if isinstance(hint, str) else '',
                     ';'.join('%s=%s' % kv for kv in ev.items()), scs, o['props'].get('Checked', '')))
        for c in o['children']: walk(c, form, path + '/' + c['name'], depth+1)
    for f in forms: walk(f, f['class'], f['name'], 0)
    with open(os.path.join(out, 'form_controls.tsv'), 'w') as fh:
        fh.write('form\tpath\tclass\tname\tcaption\thint\tevents\tshortcut\tchecked\n')
        for r_ in rows: fh.write('\t'.join(str(x) for x in r_) + '\n')
    print(len(forms), 'forms,', len(rows), 'controls')
if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
