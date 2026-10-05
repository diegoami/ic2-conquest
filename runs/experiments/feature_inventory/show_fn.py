#!/usr/bin/env python3
"""Print functions from the whole-application dump by Delphi symbol or address. Read only. Usage: show_fn.py NAME_OR_ADDR..."""
import sys, re
DUMP = '/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt'
txt = open(DUMP, encoding='latin-1').read()
for a in sys.argv[1:]:
    pat = r'// ==== (\S*%s\S*) @ ([0-9a-f]+) ====\n(.*?)(?=\n// ==== |\Z)' % re.escape(a.lower().replace('0x', '').zfill(8) if re.match(r'(0x)?[0-9a-fA-F]{6,8}$', a) else a)
    for m in re.finditer(pat, txt, re.S):
        print('// ====', m.group(1), '@', m.group(2)); print(m.group(3)[:9000]); print()
