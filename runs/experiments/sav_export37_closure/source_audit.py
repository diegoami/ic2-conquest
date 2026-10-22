"""Bounded lexical alias leads, not a whole-program no-alias proof."""
import argparse, hashlib, json, re
from pathlib import Path
p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True); a = p.parse_args()
source = Path('/home/diego/ic2-work/decompile/all_app_functions.txt')
raw = source.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
assert digest == '2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8'
lines = raw.decode().splitlines()
starts = [(i, m.group(1), m.group(2)) for i, s in enumerate(lines) if (m := re.search(r'// ==== (.+?) @ ([0-9a-fA-F]+) ====', s))]
unknown = set(range(0x450, 0x46b)) | {0x46d, 0x491, 0x492, 0x493}
functions = []; absolute = []; relative = []
for k, (start, name, address) in enumerate(starts):
    end = starts[k+1][0] if k+1 < len(starts) else len(lines)
    hits = []; strides = []; offsets = []
    for i in range(start, end):
        line = lines[i]
        for m in re.finditer(r'(?:\b[A-Za-z_]*?)([0-9a-fA-F]{8})\b|\b0x([0-9a-fA-F]{6,8})\b', line):
            value = int(m.group(1) or m.group(2), 16)
            if 0x474670 <= value < 0x474670 + 16*1172:  # all sixteen 1172-byte records
                nation, offset = divmod(value-0x474670, 1172)
                hit = dict(line=i+1, text=line, address=hex(value), nation=nation, offset=hex(offset), starts_in_unknown=offset in unknown)
                hits.append(hit); absolute.append(dict(function=name, **hit))
        if re.search(r'\b0x(?:494|24a|125)\b', line): strides.append(i+1)
        if any(int(v, 16) in unknown for v in re.findall(r'\b0x([0-9a-fA-F]+)\b', line)):
            offsets.append(dict(line=i+1, text=line))
    if hits or strides:
        functions.append(dict(name=name, address=address, first_line=start+1, last_line=end, absolute_references=hits, stride_lines=strides, relative_unknown_constant_leads=offsets))
        relative.extend(dict(function=name, **r) for r in offsets)
prior = json.loads((Path(__file__).resolve().parents[3]/'runs/experiments/data/run-exp-sav-export37/source-inventory-addresses-v2.json').read_text())
old = {f['name'] for f in prior['functions']}
record = dict(source=str(source), source_sha256=digest, scope='Lexical start addresses across all 16 nation records, any symbol spelling or literal; stride and relative-constant leads. Access widths, derived pointers, casts, dynamic offsets and transitive callees are NOT resolved. Zero hits is not unused/padding proof.', functions=functions, absolute_references=absolute, unknown_start_references=[r for r in absolute if r['starts_in_unknown']], relative_unknown_constant_leads=relative, added_functions=[f['name'] for f in functions if f['name'] not in old])
with a.output.open('x') as f: json.dump(record, f, indent=2); f.write('\n')
print(json.dumps(dict(functions=len(functions), references=len(absolute), unknown_starts=len(record['unknown_start_references']), relative_leads=len(relative), added_functions=record['added_functions'])))
